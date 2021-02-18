from preprocessor import preprocess_text
import jsonlines
import json


def create_alphabetical_inverted_index(filepath: str) -> dict:
    """
    Creates the alphabetical_inverted_index and a dict storing related information of papers.

    Parameters
    ----------
    filepath: str
        Path to JSONL file which contains extracted information from papers.

    Returns
    -------
    words_index: dict
        Dictionary {'alphabet': {'preprocessed_token': {docid: [position]}}}
    docid_info: dict
        Dictionary {docid: ['doi_url', 'title', 'abstract']}
    """

    # All of the count (including the docid and term_position) starts from 0.

    # create the dictionary of words_index
    words_index = {}
    lower_letters = [chr(i) for i in range(97, 123)]  # The result is [a-z]
    for alphabet in lower_letters:
        words_index[alphabet] = {}
    # When the first letter of the term is not [a-z], it will be assigned into
    # this dictionary of words_index['num']
    words_index['num'] = {}
    # 'words_index' will be transformed into inverted index in the function 'write_index_to_disk()'.

    # create the dictionary of 'docid_info'
    docid_info = {}

    with open(filepath, "r+", encoding="utf8") as f:
        for docid, paper_dict in enumerate(
                jsonlines.Reader(f)):  # docid counts from 0
            content = preprocess_text(
                str(paper_dict['title']) + str(' ') + str(paper_dict['abstract']))

            # Start the process of docid_info
            '''
            docid_info[docid][0]: doi_url
            docid_info[docid][1]: title
            docid_info[docid][2]: abstract
            '''
            docid_info[docid] = []
            docid_info[docid].append(str(paper_dict['doi_url']))
            docid_info[docid].append(str(paper_dict['title']))
            # Control the abstract only display around 300 characters
            if len(paper_dict['abstract']) <= 300:
                docid_info[docid].append(str(paper_dict['abstract']))
            else:
                position = 300
                while paper_dict['abstract'][position] != ' ':
                    # This is to show the complete word that has character on the position 300,
                    # to ensure it will not just display part of the word.
                    position += 1
                if position + 1 == len(paper_dict['abstract']):
                    docid_info[docid].append(paper_dict['abstract'])
                else:
                    docid_info[docid].append(
                        paper_dict['abstract'][:position] + ' ...')
            # End the process of docid_info

            # Start the process for words_index (alphabetical inverted index)
            for term_pos, term in enumerate(content):
                if term[0] in lower_letters:
                    # If the term[0] is one of the alphabets a->z, the term will be classified into corresponding
                    # alphabet dictionary. For example, for term 'apple', it
                    # will be classified into dict words_index['a'].
                    if term not in words_index[term[0]].keys():
                        words_index[term[0]][term] = {}
                    if docid not in words_index[term[0]][term].keys(
                    ):
                        words_index[term[0]][term][docid] = [
                            term_pos]
                    else:
                        words_index[term[0]][term][docid].append(
                            term_pos)
                else:
                    # If the term[0] is not an alphabet. It will be classified
                    # into dict words_index['num'].
                    if term not in words_index['num'].keys():
                        words_index['num'][term] = {}
                    if docid not in words_index['num'][term].keys(
                    ):
                        words_index['num'][term][docid] = [
                            term_pos]
                    else:
                        words_index['num'][term][docid].append(
                            term_pos)
            # End the process for words_index
    return words_index, docid_info


def write_index_to_disk(words_index: dict):
    """
    Transform the dict 'words_index' to an inverted index, then save the inverted index as a json file.

    Parameters
    ----------
    words_index: dict
        alphabetical inverted index produced by the function 'create_alphabetical_inverted_index'.

    Returns
    -------

    """
    inverted_index = {}
    for single_part in words_index.values():
        inverted_index.update(single_part)
    with open('processed_data/index.json', 'w', encoding='utf-8') as f:
        json.dump(inverted_index, f)


def write_docinfo_into_disk(docid_info: dict):
    """
    Write the dictionary 'docid_info' into disk as a json file

    Parameters
    ----------
    docid_info: dict
        Dictionary which stores extracted information from papers. Dict {'doc_id':['doi_url', 'title', 'abstract']}

    Returns
    -------

    """
    with open('processed_data/docid_info.json', 'w', encoding='utf-8') as f:
        json.dump(docid_info, f)


def write_numbers_of_docs_into_disk(docid_info: dict):
    """
    This is done to have a count of the dataset and write the number into a txt file.

    Parameters
    ----------
    docid_info: dict
        Dictionary which stores extracted information from papers. Dict {'doc_id':['doi_url', 'title', 'abstract']}
    Returns
    -------

    """
    doc_numbers = len(docid_info.keys())
    with open('processed_data/num_of_docs.txt', 'w', encoding='utf-8') as f:
        f.write(str(doc_numbers))


def load_index_from_disk() -> dict:
    """
    Loaded json file docid is str rather than int {'award': {'0': [17], '4': [25], '10': [369]

    Returns
    -------
    indexdic: dict
        Dictionary of inverted index. {'term':{'doc_id':[term_position]}}
    """
    with open('processed_data/index.json', 'r', encoding='utf-8') as f:
        indexdic = json.load(f)
    return indexdic


def load_docinfo_from_disk() -> dict:
    """
    Load dict 'docid_info' from disk

    Returns
    -------
    docid_info: dict
        Dictionary {'doc_id': ['doi_url','title','abstract']}
    """
    with open('processed_data/docid_info.json', 'r', encoding='utf-8') as f:
        docid_info = json.load(f)
    return docid_info
