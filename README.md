<div align="center">
  <img src="img/logo.png"><br>
  <h3>Medical Search Engine</h3><br>
  <h3>Text Techonologies for Data Science 2020-21</h3><br>
</div>

[MediSia](https://github.com/universvm/MediSia) is an open-source search 
engine which uses Python backend in Gensim + Django and a user-friendly 
front-end built with Angular. It indexes medical papers from [Unpaywall](https://github.com/universvm/MediSia)) to 
promote open-access research.

## Why?

With the coronavirus pandemic, more and more people have used the web to 
expand their medical knowledge. At the same time more and more inaccurate 
or fake information has been produced. The aim of the project is to 
facilitate access to reputable sources of medical knowledge and promote 
open-access research. 

### Contributions

- A new SE system used to retrieve medical and biological literature-based information available on the Internet across multiple sources for both users with and without previous medical or scientific training
    
- A system that is capable of taking a simple (or complex) query specification depending on the user's background and match it to a topic or set of topics commonly used in the medical and biological fields for faster processing and search speed.
    
- A literature retrieval database powered by a topical web crawler and an indexing strategy that exploits the advantage of medical and biology domain knowledge to filter irrelevant search results.

### How it works

Below is a diagram that illustrates the general search process and the different types of searches available:

![](img/overview.png | width=300)
*Overview of search retrieval system.*

![](img/overview_2.png | width=300)
*Distinction across three search functionalities*

For a ranked search this is the main logic:

- Create a TF-IDF vectorizer object
- Use fit-transform method to represent each docu-ment in the index of interest as a weighted TF-IDFvector and save into an object for use during queryprocessing
- Similarly, retrieve the TF-IDF vector representationof the query using the transform method
- Compute the cosine similarity score for the selectquery against all the document vectors
- Compile a results array ranking documents withrespect to the query by score
- Acquire the top 300 results to allow for follow-upsearch, if desired, and return the top 10 results tothe user by pagination 

## Screenshots

## How to run

### Environment Setup

We use conda as an environment manager. Simply run:

```shell
conda env create -f environment.yml
```

Activate the environment with:

```shell
conda activate medisia
```

Alternatively you can use the requirements.txt to install the required packages.

### Front-End Setup

The front-end requires npm and Angular. Once installed simply 

```shell
cd /ui/search-frontend/
```

and then run

```shell
npm install .
```

### Dataset Download

This project requires you to donwload the dataset from unpaywall and 
process it using the [unpaywall_process.py](https://github.com/universvm/MediSia/blob/main/django_backend/medical_ir/index/unpaywall_process.py). This has an option to also download abstracts from journals using bioRxiv, PubMed and crossref. If nothing is found it will try to use Selenium to download the abstract. 

This data should be positioned in the data folder `django_backend/medical_ir/data/paper`

Please make sure you read the functions thoroughly and once you've uncommented and commented the functions you need simply run:

```shell
python django_backend/medical_ir/index/unpaywall_process.py 
```

Make sure you have enough space. Unpaywall may take up 200+ GB uncompressed.

### BOW and TFIDF Model

To create your custom models, simply run:

```shell
python django_backend/medical_ir/index/tfidf_vectorizer.py
```

this should create the models under the folder `django_backend/medical_ir/data/search_utils`. The documents will be vectorized and saved as market matrix Gensim format (it might take a while).

### ML query classifier

We use a machine learning model to classify the query and reduce the number of documents to search. The query is classfied in 27 different classes (categories, topics) of medical journals (full list here: https://github.com/universvm/MediSia/blob/main/django_backend/medical_ir/data/journals/journals_categories.txt). The model will learn to associate terms of the title and abstract of the paper to specific categories. To train a model run:

```shell
python django_backend/medical_ir/query_classifier/train_classifiers.py
```

This trains these models using SKLearn MultinomialNB(), GaussianNB(),  BernoulliNB(), SGDClassifier(loss="log"). Gaussian NB is the slowest of them all and was removed. Perfomances of each model is shown below.

|Metric       |MultinomialNB|Bernoulli NB|SGD |
|-------------|-------------|------------|----|
|Accuracy     |0.38         |0.32        |0.33|
|Top3 Accuracy|0.61         |0.52        |0.52|
|Top5 Accuracy|0.72         |0.63        |0.64|
|Precision    |0.39         |0.38        |0.36|
|Recall       |0.39         |0.32        |0.33|
|Time (s)     |1.14         |2.76        |1.1 |

Time refers to the time taken to classify 260K articles.

The top5 accuracy indicates that 5 indeces can be searched at once and still retrieve relevant results.

### Running the search engine

The search engine uses Redis to cache results to make the search faster and Django to communicate with the front end. To run the search engine run:

```shell
cd /ui/search-frontend/
```

```shell
redis-server & python ../../django_backend/manage.py runserver 8000 & ng serve
```

## Optimisation and Metrics

To optimise search, each paper was classified into 1 of 27 categories using the journal name (full list here: https://github.com/universvm/MediSia/blob/main/django_backend/medical_ir/data/journals/journals_categories.txt). These were compiled manually from Wikipedia. 

Some indeces for example medicine took about 5M documents which significantly decreased the speed at which to search medicine. We therefore split the index into smaller sub-indeces called "shards". These take advantage of multiprocessing which searches through parts of them simoultaneously. This was done for the "all" categories (ie. an index that includes all the papers) which is used for the deep search. This reduced the time to search the term "coronavirus" as Deep Search from 67.8 to 24.2 seconds.

### Deep Search 

Searching for the term "Coronavirus" as a Deep Search (ie. through 13M+) takes 24.2 seconds, and an additional 14s seconds to paginate and display the results to the user in the front-end.

A cached query takes about 1 second to be retrieved.

### Topic Search

A topic search varies in speed depending on the topic (ie. some topics have more knowledge than others eg. medicine > forestry). Searching for the term "coronavirus" in the category "virology" takes 3.847 seconds

### Magic Search

The magic search reduces the number of indeces to search (compared to a deep search), by classifying the query and computing similarities against the top 3 indeces returned by the classifier. Searching for "coronavirus" takes about 5.04 seconds. 

## Python Style

We used PEP8 and BLACK (https://black.readthedocs.io/en/stable/) as well as 
typing docstring. 
