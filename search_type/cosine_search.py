import bz2
from gensim.corpora.mmcorpus import MmCorpus
from gensim.test.utils import get_tmpfile
from gensim.similarities.docsim import Similarity
from config import INDECES_FOLDER
import pickle
from index.tfidf_vectorizer import convert_str_to_tfidf
from pathlib import Path


def search_query_in_category(query: str, category: str, indeces_folder: Path = INDECES_FOLDER):
    tfidf_query, bow_len = convert_str_to_tfidf(query)
    # Create temporary file for similarity index
    index_tmpfile = get_tmpfile("index")
    # Load corpora for specific category
    category_corpus_path = indeces_folder / f"{category}_corpus.mm"
    corpus = MmCorpus(str(category_corpus_path))
    # TODO: This could be saved to file and reloaded:
    index = Similarity(index_tmpfile, corpus, num_features=bow_len)
    # Cosine search
    similarity_results = index[tfidf_query]
    # Sort by most relevant:
    sorted_docid_results = sorted(range(len(similarity_results)), key=lambda k: similarity_results[k], reverse=True)
    # TODO: Indeces could be loaded in memory while search is going:
    # Import metadata
    metadata_dict_path = indeces_folder / f"{category}_metadata.bz2"
    with bz2.BZ2File(metadata_dict_path, "rb") as f:
        metadata_dict = pickle.load(f)

    print(metadata_dict[str(sorted_docid_results[0])])
    print(metadata_dict[str(sorted_docid_results[1])])
    print(metadata_dict[str(sorted_docid_results[2])])



if __name__ == '__main__':
    search_query_in_category("nucleotide chromatin associated rna synthesis", "biochemistry")