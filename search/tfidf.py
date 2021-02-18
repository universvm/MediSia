from preprocessor import preprocess_text
from bool import boolean_search
import math


def get_tf(term: str, docid: str, indexdic: dict) -> int:
    """
    This is to get the Term Frequency according to the pointed term and docid.
    Parameters
    ----------
    term: str
        The term we get from the query.
    docid: str
        The ID of the corresponding doc.
    indexdic: dict
        Inverted index.

    Returns
    -------
    tf: int
        Term frequency corresponding to the term and docID.
    """
    if term in indexdic.keys():
        if docid in indexdic[term].keys():
            tf = len(indexdic[term][docid])
        else:
            tf = 0
    else:
        tf = 0
    return tf


def get_df(term: str, indexdic: dict) -> int:
    """
    This is to get the document frequency corresponding to the term.
    Parameters
    ----------
    term: str
        The term preprocessed from the query.
    indexdic: dict
        Inverted index.

    Returns
    -------
    df: int
        Document frequency corresponding to the term.
    """
    if term in indexdic.keys():
        df = len(indexdic[term])
    else:
        df = 0
    return df


def term_weight(
        term: str,
        docid: str,
        indexdic: dict,
        doc_numbers: int) -> int:
    tf = get_tf(term, docid, indexdic)
    df = get_df(term, indexdic)
    if df != 0:
        idf = math.log10(doc_numbers / df)
        if tf > 0:
            w = (1 + math.log10(tf)) * idf
        else:
            w = 0
    else:
        w = 0
    return w


def get_tfidf_score(
        query: list,
        docid: str,
        indexdic: dict,
        doc_numbers: int) -> int:
    """
    This is to get the TFIDF score of the query corresponding to the pointed docid.
    Parameters
    ----------
    query: list
    docid: str
    indexdic: dict
    doc_numbers: int

    Returns
    -------
    score: int
        TFIDF score corresponding to the query and doc_ID.
    """
    score = 0
    for term in query:
        score += term_weight(term, docid, indexdic, doc_numbers)
    return score


def get_all_doc(query: list, indexdic: dict, doc_numbers: int) -> list:
    """
    This is to get the sorted list of doc_id(s) corresponding to the query in TFIDF.
    Parameters
    ----------
    query: list
    indexdic: dict
    doc_numbers: int

    Returns
    -------
    all_doc: list
        The list of doc_ID(s) corresponding to the query in TFIDF.
    """
    or_query = ' OR '.join(query)
    all_doc = boolean_search(or_query, indexdic, doc_numbers)
    return all_doc


def run_tfidf(indexdic: dict, docid_info: dict, doc_numbers: int):
    """
    This is to run the TFIDF search.

    Parameters
    ----------
    indexdic: dict
        Dictionary of inverted index
    docid_info: dict
        Dictionary {'doc_id': ['doi_url', 'title', 'abstract']}
    doc_numbers: int
        number of docs

    Returns
    -------

    """
    query = input("Please type your query: ")
    query = preprocess_text(query)
    # get the docid(s) of document(s) having at least one word in query
    all_doc = get_all_doc(query, indexdic, doc_numbers)

    scoredic = {}
    for docid in all_doc:
        score = get_tfidf_score(query, docid, indexdic, doc_numbers)
        scoredic[docid] = score

    sorted_score = sorted(scoredic.items(), key=lambda x: (-x[1], x[0]))

    for docid, tfidf_score in sorted_score:
        # docid_info[docid][0]: doi_url
        # docid_info[docid][1]: title
        # docid_info[docid][2]: abstract
        print('\nDoi_url: ' + docid_info[docid][0] + '\n' +
              'Title: ' + docid_info[docid][1] + '\n' +
              'Rank value: ' + str(round(tfidf_score, 4)) + '\n' +
              'Abstract: ' + docid_info[docid][2] + '\n----------------')
