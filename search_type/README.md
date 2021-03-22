# Search 

## Files Necessary

### 1. Indeces 

location: `data/indeces/`

```
{category_name}_corpus.mm
{category_name}_corpus.mm.index
{category_name}_metadata.jsonl *(deprecated - not in use)*
index_{category_name}.jsonl
```

eg. for agriculture:

```
agriculture_corpus.mm
agriculture_corpus.mm.index
agriculture_metadata.jsonl *(deprecated - not in use)*
index_agriculture.jsonl
```

#### Explanation

These files contain the indeces divided by topics.

| File extension  | Description  |
|---|---|
| .mm  | Market Matrix (sparse) containing TFIDF corpus |
|  .mm.index | Necessary file for .mm corpus  |
|  .jsonl |  Index JSONL with journal dictionary |


### 2. Classifier

location `data/classifiers/`

```
MultinomialNB_model.joblib
```

#### Explanation

This file is the scikit-learn classifier Multinomial NB. This is necessary 
to classify the query.

### 3. Search Utils

location `data/search_utils/`

```
bow.pkl.bz2
tfidf.pkl.bz2
```

#### Explanation

| File   | Description  |
|---|---|
| bow.pkl.bz2 | Gensim Bag of Word Model |
| tfidf.pkl.bz2 | Gensim TFIDF model |





