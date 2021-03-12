import linecache
import warnings
import typing as t
import multiprocessing as mp
from operator import itemgetter
from pathlib import Path

import joblib
from gensim.corpora.mmcorpus import MmCorpus
from sklearn.preprocessing import LabelEncoder
from gensim.matutils import sparse2full
from gensim.similarities.docsim import Similarity, SparseMatrixSimilarity


from config import INDECES_FOLDER, QUERY_CLASSIFIER, BOW_LENGTH
from index.tfidf_vectorizer import convert_str_to_tfidf
from index.unpaywall_process import build_journal_category_dict


class SearchModule:
    def __init__(
        self,
        indeces_folder: Path = INDECES_FOLDER,
        classifier_path: Path = QUERY_CLASSIFIER,
        num_features: int = BOW_LENGTH,
        top_k: int = 300,
        sparse_search: bool = True,
    ):
        self.indeces_folder = indeces_folder
        self.classifier_path = classifier_path
        self.top_k = top_k
        self.sparse_search = sparse_search
        self.num_features = num_features

        self.cat_to_cache_dict = self._load_jsonl_indeces()
        self.query_classifier = self._load_query_classifier()

        _, categories_list = build_journal_category_dict()
        self.categories = sorted(categories_list)
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
        if processed_category:
            pool_results = self.search_category(tfidf_query, processed_category)
        # Do classification + multiprocessing
        else:
            # Classifyc query
            query_category = self.classify_query(sparse2full(tfidf_query, length=self.num_features))
            pool_results = []
            pool = mp.Pool()
            for curr_results in pool.starmap(self.search_category, query_category):
                pool_results.append(curr_results)

        return pool_results

    def search_category(self, tfidf_query, category):
        # Load corpora for specific category
        category_corpus_path = self.indeces_folder / f"{category}_corpus.mm"
        corpus = MmCorpus(str(category_corpus_path))
        sparse_sim = SparseMatrixSimilarity(
            corpus, num_features=self.num_features, num_best=self.top_k
        )
        similarity_results = sparse_sim.get_similarities(tfidf_query)
        # Sort by most relevant:
        sorted_docid_results = sorted(
            range(len(similarity_results)),
            key=lambda k: similarity_results[k],
            reverse=True,
        )[:self.top_k]
        metadata = linecache.getlines(str(self.cat_to_cache_dict[category]))

        return zip(sorted_docid_results, itemgetter(*sorted_docid_results)(metadata))

    def classify_query(self, tfidf_query, top_cat: int = 5):
        query_scores = self.query_classifier.predict_proba(tfidf_query.reshape(1, -1))
        sorted_query = sorted((self.categories, query_scores), key=lambda x: x[1])
        # Convert topn cat into numbers:
        query_category = []
        for cat, score in sorted_query[:top_cat]:
            # Convert categories to txt:
            cat_txt = self.label_encoder.inverse_transform(cat)
            query_category.append(zip(tfidf_query, cat_txt))

        return query_category


if __name__ == "__main__":
    search_module = SearchModule()
    results = search_module.search("coronavirus")
