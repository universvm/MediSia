import linecache
from time import time
from operator import itemgetter
from pathlib import Path

from gensim.corpora.mmcorpus import MmCorpus
from gensim.test.utils import get_tmpfile
from gensim.similarities.docsim import Similarity

from config import INDECES_FOLDER
from index.tfidf_vectorizer import convert_str_to_tfidf


def search_query_in_category(query: str, category: str, indeces_folder: Path = INDECES_FOLDER, top_k: int = 300):
    """
    Searches query in a specific category of index.

    Parameters
    ----------
    query: str
        Query to search
    category: str
        Category to search in
    indeces_folder: Path
        Path to all indeces

    """
    tfidf_query, bow_len = convert_str_to_tfidf(query)
    # Create temporary file for similarity index
    index_tmpfile = get_tmpfile("index")
    # Load corpora for specific category
    category_corpus_path = indeces_folder / f"{category}_corpus.mm"
    corpus = MmCorpus(str(category_corpus_path))
    index = Similarity(index_tmpfile, corpus, num_features=bow_len)
    # Cosine search:
    similarity_results = index[tfidf_query]
    # Sort by most relevant:
    sorted_docid_results = sorted(range(len(similarity_results)), key=lambda k: similarity_results[k], reverse=True)[:top_k]
    # Import metadata
    # TODO: This can be preindexed:
    metadata_dict_path = indeces_folder / f"{category}_metadata.jsonl"
    metadata = linecache.getlines(str(metadata_dict_path))
    print(itemgetter(*sorted_docid_results)(metadata))


if __name__ == '__main__':
    start = time()
    search_query_in_category("coronavirus", "virology")
    end = time()
    print(end-start)
