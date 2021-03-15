import linecache
import time
import datetime
import warnings
import typing as t
import multiprocessing as mp
from operator import itemgetter
from pathlib import Path
import copy

import joblib
import json
from gensim.corpora.mmcorpus import MmCorpus
from sklearn.preprocessing import LabelEncoder
from gensim.matutils import sparse2full
from gensim.test.utils import get_tmpfile
from gensim.similarities.docsim import Similarity, SparseMatrixSimilarity

from config import (
    INDECES_FOLDER,
    QUERY_CLASSIFIER,
    BOW_LENGTH,
    MEDICINE_SHARDS,
    ALL_SHARDS,
)
from index.tfidf_vectorizer import convert_str_to_tfidf
from index.unpaywall_process import build_journal_category_dict

# Turning off gensim printouts:
import logging

logging.getLogger("gensim").setLevel(logging.WARNING)


class SearchModule:
    def __init__(
        self,
        indeces_folder: Path = INDECES_FOLDER,
        classifier_path: Path = QUERY_CLASSIFIER,
        num_features: int = BOW_LENGTH,
        medicine_shards: int = MEDICINE_SHARDS,
        all_shards: int = ALL_SHARDS,
        top_k: int = 3,
        query_cat: int = 3,
        sparse_search: bool = True,
        return_unique_jsonl: bool = False,
    ):
        self.indeces_folder = indeces_folder
        self.classifier_path = classifier_path
        self.top_k = top_k
        self.sparse_search = sparse_search
        self.num_features = num_features
        self.query_cat = query_cat
        self.medicine_shards = medicine_shards
        self.all_shards = all_shards
        self.return_unique_jsonl = return_unique_jsonl

        self.cat_to_cache_dict = self._load_jsonl_indeces()
        self.query_classifier = self._load_query_classifier()

        _, categories_list = build_journal_category_dict()
        self.categories = sorted(categories_list)

        self.classifier_categories = copy.copy(self.categories)
        self.classifier_categories.remove("nutrition")
        self.label_encoder = LabelEncoder()
        # Fit categories to label encoder
        self.label_encoder.fit(self.categories)

    def _load_jsonl_indeces(self):
        # Initialize dictionary:
        cat_to_cache_dict = dict()
        # Get all indeces file:
        category_outpaths_list = list(self.indeces_folder.rglob("index_*"))
        for cat_file in category_outpaths_list:
            # Extract Category:
            category = str(cat_file.stem).split("index_")[-1]
            # Create dictionary
            cat_to_cache_dict[category] = cat_file

        return cat_to_cache_dict

    def _load_query_classifier(self):
        return joblib.load(self.classifier_path)

    def search(
        self, query, category: t.Union[str, None] = None, deep_search: bool = False
    ):
        processed_category = category
        if deep_search:
            if isinstance(category, str):
                warnings.warn(
                    "Deep Search was True but category was given. Will be performing Deep Search."
                )
            elif category is None:
                processed_category = "all"
            else:
                assert isinstance(
                    category, str
                ), f"Category must be a str or None but got {type(category)}"

        tfidf_query, bow_len = convert_str_to_tfidf(query)
        if (
            (processed_category)
            and (processed_category != "medicine")
            and (processed_category != "all")
        ):
            curr_results = self.search_category((tfidf_query, processed_category))
            # Extract results from tuple
            sorted_score, sorted_results = curr_results
        # Do classification + multiprocessing
        else:
            if processed_category is None:
                # Classify query
                query_category = self.classify_query(tfidf_query)
            # category is all or medicine:
            else:
                # Make categories like medicine and all into shards for multiprocessing
                query_category = self.replace_cat_with_shards(
                    tfidf_query, processed_category
                )

            # Create empty lists for results
            pool_score = []
            pool_results = []
            # Initiate multiprocessing:
            pool = mp.Pool()
            for curr_results in pool.imap(self.search_category, query_category):
                # Extract results from tuple
                score_results, docs_results = curr_results
                # Merge results together:
                pool_score += score_results
                pool_results += docs_results

            sorted_score, sorted_results = zip(*sorted(zip(pool_score, pool_results), key=lambda x: x[0]))

        response = [json.loads(res) for res in sorted_results]
        json_response = json.dumps(response)

        return sorted_score, json_response

    def search_category(self, tfidf_query_category):
        tfidf_query, category = tfidf_query_category
        # Load corpora for specific category
        category_corpus_path = self.indeces_folder / f"{category}_corpus.mm"
        corpus = MmCorpus(str(category_corpus_path))
        if self.sparse_search:
            sparse_sim = SparseMatrixSimilarity(
                corpus, num_features=self.num_features, num_best=self.top_k
            )
            similarity_results = sparse_sim.get_similarities(tfidf_query)
        else:
            index_tmpfile = get_tmpfile("index")
            index = Similarity(
                index_tmpfile,
                corpus,
                num_features=self.num_features,
                num_best=self.top_k,
            )
            # Cosine search:
            similarity_results = index[tfidf_query]
        # Create range of docids
        doc_ids = range(len(similarity_results))
        # Sort by most relevant:
        sorted_similarity_results, sorted_docid_results = zip(
            *sorted(zip(similarity_results, doc_ids), key=lambda x: x[0])[:self.top_k])

        metadata = linecache.getlines(str(self.cat_to_cache_dict[category]))

        return (sorted_similarity_results, list(itemgetter(*sorted_docid_results)(metadata)))

    def classify_query(self, tfidf_query):
        full_tfidf_query = sparse2full(tfidf_query, length=self.num_features)
        query_scores = self.query_classifier.predict_proba(
            full_tfidf_query.reshape(1, -1)
        )
        sorted_query = sorted(
            zip(self.classifier_categories, query_scores[0]),
            key=lambda x: x[1],
            reverse=True,
        )
        # Convert topn cat into numbers:
        query_category = []
        for cat, score in sorted_query[: self.query_cat]:
            # make sure that large categories are sharded:
            query_category += self.replace_cat_with_shards(tfidf_query, cat)

        return query_category

    def replace_cat_with_shards(self, tfidf_query, category):
        if category == "medicine":
            query_category = [
                (tfidf_query, f"medicine{i}")
                for i in range(1, self.medicine_shards + 1)
            ]
        elif category == "all":
            query_category = [
                (tfidf_query, f"all{i}") for i in range(1, self.all_shards + 1)
            ]
        else:
            query_category = [(tfidf_query, category)]

        return query_category


class FollowUpSearch:
    def __init__(self, json_response):
        self.json_response = json.loads(json_response)
        # Create indeces from json response:
        self.docid_index, self.date_index, self.journal_index = self._create_indeces()

    def _create_indeces(self):
        docid_index = {}
        date_index = {}
        journal_index = {}

        for i, json_obj in enumerate(self.json_response):
            # Create general index:
            docid_index[i] = json_obj
            # Create date index:
            year = json_obj["year"]
            if year not in date_index.keys():
                date_index[year] = []
            date_index[year].append(i)
            # Create journal index:
            journal = json_obj["journal_name"]
            if journal not in journal_index.keys():
                journal_index[journal] = []
            journal_index[journal].append(i)

        return docid_index, date_index, journal_index

    def search_date(self, start, end):
        start = int(start)
        if end is None:
            x = datetime.datetime.now()
            end = x.year
        end = int(end)
        range_date = list(range(start, end))
        response = []
        for date in range_date:
            if date in self.date_index.keys():
                curr_docids = self.date_index[date]
                for docid in curr_docids:
                    response.append(self.docid_index[int(docid)])

        json_response = json.dumps(response)
        return json_response

    def search_journal(self, journal):
        response = []
        if journal in self.journal_index.keys():
            curr_docids = self.journal_index[journal]
            for docid in curr_docids:
                response.append(self.docid_index[int(docid)])

        json_response = json.dumps(response)
        return json_response


if __name__ == "__main__":
    search_module = SearchModule()
    sorted_score, json_response = search_module.search("Hypoglycemia")
    print(json_response)
    followup_search = FollowUpSearch(json_response)
    p = followup_search.search_date(2000, None)
    print(p)
    followup_search = FollowUpSearch(p)
    p = followup_search.search_journal("Japanese Journal of Food Microbiology")
    print(p)

