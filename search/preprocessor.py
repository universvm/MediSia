import collections
import re
from stemming.porter2 import stem

def tokenization(content):
	#delete "'" from the punctuation set, because in the stop words file, some stop words invlove '.
		word_tokens = re.sub(r'[!@#$%^&*()_+{}|:"<>?,./;\'[\]\-=]+', ' ', content).lower().split()
		return word_tokens

def stop_words(word_tokens):
	with open('stop_words/englishST.txt', 'r') as f:
		content = f.read()
	stop_word_tokens = tokenization(content)
	filter_stop = [w for w in word_tokens if w not in stop_word_tokens]
	return filter_stop

def porter_stemmer(filter_stop):
	filter_stemmer = [stem(tokens) for tokens in filter_stop]
	return filter_stemmer

def preprocess(content):
	word_tokens = tokenization(content)
	filter_stop = stop_words(word_tokens)
	filter_stemmer = porter_stemmer(filter_stop)
	return filter_stemmer


#The following is another version of preprocessor. The biggest difference is the following version would tokenize much more terms.

"""
import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.stem.porter import *
import re
from os import path

def tokenizer(text):
    tokenizer = RegexpTokenizer(r'\w+')
    newtext = tokenizer.tokenize(text.lower())
    return newtext

def deleteStopWords(text):
    with open('englishST.txt') as f:
        stopWords = f.read().split(' ')
    newtext = []
    for word in text:
        if word not in stopWords:
            newtext.append(word)
    return newtext

def stemmer(text):
    stemmer = PorterStemmer()
    newtext = [stemmer.stem(word) for word in text]
    return newtext

def preprocess(text):
    text = tokenizer(text)
    text = deleteStopWords(text)
    text = stemmer(text)
    return text
"""