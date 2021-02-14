import gzip
import jsonlines
import pickle
import typing as t
from pathlib import Path

from gensim.corpora import Dictionary
from gensim.corpora.mmcorpus import MmCorpus
from gensim.models import TfidfModel
from gensim.parsing.preprocessing import preprocess_string
from tqdm import tqdm

from config import BIOPAPERS_JSON_PATH, BOW_PATH, TFIDF_VECTORIZER


def clean_and_tokenize_text(input_corpus: str) -> t.List[str]:
    return preprocess_string(input_corpus)


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
        for json_line in tqdm(jsonlines.open(self.index_path), "Iterating through corpora"):
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
                    metadata_dict = {self.count_doc_id : {
                        "doi": doi,
                        "title": title,
                        "url": url,
                        "journal": journal,
                        "authors": authors_dict,
                        "year": year,
                    }}
                    # Create key in gz pickle file:
                    with gzip.open(self.metadata_index_outpath, 'wb') as outfile:
                        pickle.dump(metadata_dict, outfile)
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
    bow_dictionary = Dictionary.load(str(path_to_bow))
    # Load tfidf model:
    tfidf_model = TfidfModel.load(str(tfidf_vectorizer))
    # Add pickle suffix
    metadata_index_outpath = metadata_index_outpath.with_suffix('.pkl.gz')
    # Load corpus generator:
    tfidf_corpus = BiopapersCorpus(
        bow_dictionary=bow_dictionary,
        path_to_JSONL_index=path_to_jsonl_index,
        tfidf_vectorizer=tfidf_model,
        metadata_index_outpath=metadata_index_outpath,
    )
    # Save corpus and index to file:
    MmCorpus.serialize(str(vectorized_corpus_outpath), tfidf_corpus)


if __name__ == "__main__":
    _ = create_bow_from_biopapers()
    _ = create_tfidf_from_papers()
    convert_corpus_to_sparse_tfidf(Path('botany_metadata'), Path("botany_corpus.mm"))