from preprocessor import preprocess
import json
import math

'''
This file contains functions including:
	1. loading json file from disk
	2. process of TFIDF and BOOLEAN
	3. running TFIDF and BOOLEAN search

'''

def load_index_from_disk(): 
#When we load the json file from disk, the docid is str instead of int. {'award': {'0': [17], '4': [25], '10': [369]
    with open('processed_data/index.json','r',encoding='utf-8') as f:
        indexdic = json.load(f)
    return indexdic


def load_docinfo_from_disk():
    with open('processed_data/docid_info.json','r',encoding='utf-8') as f:
        docid_info = json.load(f)
    return docid_info


# output: a set of docid(s) having this word
def getIndexSet(word,indexdic):
    try:
        term = preprocess(word)[0]
        index = list(indexdic[term].keys())
    except:
        index = []
    return set(index)


def booleanSearch(query,indexdic, N):
    wordList = []
    for word in query.split(' '):
        wordList.append(word)
    
    length = len(wordList) #wordList includes operator (AND, OR, NOT)

    op = '' # record current operator
    pos = 0 # the position of current word
    opnot = False # whether the operator is NOT
    existAll_docid = False # All_docid is used for boolean search (op: NOT) 
    resultSet = set()
    tempSet = set()
    FirstWord = True # if it's the first word, the operation will be a little different
    while pos<length:
        currentWord = wordList[pos]
        if currentWord == 'AND':
            op = 'AND'
        elif currentWord == 'OR':
            op = 'OR'
        elif currentWord == 'NOT':
            opnot = True
        else:
            if opnot:
                if existAll_docid == False:
                    All_docid = set([str(i) for i in range(N)])
                    existAll_docid = True
                    
                tempSet = All_docid.difference(getIndexSet(currentWord,indexdic))
                opnot = False
            else:
                tempSet = getIndexSet(currentWord,indexdic)
            if FirstWord:
                resultSet = tempSet
                FirstWord = False
            if op == 'AND':
                resultSet = set.intersection(resultSet, tempSet)
                op = ''
            if op == 'OR':
                resultSet = set.union(resultSet, tempSet)
                op = ''
        pos += 1
    return sorted(resultSet)


def getTF(term, docid, indexdic):
    try: # term may not exist in document(docid)
        tf = len(indexdic[term][docid])
    except:
        tf = 0
    return tf


def getDF(term,indexdic):
    try:
        df = len(indexdic[term])
    except:
        df = 0
    return df


def termWeight(term, docid, indexdic, N):
    tf = getTF(term, docid, indexdic)
    df = getDF(term, indexdic)
    if df!=0:
        idf = math.log10(N/df)
    if tf>0:
        w = (1+math.log10(tf))*idf
    else:
        w = 0
    return w


def TfidfScore(query, docid, indexdic, N):
    score = 0
    for term in query:
        score += termWeight(term, docid,indexdic, N)
    return score


def getAllDoc(query,indexdic,N):
    ORquery = ' OR '.join(query)
    allDoc = booleanSearch(ORquery,indexdic, N)
    return allDoc


def runTfidf(indexdic, docid_info, N):
    # This part is to run the TFIDF search
    query = input("Please type your query: ")
    query = preprocess(query)
    allDoc = getAllDoc(query,indexdic, N) # get the docid(s) of document(s) having at least one word in query

    scoredic = {}
    for docid in allDoc:
        score = TfidfScore(query, docid, indexdic, N)
        scoredic[docid] = score

    sorted_score = sorted(scoredic.items(), key = lambda x: (-x[1], x[0]))


    for docid, tfidf_score in sorted_score:
        '''
        docid_info[docid][0]: doi_url
        docid_info[docid][1]: title
        docid_info[docid][2]: abstract
        '''
        print('\nDoi_url: ' + docid_info[docid][0] + '\n' + \
          'Title: ' + docid_info[docid][1] + '\n' +\
          'Rank value: ' + str(round(tfidf_score,4)) + '\n' + \
          'Abstract: ' + docid_info[docid][2] + '\n----------------')


def runBoolean(indexdic, docid_info, N):
    # The following part is to run boolean search

    query_boolean = input("Please input your query for boolean search: ")

    '''
    I think for boolean search, it's better to provide options of operators for users instead of typing all by themselfs.
    For example, four options for user to choose: AND, OR, NOT AND, NOT OR. After option is a box for user to type term.
    The frontend will combine them automatically and push to the backend.
    The following code is designed in this way, so I assume the variable 'query_boolean' doesn't contain any punctuation.
    '''

    allDocid = booleanSearch(query_boolean, indexdic, N)

    for docid in allDocid:
        '''
        docid_info[docid][0]: doi_url
        docid_info[docid][1]: title
        docid_info[docid][2]: abstract
        '''
        print('\nDoi_url: ' + docid_info[docid][0] + '\n' + \
          'Title: ' + docid_info[docid][1] + '\n' +\
          'Abstract: ' + docid_info[docid][2] + '\n----------------')


