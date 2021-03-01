import csv
from pathlib import Path
from numpy import inf
import numpy as np

from gensim.corpora import MmCorpus
from gensim.matutils import sparse2full
from joblib import dump
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score,
    top_k_accuracy_score,
)
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from tqdm import tqdm

from config import INDECES_FOLDER
from index.unpaywall_process import build_journal_category_dict


class ModelTrainer:
    """
    Trains a Scikit Learn model using partial fit and random sampling.
    """
    def __init__(
        self,
        epochs: int,
        val_split: float,
        bow_length: int,
        skmodel,
        indeces_folder: Path = INDECES_FOLDER,
    ):
        """
        Parameters
        ----------
        epochs: int
            Number of epochs.
        val_split: float
            Split for validation data. (2/3 are for validation and 1/3 for test)
        bow_length: int
            Number of features in the BoW.
        skmodel: Scikit Learn model
            Scikit Learn model which supports partial fit
        indeces_folder: Path
            Path to all indeces and market matrices for each category.
        """
        self.epochs = epochs
        self.val_split = val_split
        self.indeces_folder = indeces_folder
        self.bow_length = bow_length
        self.skmodel = skmodel
        # Extract categories:
        _, categories_list = build_journal_category_dict()
        self.categories = sorted(categories_list)
        self.label_encoder = LabelEncoder()
        # Fit categories to label encoder
        self.label_encoder.fit(self.categories)

    def train(self):
        """
        Trains a scikit learn model with partial fit
        """
        # Get document numbers per category:
        (
            categories_to_corpus,
            train_category_to_docIDs,
            val_category_to_docIDs,
            test_category_to_docIDs,
            smallest_doc_length,
            total_n_docs,
        ) = self.get_docs_train_test_val_set()
        # Begin training:
        for i in tqdm(range(self.epochs)):
            # Calculate documents per batch
            n_docs_per_batch = int(smallest_doc_length * 0.01)
            # Partial fit:
            self.train_model(
                i,
                categories_to_corpus,
                train_category_to_docIDs,
                val_category_to_docIDs,
                n_docs_per_batch,
            )
        # Begin testing:
        print("Finished training. Starting test...")
        metrics = self.test_model(test_category_to_docIDs, categories_to_corpus)
        # Save model to file:
        self.save_model(metrics)

    def get_docs_train_test_val_set(self) -> (dict, dict, dict, dict, int, int):
        """
        Obtains all documents for each class and divides them into train, test
        and validation set.

        Returns
        -------
        categories_to_corpus: dict
            Category to category market matrix corpus.
        train_category_to_docIDs: dict
            Category to DocIDs for train data.
        val_category_to_docIDs: dict
            Category to DocIDs for val data.
        test_category_to_docIDs: dict
            Category to DocIDs for test data.
        smallest_doc_length: int
            Smallest number of document for class. This is necessary for
            underbalancing.
        total_n_docs: int
            Total number of documents in all classes.
        """
        # Get list of corpora files in index:
        mm_corpora_files = list(self.indeces_folder.glob(f"**/*.mm"))
        # TODO FIXME:
        self.categories = [c.stem.split("_")[0] for c in mm_corpora_files]
        categories_to_corpus = {}
        # Double check categories:
        assert len(mm_corpora_files) == len(
            self.categories
        ), f"Expected to find {len(self.categories)} files but  found {len(mm_corpora_files)}."
        # Pre-index with empty list:
        train_category_to_docIDs = {k: [] for k in self.categories}
        val_category_to_docIDs = {k: [] for k in self.categories}
        test_category_to_docIDs = {k: [] for k in self.categories}
        # Smallest length of docids (used for undersampling):
        smallest_doc_length = inf
        total_n_docs = 0
        # Loop and obtain ids:
        for corpus_file, category in zip(mm_corpora_files, self.categories):
            # Load corpus:
            category_corpus = MmCorpus(str(corpus_file))
            # Add open file to dictionary:
            categories_to_corpus[category] = category_corpus
            # Calculate the lenght of the docs:
            corpus_length = len(category_corpus)
            total_n_docs += corpus_length
            # Update smallest length for undersampling:
            if corpus_length < smallest_doc_length:
                smallest_doc_length = corpus_length
            # Split into train validation and test
            X_train, X_val_test = train_test_split(
                list(range(corpus_length)), test_size=self.val_split, random_state=42
            )
            X_val, X_test = train_test_split(
                X_val_test, test_size=self.val_split * (2 / 3), random_state=42
            )
            # Add range of docIDs to dictionary:
            train_category_to_docIDs[category] = X_train
            val_category_to_docIDs[category] = X_val
            test_category_to_docIDs[category] = X_test

        return (
            categories_to_corpus,
            train_category_to_docIDs,
            val_category_to_docIDs,
            test_category_to_docIDs,
            smallest_doc_length,
            total_n_docs,
        )

    def train_model(
        self,
        iteration: int,
        categories_to_corpus: dict,
        train_category_to_docIDs: dict,
        val_category_to_docIDs: dict,
        n_docs_per_batch: int,
    ):
        # Load train data:
        X_train, y_train = self.load_batch_data(
            categories_to_corpus, train_category_to_docIDs, n_docs_per_batch
        )
        # Fit current training batch:
        self.skmodel.partial_fit(X_train, y_train, classes=np.unique(y_train))
        # Report Performance
        print(f"{iteration} Train: {self.skmodel.score(X_train, y_train)}")
        # Delete to save space:
        del X_train
        del y_train
        # Load validation set
        X_val, y_val = self.load_batch_data(
            categories_to_corpus, val_category_to_docIDs, n_docs_per_batch
        )
        val_score = self.skmodel.score(X_val, y_val)
        print(f"{iteration} Validation: {val_score}")
        # Delete to save space:
        del X_val
        del y_val

    def test_model(
        self, test_category_to_docIDs: dict, categories_to_corpus: dict
    ) -> dict:
        """
        Test model performance on test set. Calculates metrics: accuracy, top2,
        top3, precision, recall and AUC.

        Parameters
        ----------
        test_category_to_docIDs: dict
            Category to DocIDs for test data.
        categories_to_corpus: dict
            Category to category market matrix corpus.

        Returns
        -------
        metrics: dict
            Dictionary with accuracy, top2, top3, precision, recall and auc
        """
        # Load data:
        X_test, y_test = self.load_batch_data(
            categories_to_corpus, test_category_to_docIDs, -1
        )
        # Predict data:
        y_predicted = self.skmodel.predict(X_test)
        y_score = self.skmodel.predict_proba(X_test)
        # Calculate metrics:
        metrics = {
            "accuracy": 0,
            "top2": 0,
            "top3": 0,
            "precision": 0,
            "recall": 0,
            "auc": 0,
        }
        test_accuracy = accuracy_score(y_true=y_test, y_pred=y_predicted)
        test_precision = precision_score(
            y_true=y_test, y_pred=y_predicted, average="macro"
        )
        test_recall = recall_score(y_true=y_test, y_pred=y_predicted, average="macro")
        test_auc = roc_auc_score(
            y_true=y_test, y_score=y_score, average="macro", multi_class="ovr"
        )
        test_top2 = top_k_accuracy_score(
            y_true=y_test, y_score=y_score, k=2, labels=np.unique(y_test)
        )
        test_top3 = top_k_accuracy_score(
            y_true=y_test, y_score=y_score, k=3, labels=np.unique(y_test)
        )
        # Save and Report metrics:
        metrics["accuracy"] = test_accuracy
        metrics["top2"] = test_top2
        metrics["top3"] = test_top3
        metrics["precision"] = test_precision
        metrics["recall"] = test_recall
        metrics["auc"] = test_auc
        print(metrics)
        # Delete to save space:
        del X_test
        del y_test

        return metrics

    def load_batch_data(
        self,
        categories_to_corpus: dict,
        category_to_docIDs: dict,
        n_docs_per_batch: int,
        shuffle: bool = True,
    ) -> (np.ndarray, np.ndarray):
        """
        Loads batch of data from corpora dictionaries.

        Parameters
        ----------
        categories_to_corpus:
            Categories to Category Corpora Market Matrix
        category_to_docIDs:
            Category to DocID dictionary.
        n_docs_per_batch: int
            Number of docs per batch
        shuffle: bool
            Whether to shuffle the data. Default = True

        Returns
        -------
        X_set, y_set: np.ndarray
            Set of training points and labels respectively
        """
        X_set = []
        y_set = []
        for cat in self.categories:
            # Get category corpus
            curr_corpus = categories_to_corpus[cat]
            # Get documents for current batch:
            cat_batch = category_to_docIDs[cat]
            if n_docs_per_batch == -1:
                n_docs_per_batch = len(cat_batch)
            # Randomly sample from documents within class:
            batch_docs = np.random.choice(cat_batch, n_docs_per_batch)
            # Extract corpus of each document:
            for doc_idx in batch_docs:
                # Append corpus:
                X_set.append(sparse2full(curr_corpus[doc_idx], length=self.bow_length))
            # Get labels
            y_set += [self.label_encoder.transform([cat])] * len(batch_docs)
        # Check labels and training samples length:
        assert len(y_set) == len(
            X_set
        ), f"Expected labels and data to have the same length but got {len(y_set)} and {len(X_set)} respectively "
        # Reshaping sets for training:
        X_set = np.array(X_set)
        y_set = np.array(y_set).flatten()
        # Shuffle datapoints
        if shuffle:
            p = np.random.permutation(len(y_set))
            return X_set[p, :], y_set[p]
        else:
            return X_set, y_set

    def save_model(self, metrics: dict):
        """
        Saves model to file.

        Parameters
        ----------
        metrics: dict or None
            Dictionary with metrics. If empty metrics won't be saved.

        """
        # Save model to file:
        dump(self.skmodel, f"{self.skmodel}_model.joblib")
        if metrics:
            # Save metrics to csv:
            w = csv.writer(open(f"{self.skmodel}_metrics.csv", "w"))
            for key, val in metrics.items():
                w.writerow([key, val])


if __name__ == "__main__":
    model = GaussianNB()
    print(vars(GaussianNB()))
    trainer = ModelTrainer(
        epochs=1, val_split=0.2, bow_length=100000, skmodel=model
    )
    trainer.train()

# from gensim.corpora import MmCorpus
# from gensim.test.utils import datapath
#
# path_to_index = INDECES_FOLDER / "biology_corpus.mm"
# corpus = MmCorpus(datapath(path_to_index))
# print(corpus[3])
# print(len(corpus))
# print(vars(corpus))
