import linecache
import time
import warnings
import typing as t
import multiprocessing as mp
from operator import itemgetter
from pathlib import Path
import copy

import joblib
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
        top_k: int = 50,
        query_cat: int = 5,
        sparse_search: bool = True,
    ):
        self.indeces_folder = indeces_folder
        self.classifier_path = classifier_path
        self.top_k = top_k
        self.sparse_search = sparse_search
        self.num_features = num_features
        self.query_cat = query_cat
        self.medicine_shards = medicine_shards
        self.all_shards = all_shards

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
            pool_results = self.search_category((tfidf_query, processed_category))
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
            pool_results = []
            pool = mp.Pool()
            for curr_results in pool.imap(self.search_category, query_category):
                pool_results.append(curr_results)

        return pool_results

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
        # Sort by most relevant:
        sorted_docid_results = sorted(
            range(len(similarity_results)),
            key=lambda k: similarity_results[k],
            reverse=True,
        )[: self.top_k]
        metadata = linecache.getlines(str(self.cat_to_cache_dict[category]))

        return zip(sorted_docid_results, itemgetter(*sorted_docid_results)(metadata))

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


if __name__ == "__main__":
    search_module = SearchModule()
    start = time.time()
    results = search_module.search("coronavirus")
    end = time.time()
    print(end - start)
