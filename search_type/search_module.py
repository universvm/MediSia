import linecache
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
        top_k: int = 20,
        query_cat: int = 3,
        sparse_search: bool = True,
    ):
        """
        Initialize search module.

        Parameters
        ----------
        indeces_folder: Path
            Path to indeces
        classifier_path: Path
            Path to classifier
        num_features: int
            Number of words in BOW
        medicine_shards: int
            Number of shards which split the medicine category
        all_shards: int
            Number of shards which split the all category
        top_k: int
            Number of results to be returned per category
        query_cat: int
            Number of categories to consider
        sparse_search: bool
            Whether to do sparse search (True) or not (False). Sparse search is faster.

        """
        self.indeces_folder = indeces_folder
        self.classifier_path = classifier_path
        self.top_k = top_k
        self.sparse_search = sparse_search
        self.num_features = num_features
        self.query_cat = query_cat
        self.medicine_shards = medicine_shards
        self.all_shards = all_shards

        # Load jsonlines category indeces:
        self.cat_to_cache_dict = self._load_jsonl_indeces()
        # Load query classifier:
        self.query_classifier = self._load_query_classifier()
        # Load category names:
        _, categories_list = build_journal_category_dict()

        self.categories = sorted(categories_list)
        # Removing nutrition from classifier (immunology only contains less than 1k articles):
        self.classifier_categories = copy.copy(self.categories)
        self.classifier_categories.remove("immunology")
        # Load label encoder:
        self.label_encoder = LabelEncoder()
        # Fit categories to label encoder
        self.label_encoder.fit(self.categories)

    def _load_jsonl_indeces(self) -> dict:
        """
        Loads the jsonl indeces to dict.

        Returns
        -------
        cat_to_cache_dict: dict
            Dictionary {category: path_to_category_index}
        """
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
    ) -> (t.List[float], json.JSONEncoder):
        """
        Performs a basic search function through a corpus.

        Parameters
        ----------
        query: str
            Query to be searched
        category: t.Union[str, None]
            Category (str) or None if query should be classified for magic search
        deep_search:
            Whether to do a deep search through the whole index/

        Returns
        -------
        sorted_score: t.List[float]
            List of similarity scores for each of the documents
        json_response: json.JSONEncoder
            JSON response containing documents sorted by similarity

        """
        processed_category = category
        # If search through all indeces:
        if deep_search:
            if isinstance(category, list):
                warnings.warn(
                    "Deep Search was True but category was given. Will be performing Deep Search."
                )
            elif category is None:
                processed_category = ["all"]
            else:
                assert isinstance(
                    category, list
                ), f"Category must be a list or None but got {type(category)}"
        # Convert str to tfidf query:
        tfidf_query, bow_len = convert_str_to_tfidf(query)

        # Do classification to search + multiprocessing through category indeces

        if processed_category is None:
            # Classify query
            query_category = self.classify_query(tfidf_query)
        # category is all or medicine:
        else:
            # Merge categories and queries for multiprocessing
            # Also, make categories like medicine and all into shards
            query_category = []
            for cat in processed_category:
                query_category += self.replace_cat_with_shards(tfidf_query, cat)

        # Create empty lists for results
        pool_score = []
        pool_results = []
        # Initiate multiprocessing:
        pool = mp.Pool()
        for curr_results in pool.imap(self.search_category, query_category):
            # Extract results from tuple:
            score_results, docs_results = curr_results
            # Merge results together:
            pool_score += score_results
            pool_results += docs_results
        # Sort results by similarity score:
        sorted_score, sorted_results = zip(
            *sorted(zip(pool_score, pool_results), key=lambda x: x[0], reverse=True)
        )
        # Create and return a json response:
        response = [json.loads(res) for res in sorted_results]
        json_response = json.dumps(response)

        return sorted_score, json_response

    def search_category(
        self, tfidf_query_category: tuple
    ) -> (t.List[float], t.List[str]):
        """
        Searches through a category

        Parameters
        ----------
        tfidf_query_category: tuple
            tfidf_query and category tuple

        Returns
        -------
        sorted_similarity_results: t.List[float]
            List of float sorted by largest similarity to smallest
        sorted_corpora: t.List[str]
            List of str of JSONL documents

        """
        # Unpack input data:
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
            *sorted(zip(similarity_results, doc_ids), key=lambda x: x[0], reverse=True)[
                : self.top_k
            ]
        )
        # Load category index:
        metadata = linecache.getlines(str(self.cat_to_cache_dict[category]))

        return (
            sorted_similarity_results,
            list(itemgetter(*sorted_docid_results)(metadata)),
        )

    def classify_query(self, tfidf_query) -> t.List[tuple]:
        """
        Uses a classifier to classify a query into 1 of 26 categories. Used for magic search.

        Parameters
        ----------
        tfidf_query: list
            Tfidf query

        Returns
        -------
        query_category: t.List[tuple]
            List of [(tfidf_query, category), (tfidf_query, category)]

        """
        # Unsparse query for classifier:
        full_tfidf_query = sparse2full(tfidf_query, length=self.num_features)
        # Classify query:
        query_scores = self.query_classifier.predict_proba(
            full_tfidf_query.reshape(1, -1)
        )
        # Sort query by most probable:
        sorted_query = sorted(
            zip(self.classifier_categories, query_scores[0]),
            key=lambda x: x[1],
            reverse=True,
        )
        # Convert topn categories into numbers:
        query_category = []
        for cat, score in sorted_query[: self.query_cat]:
            # make sure that large categories are sharded:
            query_category += self.replace_cat_with_shards(tfidf_query, cat)

        return query_category

    def replace_cat_with_shards(self, tfidf_query, category) -> t.List[tuple]:
        """
        Splits categories of all and medicine into shards for faster processing.

        Parameters
        ----------
        tfidf_query: list
            Tfidf query
        category: str
            Category str

        Returns
        -------
        query_category: t.List[tuple]
            List [(tfidf_query, category)]
        """
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
        """
        Initializes Follow Up Search

        Parameters
        ----------
        json_response: json.JSONEncoder
            Json response
        """
        self.json_response = json.loads(json_response)
        # Create indeces from json response:
        self.docid_index, self.date_index, self.journal_index = self._create_indeces()

    def _create_indeces(self) -> (dict, dict, dict):
        """
        Creates indeces of docid, date and journal. Because the json response
        is ranked by most relevant, the index is also ordered by most relevant
        hence why it is not necessary to do the sorting again.

        Returns
        -------
        docid_index: dict
            {docid: json_doc}
        date_index: dict
            {date: docid}
        journal_index: dict
            {journal: docid}
        """
        # Initialize empty indeces:
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

    def search_date(self, start: int, end: t.Union[int, None]) -> json.JSONEncoder:
        """
        Searches json for range of date

        Parameters
        ----------
        start: int
            Start date
        end: int or None
            End date. If None, today's year is used

        Returns
        -------
        json_response: json.JSONEncoder
            Json response

        """
        # Load start and end date:
        start = int(start)
        if end is None:
            x = datetime.datetime.now()
            end = x.year
        end = int(end)
        # Create a range of dates:
        range_date = list(range(start, end + 1))
        # Initilize Response
        response = []
        for date in range_date:
            # If date is in index:
            if date in self.date_index.keys():
                # Load DocIDs:
                curr_docids = self.date_index[date]
                # Save JSON of DocIDs:
                for docid in curr_docids:
                    response.append(self.docid_index[int(docid)])
        # Save to JSON response
        json_response = json.dumps(response)

        return json_response

    def search_journal(self, journals: t.List[str]) -> json.JSONEncoder:
        """
        Searches through journals. The journal input must be precise, an error will be returned if a journal does not exist.

        Parameters
        ----------
        journal: t.List[str]
            List of names of journals

        Returns
        -------
        json_response: json.JSONEncoder
            Json response

        """
        response = []
        docs_in_response_set = set()
        for journal in journals:
            # If journal is in index:
            if journal in self.journal_index.keys():
                # Load DocIDs:
                curr_docids = self.journal_index[journal]
                # Save JSON of DocIDs:
                for docid in curr_docids:
                    # if document is already in the response, ignore it
                    if int(docid) in docs_in_response_set:
                        continue
                    else:
                        # add document to response
                        docs_in_response_set.add(int(docid))
                        response.append(self.docid_index[int(docid)])
        # Save to JSON response
        json_response = json.dumps(response)

        return json_response

    def return_indeces(self):
        return list(self.date_index.keys()), list(self.journal_index.keys())


if __name__ == "__main__":
    # 1. Magic Search
    search_module = SearchModule()
    sorted_score, json_response = search_module.search("coronavirus")
    # 2. Category Search
    print(json_response)
    sorted_score, json_response = search_module.search("coronavirus", category=["biochemistry", "bioengineering"])
    print(json_response)
    followup_search = FollowUpSearch(json_response)
    # Return list of dates and journals for the front end:
    date_list, journals_list = followup_search.return_indeces()
    # 3. Follow up search
    p = followup_search.search_journal(["Journal of Industrial Microbiology & Biotechnology"])
    print(p)
    followup_search = FollowUpSearch(p)
    p = followup_search.search_date(2000, None)
    print(p)
