import itertools
import multiprocessing as mp
import pickle
import re
import requests
import typing as t
import urllib.request, json
from io import StringIO, BytesIO
from pathlib import Path

import shutil
import bz2
import jsonlines
import metapub
import numpy as np
from bs4 import BeautifulSoup
from nltk import edit_distance
from metapub import PubMedFetcher
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser
from selenium import webdriver
from xvfbwrapper import Xvfb

from index.tfidf_vectorizer import clean_and_tokenize_text
from config import (
    PAPERS_JSON_FOLDER,
    BIOJOURNALS_CATEGORIES_FILE,
    BIOPAPERS_JSON_PATH,
    BIOJOURNALS_FILE,
    BIOPAPERS_WOUT_ABSTRACT_JSON_PATH,
    BIOPAPERS_W_ABSTRACT_JSON_PATH,
    INDECES_FOLDER,
)


def clean_text(text: str) -> str:
    # Remove string control characters:
    text = re.sub(r"[\n\r\t]", "", text)
    # Remove special characters but not space
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text)
    return text.lower()


def build_journal_category_dict(
    journals_categories_path: Path = BIOJOURNALS_CATEGORIES_FILE,
) -> (dict, list):
    """
    Creates a dictionary of {journal : category} form

    Parameters
    ----------
    journals_categories_path: Path
        Path to journals categories

    Returns
    -------
    journal_to_category: dict
        Dictionary {journal : category}
    categories_list: list
        List of categories in the journal_to_category dictionary.
    """
    # Initialize dict:
    journal_to_category = {}
    categories_list = []
    # Open file and read line by line
    with open(journals_categories_path, "r") as f:
        flines = f.readlines()
        for line in flines:
            # Extract category and journals
            category, journals = line.split(" - ", maxsplit=1)
            # Save category to list:
            categories_list.append(category)
            # Split journals by comma:
            for journal in journals.split(","):
                # Clean text:
                clean_journal = "".join(clean_and_tokenize_text(journal))
                # Add journal to dict:
                journal_to_category[clean_journal] = category

    return journal_to_category, categories_list


class BiopapersFilter:
    """
    Filters papers from unpaywall and saves all the bio-related papers to file.
    """

    def __init__(
        self,
        biojournals_file: Path = BIOJOURNALS_FILE,
        unpaywall_path: Path = PAPERS_JSON_FOLDER,
        output_path: Path = BIOPAPERS_JSON_PATH,
    ):

        # Load Biojournals from text and normalize text:
        self.biojournals = np.genfromtxt(
            biojournals_file, delimiter="\n", dtype="str"
        ).tolist()
        self.biojournals = [j.lower() for j in self.biojournals]
        self.biojournals = [re.sub("\W+", "", j) for j in self.biojournals]
        # Save paths to self:
        self.unpaywall_path = unpaywall_path
        self.output_path = output_path

        self.select_and_save_biopapers()

    def select_and_save_biopapers(self):
        """
        Loads unpaywall jsonlines, filters for biojournals and saves them to a file.

        Parameters
        ----------
        unpaywall_path: Path
            Path to unpaywall's JSONL file.
        output_path: Path
            Output path for JSONL file with biopaper only.

        """
        biojournals_count = 0

        # Open JSONL Unpaywall file:
        with jsonlines.open(self.unpaywall_path) as reader, jsonlines.open(
            self.output_path, mode="a"
        ) as writer:
            # Create Muliprocessing Pool:
            pool = mp.Pool()
            # Open output:
            for ret in pool.imap(self.is_bio_journal, reader):
                if ret:
                    writer.write(ret)
                    biojournals_count += 1

        print(f"Found {biojournals_count} Biology-related journals.")

    def is_bio_journal(self, paper_dict: dict) -> t.Optional[dict]:
        """
        Check if journal is similar to biojournals available

        Parameters
        ----------
        paper_dict: dict
            Dictionary of the paper with journal name

        Returns
        -------
        journal_dict: dict
            Dictionary of the paper with journal name if paper is about biology.

        """
        if paper_dict["journal_name"]:
            curr_journal = paper_dict["journal_name"].lower()
            curr_journal = re.sub("\W+", "", curr_journal)
            if curr_journal in self.biojournals:
                return paper_dict
            else:
                return None


class AbstractDownloader:
    """
    Downloads abstracts for papers in JSONL file
    """

    def __init__(
        self,
        biopapers_path: Path = BIOPAPERS_JSON_PATH,
        output_path_with_abstract: Path = BIOPAPERS_W_ABSTRACT_JSON_PATH,
        output_path_without_abstract: Path = BIOPAPERS_WOUT_ABSTRACT_JSON_PATH,
        fast_search: bool = False,
    ):
        """
        Creates a loop through all papers and attempts to find an abstract. Uses
        multiprocessing to speed up the search process

        Parameters
        ----------
        biopapers_path: path
            Path to biopapers jsonl file
        output_path_with_abstract: path
            Output of biopapers jsonl file with abstract
        output_path_without_abstract: path
            Output of biopapers jsonl file without abstract
        fast_search: bool
            Whether to attempt to download abstracts through Selenium (True) or
            not (False).

        Returns
        -------
        results_stats: dict
            Dictionary {source_type: count}
        """
        self.biopapers_path = Path(biopapers_path)
        self.output_path_with_abstract = Path(output_path_with_abstract)
        self.output_path_without_abstract = Path(output_path_without_abstract)
        self.fast_search = fast_search
        self.obtain_and_save_abstract()

    def obtain_and_save_abstract(self):
        # Create stats for results
        results_stats = {
            k: 0 for k in ["bioarxiv", "pubmed", "crossref", "selenium", "na"]
        }
        if Path(self.output_path_with_abstract).exists() and Path(
            self.output_path_without_abstract.exists()
        ):
            # Calculate last papers searched overall so they can be skipped
            with jsonlines.open(
                self.output_path_with_abstract, mode="r"
            ) as wab, jsonlines.open(
                self.output_path_without_abstract, mode="r"
            ) as woutab:
                last_checkpoint = len(list(wab)) + len(list(woutab))
        else:
            last_checkpoint = 0
        # Open output and input files:
        with jsonlines.open(self.biopapers_path) as reader, jsonlines.open(
            self.output_path_with_abstract, mode="a"
        ) as writer_with, jsonlines.open(
            self.output_path_without_abstract, mode="a"
        ) as writer_without:
            print(f"Last Checkpoint was at {last_checkpoint}")
            # Create Muliprocessing Pool:
            pool = mp.Pool()
            # Open reader and start from checkpoint rather than from 0
            checkpoint_reader = itertools.islice(reader, last_checkpoint, None)
            print(checkpoint_reader)
            # For each paper, extract abstract:
            for paper_w_abstract_dict in pool.imap(
                self.get_abstract, checkpoint_reader
            ):
                if paper_w_abstract_dict["abstract_source"] == "na":
                    writer_without.write(paper_w_abstract_dict)
                else:
                    writer_with.write(paper_w_abstract_dict)
                # Logging the source of the paper
                results_stats[paper_w_abstract_dict["abstract_source"]] += 1
                # Delete to save memory:
                del paper_w_abstract_dict
        print("Finished processing results")
        print(results_stats)
        return results_stats

    def get_abstract(self, paper_dict: dict) -> dict:
        """
        Fetches Abstracts of selected papers in "bioarxiv", "pubmed", "crossref" and
        attempts to download the HTML page if the abstract is not available.

        Parameters
        ----------
        paper_dict: dict
            JSONLines dictionary with the Unpaywall papers
        Returns
        -------
        paper_dict: dict
            JSOLines dictionary with the abstract added

        """
        doi = paper_dict["doi"]
        doi_url = paper_dict["doi_url"]
        # Attempt to use Bioarxiv API
        abstract_status, abstract = self._get_abstract_w_bioarxiv(doi)
        if abstract_status and abstract:
            paper_dict["abstract"] = abstract
            paper_dict["abstract_source"] = "bioarxiv"
        else:
            # Attempt to use Pubmed:
            abstract_status, abstract = self._get_abstract_w_pubmed(doi)
            if abstract_status and abstract:
                paper_dict["abstract"] = abstract
                paper_dict["abstract_source"] = "pubmed"
            else:
                # Attempt to use Crossref:
                abstract_status, abstract = self._get_abstract_w_crossref(doi)
                if abstract_status and abstract:
                    paper_dict["abstract"] = abstract
                    paper_dict["abstract_source"] = "crossref"
                else:
                    # Attempt to use Selenium
                    if not self.fast_search:
                        print("No methods have extracted the abstract, trying Selenium")
                        abstract_status, abstract = self._get_abstract_w_selenium(
                            doi_url
                        )
                        if abstract_status and abstract:
                            paper_dict["abstract"] = abstract[:650]
                            paper_dict["abstract_source"] = "selenium"
                        else:
                            print("Abstract not found at all.")
                            paper_dict["abstract"] = ""
                            paper_dict["abstract_source"] = "na"
                    else:
                        print("Abstract not found at all.")
                        paper_dict["abstract"] = ""
                        paper_dict["abstract_source"] = "na"

        return paper_dict

    def _get_abstract_from_pdf(pdf_url) -> t.Union[bool, t.Optional[str]]:
        found_abstract = False
        try:
            pdf_response = requests.get(pdf_url)
            output_string = StringIO()
            with BytesIO(pdf_response.content) as open_pdf_file:
                parser = PDFParser(open_pdf_file)
                doc = PDFDocument(parser)
                rsrcmgr = PDFResourceManager()
                device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
                interpreter = PDFPageInterpreter(rsrcmgr, device)
                for page in PDFPage.create_pages(doc):
                    interpreter.process_page(page)
                    break
                abstract = output_string.getvalue().lower()
                abstract = clean_text(abstract)
                if "abstract" in abstract:
                    abstract = abstract.split("abstract", 1)[-1]
                found_abstract = True
            return found_abstract, abstract
        except:
            print("PDF Not found.")
            return found_abstract, None

    def _get_abstract_w_bioarxiv(self, doi: str) -> t.Union[bool, t.Optional[str]]:
        found_abstract = False
        try:
            # Open URL and attempt retrieval
            with urllib.request.urlopen(
                f"https://api.biorxiv.org/details/biorxiv/{doi}"
            ) as url:
                data = json.loads(url.read().decode())
                if data["messages"][0]["status"] == "ok":
                    abstract = data["collection"][-1]["abstract"]
                    # Jackpot baby
                    found_abstract = True
                    print("Abstract Found.")
                    return found_abstract, abstract
                else:
                    # print('Abstract not found, returning None.')
                    return found_abstract, None
        except:
            return found_abstract, None

    def _get_abstract_w_crossref(self, doi: str) -> t.Union[bool, t.Optional[str]]:
        found_abstract = False
        try:
            # Open URL and attempt retrieval
            with urllib.request.urlopen(f"https://api.crossref.org/works/{doi}") as url:
                data = json.loads(url.read().decode())
                if "abstract" in data["message"].keys():
                    abstract = data["message"]["abstract"]
                    abstract = abstract.lstrip("<jats:p>")
                    abstract = abstract.rstrip("</jats:p>")
                    # If abstract is sufficiently long
                    if len(abstract) > 20:
                        # Jackpot baby
                        found_abstract = True
                        print("Abstract Found.")
                        return found_abstract, abstract
                    else:
                        print("Abstract was too short, returning None.")
                        return found_abstract, None
                else:
                    # If the link to pdf is available and we are not fast search:
                    if "link" in data["message"].keys() and not self.fast_search:
                        # Extract URL
                        url = data["message"]["link"][0]["URL"]
                        # Take PDF url:
                        if url.endswith(".pdf"):
                            found_abstract, abstract = self._get_abstract_from_pdf(url)
                            return found_abstract, abstract
                        # PDF abstract not found:
                        else:
                            return found_abstract, None
                    return found_abstract, None
        except:
            return found_abstract, None

    def _get_abstract_w_pubmed(self, doi: str) -> t.Union[bool, t.Optional[str]]:
        found_abstract = False
        # Initialize Fetcher:
        fetch = PubMedFetcher()
        try:
            article = fetch.article_by_doi(doi)
            abstract = article.abstract
            # If abstract is sufficiently long
            if len(abstract) > 20:
                # Jackpot baby
                found_abstract = True
                print("Abstract Found.")
                return found_abstract, abstract
            else:
                print("Abstract was too short, returning None.")
                return found_abstract, None
        except metapub.exceptions.MetaPubError:
            return found_abstract, None
        except:
            print("Unknown exception, returning None")
            return found_abstract, None

    def _get_abstract_w_selenium(self, doi_url: str) -> t.Union[bool, t.Optional[str]]:
        found_abstract = False
        is_vdisplay_on = False
        try:
            try:
                # attempt to start virtual display
                vdisplay = Xvfb(width=1280, height=740)
                vdisplay.start()
                is_vdisplay_on = True
            except:
                is_vdisplay_on = False

            # Create web-browser session
            options = webdriver.FirefoxOptions()
            options.add_argument("--headless")
            options.add_argument("--enable-javascript")
            web_session = webdriver.Firefox()
            found_abstract = False
            # Open URL + Save HTML
            web_session.get(doi_url)
            doi_html_page = web_session.page_source
            # Close page
            web_session.quit()
            # If virtual display has started:
            if is_vdisplay_on:
                vdisplay.stop()
            soup = BeautifulSoup(doi_html_page, "html.parser")
            text = soup.get_text().lower()
            text = clean_text(text)
            # Extract all text after "Abstract"
            abstract = text.split("abstract", 1)[-1]
            if len(abstract) > 0:
                found_abstract = True
                return found_abstract, abstract
            else:
                return found_abstract, None
        except:
            try:
                # Attempt to close everything to avoid out of memory errors:
                web_session.dispose()
                web_session.quit()
                if is_vdisplay_on:
                    vdisplay.stop()
                return found_abstract, None
            except:
                return found_abstract, None


class CategoryAnnotator:
    """
    Annotates category for papers in JSONL file. Outputs an index of papers per category.
    """
    def __init__(
        self,
        indeces_folder: Path = INDECES_FOLDER,
        biopapers_with_abstract: Path = BIOPAPERS_W_ABSTRACT_JSON_PATH,
        biopapers_without_abstract: Path = BIOPAPERS_WOUT_ABSTRACT_JSON_PATH,
        journals_categories_path: Path = BIOJOURNALS_CATEGORIES_FILE,
        pool_all_categories: bool = False,
    ):
        """
        Parameters
        ----------
        indeces_folder: Path
            Path to biopapers
        biopapers_with_abstract: Path
            Path to biopapers with abstract
        biopapers_without_abstract: Path
            Path to biopapers without abstract
        journals_categories_path: Path
            Path to Journals categories. Either .txt format or bz2
        pool_all_categories: bool
            Whether to have all the papers in one large category instead of multiple ones.
        """
        self.indeces_folder = indeces_folder
        self.biopapers_with_abstract = biopapers_with_abstract
        self.biopapers_without_abstract = biopapers_without_abstract
        self.journals_categories_path = journals_categories_path
        self.pool_all_categories = pool_all_categories
        self.count = 0

        if self.pool_all_categories:
            self.categorise_and_extract_papers(self.biopapers_with_abstract, checkpoint=0, category_to_file_dict={})
            self.categorise_and_extract_papers(self.biopapers_without_abstract, checkpoint=0, category_to_file_dict={})
        else:
            # Get journals categories:
            # if txt file, parse it
            if self.journals_categories_path.suffix == ".txt":
                (
                    self.journal_to_category,
                    self.categories_list,
                ) = build_journal_category_dict(self.journals_categories_path)
            elif self.journals_categories_path.suffix == ".bz2":
                with bz2.BZ2File(self.journals_categories_path, "rb") as f:
                    self.journal_to_category = pickle.load(f)
                    self.categories_list = list(
                        np.unique(self.journal_to_category.values())
                    )
            else:
                raise ValueError(
                    f"Journal categories file is of file type {journals_categories_path.suffix}. Supported types are .txt and .bz2"
                )
            # Check all the category index in the folder
            self.category_outpaths_list = list(self.indeces_folder.rglob("index_*"))
            # Create category index
            self.create_category_index()
            # Save journals with nltk to file (saves time)
            self.save_journal_to_category_dict()
            print(f"Processed {self.count} files.")

    def create_category_index(self):
        """
        Creates an index for each category. Uses a dictionary of opened files.
        """
        # Dictionary storing all categories of papers created
        category_to_file_dict = {}
        # Count papers
        papers_count = 0
        if len(self.category_outpaths_list) > 0:
            # Calculate last papers searched overall so they can be skipped
            if len(self.category_outpaths_list) > 0:
                # For each path available:
                for cat_path in self.category_outpaths_list:
                    # Extract category name:
                    curr_category = str(cat_path.stem).split("index_")[-1]
                    with jsonlines.open(cat_path, mode="r") as reader:
                        # Count the papers in category:
                        papers_count += len(list(reader))
                    # open file in append mode and add to dictionary:
                    writer = jsonlines.open(cat_path, mode="a")
                    # Save open file to dict:
                    category_to_file_dict[curr_category] = writer

        # Count how many papers with abstract there are:
        abstract_checkpoint = 0
        with jsonlines.open(self.biopapers_with_abstract, mode="r") as reader:
            abstract_checkpoint += len(list(reader))
        # If papers processed is higher than abstract papers,
        # move to papers without abstract
        if papers_count >= abstract_checkpoint:
            print(
                f"Finished processing papers with abstract, moving to papers without."
            )
            papers_count -= abstract_checkpoint
            # Process papers without abstract:
            category_to_file_dict = self.categorise_and_extract_papers(
                self.biopapers_without_abstract, papers_count, category_to_file_dict
            )
        else:
            # Process papers with abstract:
            category_to_file_dict = self.categorise_and_extract_papers(
                self.biopapers_with_abstract, papers_count, category_to_file_dict
            )
            # Process papers without abstract
            category_to_file_dict = self.categorise_and_extract_papers(
                self.biopapers_without_abstract, 0, category_to_file_dict
            )

        # Close files:
        for open_file in category_to_file_dict.values():
            open_file.close()

    def categorise_and_extract_papers(
        self, paper_to_open: Path, checkpoint: int, category_to_file_dict: dict
    ) -> dict:
        """
        Categorises and extracts papers. Adds the handle "category" to the json file.

        Parameters
        ----------
        paper_to_open: Path
            Path to paper to open. Either with or without abstract.
        checkpoint: int
            Integer indicating how many papers can be skipped, eg. if the process was interrupted.
        category_to_file_dict: dict
            Dictionary of opened files.

        Returns
        -------
        category_to_file_dict: dict
            Updated dictionary of opened files.

        """
        with jsonlines.open(paper_to_open, mode="r") as reader:
            # Create Muliprocessing Pool:
            pool = mp.Pool()
            # Open reader and start from checkpoint rather than from 0
            checkpoint_reader = itertools.islice(reader, checkpoint, None)
            print(f"Current checkpoint: {checkpoint}")
            # For each paper:
            for paper_w_category_dict in pool.imap(
                self.get_category, checkpoint_reader
            ):
                curr_category = paper_w_category_dict["category"]
                # If category file is present and opened:
                if curr_category in category_to_file_dict.keys():
                    category_to_file_dict[curr_category].write(paper_w_category_dict)
                else:
                    # Create jsonl path
                    category_path = self.indeces_folder / f"index_{curr_category}.jsonl"
                    # Open file and add it to the dictionariy
                    writer = jsonlines.open(category_path, mode="a")
                    category_to_file_dict[curr_category] = writer
                    # Write paper:
                    writer.write(paper_w_category_dict)
                # Increase count:
                self.count += 1

        return category_to_file_dict

    def get_category(self, paper_dict: dict) -> dict:
        """
        Extract category based on journal. If category is not found it uses NLTK
        to find the closest match. Uses gensim preprocessing as it is faster and more accurate.

        Parameters
        ----------
        paper_dict: dict
            Jsonlines dictionary for a paper.

        Returns
        -------
        paper_dict: dict
            Jsonline dictionary with the handle "category".
        """
        # If merging all categories:
        if self.pool_all_categories:
            paper_dict["category"] = "all"
        # Else divide index by category:
        else:
            journal = paper_dict["journal_name"]
            # Clean text:
            clean_journal = "".join(clean_and_tokenize_text(journal))
            # If journal is present in categories:
            if clean_journal in self.journal_to_category.keys():
                paper_dict["category"] = self.journal_to_category[clean_journal]
            else:
                print(
                    f"{journal} not found in Journals. Using NLTK to find closest match."
                )
                unique_journals = self.journal_to_category.keys()
                # Create a dictionary of distances:
                journal_distance_dict = {}
                # For each journal:
                for curr_journal in unique_journals:
                    # Measure distance
                    journal_distance_dict[curr_journal] = edit_distance(
                        clean_journal, curr_journal
                    )
                # Sort by smallest to largest by distance value
                journal_distances_list = sorted(
                    journal_distance_dict.items(), key=lambda x: x[1]
                )
                # Select closes journals:
                closest_journal = journal_distances_list[0][0]
                closest_category = self.journal_to_category[closest_journal]
                print(
                    f"Closest journal for entry {journal} was {closest_journal} of category {closest_category}."
                )
                # Add newly found journal to dictionaries:
                self.journal_to_category[clean_journal] = closest_category
                paper_dict["category"] = self.journal_to_category[clean_journal]
        return paper_dict

    def save_journal_to_category_dict(self) -> dict:
        """
        Saves dictionary of journal->category and category->journal to file.
        the journal_to_category dict is compressed with bz2, while category_to_journal_dict
        is kept as jsonlines for readability.

        Returns
        -------
        category_to_journal_dict: dict
            Category to Journal dictionary
        """
        # Initialize output dictionary:
        category_to_journal_dict = {}
        for journal_name, category in self.journal_to_category.items():
            # If category exists, append journal name
            if category in category_to_journal_dict:
                category_to_journal_dict[category].append(journal_name)
            # else create a list with the journal
            else:
                category_to_journal_dict[category] = [journal_name]
        # Save and compress dictionary:
        with bz2.BZ2File(
            self.journals_categories_path.with_suffix(".bz2"), "wb"
        ) as writer:
            pickle.dump(self.journal_to_category, writer)
        # Save inverted dictionary for the records
        inverted_outpath = Path(str(self.journals_categories_path) + "_inverted")
        with jsonlines.open(inverted_outpath.with_suffix(".jsonl"), "w") as writer:
            writer.write(category_to_journal_dict)

        return category_to_journal_dict


def merge_abstract_no_abstract_jsonl(
    paper_w_abstract: Path = BIOPAPERS_W_ABSTRACT_JSON_PATH,
    paper_wout_abstract: Path = BIOPAPERS_WOUT_ABSTRACT_JSON_PATH,
    output_file: Path = BIOPAPERS_JSON_PATH,
):
    """
    Merges papers with and without abstract into one file.

    Parameters
    ----------
    paper_w_abstract: Path
        Papers with abstract path
    paper_wout_abstract: Path
        Papers with abstract path
    output_file: Path
        Output file path

    """
    # Open outfile
    with open(output_file, "wb") as wfd:
        # For both papers:
        for f in [paper_w_abstract, paper_wout_abstract]:
            with open(f, "rb") as fd:
                # Merge files
                shutil.copyfileobj(fd, wfd)
                # add new line at the end of the file
                wfd.write(b"\n")


if __name__ == "__main__":
    # Filter all papers by bio-journals:
    # BiopapersFilter()
    # Download all abstracts:
    # AbstractDownloader()
    # Annotate papers with category:
    CategoryAnnotator()
    # Annotate papers with the same category:
    # CategoryAnnotator(pool_all_categories=True)
    # Merge papers with abstract and category:
    # merge_abstract_no_abstract_jsonl()
