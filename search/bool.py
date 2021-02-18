from preprocessor import preprocess_text


def get_index_set(word: str, indexdic: dict) -> set:
    """
    This is to get a set of docid(s) having this word.

    Parameters
    ----------
    word: str
    indexdic: dict

    Returns
    -------
    set(index): set
    """
    term = preprocess_text(word)[0]
    if term in indexdic.keys():
        index = list(indexdic[term].keys())
    else:
        index = []
    return set(index)


def boolean_search(query: str, indexdic: dict, doc_numbers: int) -> list:
    """
    This is the process of Boolean.
    Parameters
    ----------
    query: str
    indexdic: dict
    doc_numbers: int

    Returns
    -------
    sorted(result_set): list
        Doc_id list of the result from Boolean search.
    """
    word_list = []
    for word in query.split(' '):
        word_list.append(word)

    # word_list includes operator (AND, OR, NOT)
    word_list_length = len(word_list)

    op = ''  # record current operator
    pos = 0  # the position of current word
    opnot = False  # whether the operator is NOT
    exist_all_docid = False  # all_docid is used for boolean search (op: NOT)
    result_set = set()
    first_word = True  # if it's the first word, the operation will be a little different
    while pos < word_list_length:
        current_word = word_list[pos]
        if current_word == 'AND':
            op = 'AND'
        elif current_word == 'OR':
            op = 'OR'
        elif current_word == 'NOT':
            opnot = True
        else:
            if opnot:
                if not exist_all_docid:
                    all_docid = set([str(i) for i in range(doc_numbers)])
                    exist_all_docid = True

                temp_set = all_docid.difference(
                    get_index_set(current_word, indexdic))
                opnot = False
            else:
                temp_set = get_index_set(current_word, indexdic)
            if first_word:
                result_set = temp_set
                first_word = False
            if op == 'AND':
                result_set = set.intersection(result_set, temp_set)
                op = ''
            if op == 'OR':
                result_set = set.union(result_set, temp_set)
                op = ''
        pos += 1
    return sorted(result_set)


def run_boolean(indexdic: dict, docid_info: dict, doc_numbers: int):
    """
    This is to run Boolean search.

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
    query_boolean = input("Please input your query for boolean search: ")

    all_docid = boolean_search(query_boolean, indexdic, doc_numbers)

    for docid in all_docid:
        # docid_info[docid][0]: doi_url
        # docid_info[docid][1]: title
        # docid_info[docid][2]: abstract
        print('\nDoi_url: ' + docid_info[docid][0] + '\n' +
              'Title: ' + docid_info[docid][1] + '\n' +
              'Abstract: ' + docid_info[docid][2] + '\n----------------')
