import re
from stemming.porter2 import stem


def tokenization(content):
    word_tokens = re.sub(
        r'[!@#$%^&*()_+{}|:"<>?,./;\'[\]\-=]+',
        ' ',
        content).lower().split()
    return word_tokens


def text_cleaning(word_tokens):
    # This function includes processes of removing stop words and stemmer
    with open('stop_words/englishST.txt', 'r') as f:
        all_stop_words = f.read()
    stop_word_tokens = tokenization(all_stop_words)
    cleaned_result = []
    for token in word_tokens:
        if token in stop_word_tokens:
            continue
        else:
            cleaned_result.append(stem(token))
    return cleaned_result


def preprocess_text(content):
    word_tokens = tokenization(content)
    preprocessed_result = text_cleaning(word_tokens)
    return preprocessed_result
