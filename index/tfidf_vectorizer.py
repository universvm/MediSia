import bz2
import os
import jsonlines
import pickle
import typing as t
from pathlib import Path

from gensim import utils
from gensim.corpora import Dictionary
from gensim.corpora.mmcorpus import MmCorpus
from gensim.models import TfidfModel
from gensim.parsing.preprocessing import PorterStemmer
from tqdm import tqdm

from config import (
    BIOPAPERS_JSON_PATH,
    BOW_PATH,
    TFIDF_VECTORIZER,
    INDECES_FOLDER,
    DEFAULT_STOPWORDS,
    BIOPAPERS_WOUT_ABSTRACT_JSON_PATH,
    BIOPAPERS_W_ABSTRACT_JSON_PATH,
    BOW_LENGTH,
)
from config import (
    spaces,
    num_alpha,
    alpha_num,
    non_letters,
    numbers,
    html_tags,
    punctuation,
)

p = PorterStemmer()


def clean_and_tokenize_text(input_corpus: str, min_len: int = 3) -> t.List[str]:
    """
    Inspiration from gensim preprocess_text with the addition of medical stop words

    Parameters
    ----------
    input_corpus: str
        Input string to be tokenized

    Returns
    -------
    s_tokens: list
        List of stemmed tokens
    """
    s = input_corpus.lower()
    s = utils.to_unicode(s)
    # Remove HTML Tags
    s = html_tags.sub("", s)
    # Remove punctuation:
    s = punctuation.sub("", s)
    # Remove non-letters:
    s = non_letters.sub(" ", s)
    # Remove digits in letters:
    s = alpha_num.sub(" ", s)
    s = num_alpha.sub(" ", s)
    # Remove white space:
    s = spaces.sub(" ", s)
    # Remove numbers:
    s = numbers.sub("", s)
    # Remove stopwords and small words:
    s_tokens = []
    for curr_word in s.split(" "):
        if curr_word not in DEFAULT_STOPWORDS:
            if len(curr_word) >= min_len:
                s_tokens.append(p.stem(curr_word))

    return s_tokens


class BiopapersCorpus:
    def __init__(
        self,
        bow_dictionary: Dictionary,
        path_to_JSONL_index: Path,
        tfidf_vectorizer: t.Union[TfidfModel, None] = None,
        metadata_index_outpath: t.Union[Path, None] = None,
    ):
        self.bow_dictionary = bow_dictionary
        self.index_path = path_to_JSONL_index
        self.tfidf_vectorizer = tfidf_vectorizer
        self.metadata_index_outpath = metadata_index_outpath
        # Initialize id count to 0
        self.count_doc_id = 0

    def __iter__(self):
        for json_line in tqdm(
            jsonlines.open(self.index_path), f"Iterating through corpora {self.index_path}"
        ):
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
            # If Vectorization mode on:
            if self.tfidf_vectorizer:
                # If file for indexing was given:
                if self.metadata_index_outpath:
                    # Extract relevant info:
                    doi = json_line["doi"]
                    title = json_line["title"]
                    url = json_line["doi_url"]
                    journal = json_line["journal_name"]
                    authors_dict = json_line["z_authors"]
                    year = json_line["year"]
                    # Add metadata to dictionary
                    metadata_dict = {
                        self.count_doc_id: {
                            "doi": doi,
                            "title": title,
                            "url": url,
                            "journal": journal,
                            "authors": authors_dict,
                            "year": year,
                        }
                    }
                    # Create key in gz pickle file:
                    with jsonlines.open(self.metadata_index_outpath, "a") as outfile:
                        outfile.write(metadata_dict)
                    # Increasing count:
                    self.count_doc_id += 1
                # Convert BOW corpus to TFIDF:
                yield self.tfidf_vectorizer[self.bow_dictionary.doc2bow(tokens_list)]
            # Else we are converting to BOW:
            else:
                yield self.bow_dictionary.doc2bow(tokens_list)


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
    keep_n: int = BOW_LENGTH,
    prune_at_idx: int = 10000,
) -> Dictionary:
    """
    Create bag of words dictionary from jsonl biopapers

    Parameters
    ----------
    no_below: int
        Minimum number of appearances of a word
    no_above: float
        Max frequency of a word
    path_to_jsonl_index: Path
        Path to jsonlines papers
    outfile: Path
        Path to bow file
    prune_at_idx: int
        Index multiple at which to prune the dictionary. Eg. if prune_at_idx the
        index will be pruned at 1000, 2000, 3000 and so on.

    Returns
    -------
    collection_dictionary: Dictionary
        Gensim Bow dictionary
    """
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
        if i % prune_at_idx == 0:
            # Filter words:
            collection_dictionary.filter_extremes(no_below=no_below, no_above=no_above, keep_n=keep_n)
    # Final Filter words:
    collection_dictionary.filter_extremes(no_below=no_below, no_above=no_above, keep_n=keep_n)
    # Save collection to file:
    collection_dictionary.save(str(outfile))

    return collection_dictionary


def create_tfidf_from_papers(
    path_to_jsonl_index: Path = BIOPAPERS_JSON_PATH,
    path_to_bow: Path = BOW_PATH,
    outfile: Path = TFIDF_VECTORIZER,
) -> TfidfModel:
    """
    Creates TFIDF model from BOW corpora.

    Parameters
    ----------
    path_to_jsonl_index: Path
        Path to json lines index
    path_to_bow: Path
        Path to Bag of Words Dictionary
    outfile: Path
        Path to TFIDF vectorizer

    Returns
    -------
    tfidf_model: TfidfModel
        Gensim TFIDF Model
    """
    # Load dictionary
    dictionary = Dictionary.load(str(path_to_bow))
    # Load corpus generator
    corpus = BiopapersCorpus(dictionary, path_to_jsonl_index)
    # Train TFIDF
    tfidf_model = TfidfModel(corpus)
    # Save TFIDF model to file:
    tfidf_model.save(str(outfile))

    return tfidf_model


def convert_corpus_to_sparse_tfidf(
    metadata_index_outpath: Path,
    vectorized_corpus_outpath: Path,
    path_to_jsonl_index: Path = BIOPAPERS_JSON_PATH,
    path_to_bow: Path = BOW_PATH,
    tfidf_vectorizer: Path = TFIDF_VECTORIZER,
):
    """
    Convert corpora of a specific category into a tfidf sparse matrix.

    It saves:
        1. MM Corpus sparse matrix indexed by id
        2. metadata index as gz pickle file.

    Parameters
    ----------
    metadata_index_outpath: Path
        Path to metadata index (without extension)
    vectorized_corpus_outpath: Path
        Path to corpus matrix, does not require extension
    path_to_jsonl_index: Path
        Path to jsonl_index for that specific category
    path_to_bow: Path
        Path to BOW dictionary
    tfidf_vectorizer:
        Path to TFIDF model for vectorization of BOW corpus
    """
    # Load dictionary
    if path_to_bow.exists():
        bow_dictionary = Dictionary.load(str(path_to_bow))
    else:
        bow_dictionary = create_bow_from_biopapers()
    # Load tfidf model:
    if tfidf_vectorizer.exists():
        tfidf_model = TfidfModel.load(str(tfidf_vectorizer))
    else:
        tfidf_model = create_tfidf_from_papers()
    # Add pickle suffix:
    metadata_index_outpath = metadata_index_outpath.with_suffix(".jsonl")
    # Load corpus generator:
    tfidf_corpus = BiopapersCorpus(
        bow_dictionary=bow_dictionary,
        path_to_JSONL_index=path_to_jsonl_index,
        tfidf_vectorizer=tfidf_model,
        metadata_index_outpath=metadata_index_outpath,
    )
    # Save corpus and index to file:
    MmCorpus.serialize(str(vectorized_corpus_outpath), tfidf_corpus)
    # Convert Jsonlines to pickle bz2
    # convert_jsonl_to_pickle_bz(metadata_index_outpath)


def convert_jsonl_to_pickle_bz(jsonl_path: Path, delete_jsonl: bool = True):
    """
    Converts jsonl metadata to pickle bz and optionally removes the original file.

    Parameters
    ----------
    jsonl_path: Path
        Path to Jsonlines metadata
    delete_jsonl: Bool
        Whether to delete the jsonlines file after the conversion. Default = True
    """
    pkl_bz_outfile = jsonl_path.with_suffix(".bz2")
    metadata_dict = {}
    # Open jsonlines and update dictionary:
    with jsonlines.open(jsonl_path) as reader:
        for i, metadata_obj in enumerate(tqdm(reader, desc=f"Building metadata {pkl_bz_outfile}"),):
            if i == 0:
                metadata_dict = dict(metadata_obj)
            else:
                metadata_dict = {**metadata_dict, **dict(metadata_obj)}
    # TODO this stalls for large files above 4GB
    # Write pickle to compressed BZ2:
    with bz2.BZ2File(pkl_bz_outfile, "wb") as writer:
        pickle.dump(metadata_dict, writer, pickle.HIGHEST_PROTOCOL)

    # Remove Jsonlines file
    if delete_jsonl:
        try:
            os.remove(jsonl_path)
        except:
            print("Failed to delete Jsonlines file.")


def convert_indeces_to_tfidf(indeces_folder: Path = INDECES_FOLDER):
    # Obtain list of all indeces:
    index_list = list(indeces_folder.rglob("index_*"))
    # For index path
    for index_path in index_list:
        category = str(index_path.stem).split("index_")[-1]
        metadata_outpath = indeces_folder / f"{category}_metadata"
        corpus_outpath = indeces_folder / f"{category}_corpus.mm"

        convert_corpus_to_sparse_tfidf(
            metadata_index_outpath=metadata_outpath,
            vectorized_corpus_outpath=corpus_outpath,
            path_to_jsonl_index=index_path,
        )

def convert_str_to_tfidf(
    input_str: str,
    path_to_bow: Path = BOW_PATH,
    tfidf_vectorizer: Path = TFIDF_VECTORIZER,
) -> (list, int):
    """
    Converts a string to bow and then to tfidf

    Parameters
    ----------
    input_str: str
        String to be converted. eg. from query
    path_to_bow: Path
        Path to BOW dictionary
    tfidf_vectorizer:
        Path to TFIDF model for vectorization of BOW corpus

    Returns
    -------
    tfidf_query: list
        List of vectorized tokens and relative tfidf value.
    bow_len: int
        Integer representing the length of the bow dictionary.

    """
    # Load dictionary
    if path_to_bow.exists():
        bow_dictionary = Dictionary.load(str(path_to_bow))
    else:
        bow_dictionary = create_bow_from_biopapers()
    # Load tfidf model:
    if tfidf_vectorizer.exists():
        tfidf_model = TfidfModel.load(str(tfidf_vectorizer))
    else:
        tfidf_model = create_tfidf_from_papers()
    # Tokenize query:
    query_tokens = clean_and_tokenize_text(input_str)
    # Convert query to bow:
    query_bow = bow_dictionary.doc2bow(query_tokens)
    # Convert bow query to Tfidf:
    tfidf_query = tfidf_model[query_bow]

    return tfidf_query, len(bow_dictionary)


if __name__ == "__main__":
    convert_indeces_to_tfidf()
