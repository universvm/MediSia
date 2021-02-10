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
    preprocessed_corpus = preprocess_string(input_corpus)
    return utils.tokenize(preprocessed_corpus, deacc=True, lower=True)


class BiopapersCorpus:
    def __init__(self, dictionary: Dictionary, path_to_JSONL_index: Path):
        self.dictionary = dictionary
        self.index_path = path_to_JSONL_index

    def __iter__(self):
        for json_line in jsonlines.open(self.index_path):
            # Add abstract and title together:
            title_abstract_str = json_line["title"] + " " + json_line["abstract"]
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
            # Add abstract and title together:
            title_abstract_str = json_line["title"] + " " + json_line["abstract"]
            tokens_list = clean_and_tokenize_text(title_abstract_str)
            # tokens_list = simple_preprocess(title_abstract_str, deacc=True)
            # tokens_list = title_abstract_str.lower().split(" ")
            # Create a dictionary
            # yield Dictionary([tokens_list])
            yield Dictionary(tokens_list)


def create_bow_from_biopapers(
    no_below: int = 2,
    no_above: float = 0.5,
    path_to_jsonl_index: Path = BIOPAPERS_JSON_PATH,
    outfile: Path = BOW_PATH,
) -> Dictionary:

    # Initialize variables:
    biopapers_iter = BiopapersBOW(path_to_jsonl_index, create_bow_mode=True)
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
        # Filter words before reiterating:
        curr_dictionary.filter_extremes(no_below=no_below, no_above=no_above)
    # TODO Try by just returning document
    # Save collection to file
    curr_dictionary.save(outfile)

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
    tfidf_model.save(outfile)

    return tfidf_model


def vectorize_index_tfidf(
    doc_corpus: t.List, index_name: str, out_folder: Path, max_n_words
):
    # Creates a hash that allows for vectorization
    # This is really efficient as new words can be added immediately
    # read more: https://radimrehurek.com/gensim/corpora/hashdictionary.html
    dictionary = HashDictionary(id_range=DEFAULT_DICT_SIZE)
    dictionary.allow_update = True  # start collecting document frequencies

    return


if __name__ == "__main__":

    prova = BiopapersBOW()
    curr_dictionary = dict()
    for i, p in enumerate(prova):
        print(i)
        if i == 0:
            curr_dictionary = p
            curr_dictionary.filter_extremes(no_below=2, no_above=0.5)
            print(curr_dictionary)
        else:
            curr_dictionary.merge_with(p)
        if i == 5:
            print(curr_dictionary)
            break
    # twenty = fetch_20newsgroups()
    # docs = [clean_text(str(doc)) for doc in twenty.values()]
