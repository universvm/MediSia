import os
import typing as t
import pickle
from jsonlines import Reader
from pathlib import Path
from tqdm import tqdm

from gensim.corpora.dictionary import Dictionary
from gensim.utils import simple_preprocess

from gensim.corpora import Dictionary, HashDictionary, MmCorpus, WikiCorpus
from gensim.models import TfidfModel
from scipy.sparse.csr import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.datasets import fetch_20newsgroups

from config import DEFAULT_DICT_SIZE, BIOPAPERS_JSON_PATH, BOW_PATH, TFIDF_VECTORIZER
from gensim.corpora.textcorpus import TextCorpus
from gensim.models import TfidfModel


import jsonlines
from gensim import utils
from gensim.test.utils import datapath
from gensim.parsing.preprocessing import preprocess_string


def clean_and_tokenize_text(input_corpus: str) -> t.List[str]:
    return preprocess_string(input_corpus)


class BiopapersCorpus:
    def __init__(self, dictionary: Dictionary, path_to_JSONL_index: Path):
        self.dictionary = dictionary
        self.index_path = path_to_JSONL_index

    def __iter__(self):
        for json_line in jsonlines.open(self.index_path):
            # Initialize empty abstract and title:
            abstract = ""
            title = ""
            # Check if title and abstracts are available:
            if json_line["title"]:
                title = json_line["title"]
            if json_line["abstract"]:
                abstract = json_line["abstract"]
            # Add abstract and title together
            title_abstract_str = title + " " + abstract
            tokens_list = clean_and_tokenize_text(title_abstract_str)
            yield self.dictionary.doc2bow(tokens_list)


class BiopapersBOW:
    """
    Intelligent implementation of corpora which opens one document at the time
    """

    def __init__(self, path_to_JSONL_index: Path):
        self.index_path = path_to_JSONL_index

    def __iter__(self):
        for json_line in jsonlines.open(self.index_path):
            # Initialize empty abstract and title:
            abstract = ""
            title = ""
            # Check if title and abstracts are available:
            if json_line["title"]:
                title = json_line["title"]
            if json_line["abstract"]:
                abstract = json_line["abstract"]
            # Add abstract and title together
            title_abstract_str = title + " " + abstract
            # Clean text:
            tokens_list = clean_and_tokenize_text(title_abstract_str)
            # Create a dictionary
            yield Dictionary([tokens_list])


def create_bow_from_biopapers(
    no_below: int = 2,
    no_above: float = 0.5,
    path_to_jsonl_index: Path = BIOPAPERS_JSON_PATH,
    outfile: Path = BOW_PATH,
) -> Dictionary:
    # Initialize variables:
    biopapers_iter = BiopapersBOW(path_to_jsonl_index)
    collection_dictionary = dict()
    # Iterate through collection and build vocabulary
    for i, paper_vocabulary in enumerate(
        tqdm(biopapers_iter, desc="Building bag of words")
    ):
        # If first paper:
        if i == 0:
            collection_dictionary = paper_vocabulary
        else:
            collection_dictionary.merge_with(paper_vocabulary)
    # Filter words:
    collection_dictionary.filter_extremes(no_below=no_below, no_above=no_above)
    # Save collection to file:
    collection_dictionary.save(str(outfile))

    return collection_dictionary


def create_tfidf_from_papers(
    path_to_jsonl_index: Path = BIOPAPERS_JSON_PATH,
    path_to_bow: Path = BOW_PATH,
    outfile: Path = TFIDF_VECTORIZER,
) -> TfidfModel:
    # Load dictionary
    dictionary = Dictionary.load(str(path_to_bow))
    # Load corpus generator
    corpus = BiopapersCorpus(dictionary, path_to_jsonl_index)
    # Train TFIDF
    tfidf_model = TfidfModel(corpus)
    # Save TFIDF model to file:
    tfidf_model.save(str(outfile))

    return tfidf_model


if __name__ == "__main__":
    _ = create_bow_from_biopapers()
    _ = create_tfidf_from_papers()
