import re
import multiprocessing as mp
import requests
import urllib.request, json
import typing as t
from pathlib import Path

import itertools
from bs4 import BeautifulSoup
import metapub
from selenium import webdriver
from metapub import PubMedFetcher
from xvfbwrapper import Xvfb
import time
import jsonlines
import numpy as np

from io import StringIO, BytesIO
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from config import (
    PAPERS_JSON_FOLDER,
    BIOPAPERS_JSON_PATH,
    BIOJOURNALS_FILE,
    BIOPAPERS_WOUT_ABSTRACT_JSON_PATH,
    BIOPAPERS_W_ABSTRACT_JSON_PATH,
)

# Load Biojournals from text and normalize text:
biojournals = np.genfromtxt(BIOJOURNALS_FILE, delimiter="\n", dtype="str").tolist()
biojournals = [j.lower() for j in biojournals]
biojournals = [re.sub("\W+", "", j) for j in biojournals]


def is_bio_journal(paper_dict: dict) -> t.Optional[dict]:
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
        if curr_journal in biojournals:
            return paper_dict
        else:
            return None


def select_and_save_biopapers(
    unpaywall_path: Path = PAPERS_JSON_FOLDER,
    output_path: Path = BIOPAPERS_JSON_PATH,
):
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
    with jsonlines.open(unpaywall_path) as reader, jsonlines.open(
        output_path, mode="a"
    ) as writer:
        # Create Muliprocessing Pool:
        pool = mp.Pool()
        # Open output:
        for ret in pool.imap(is_bio_journal, reader):
            if ret:
                writer.write(ret)
                biojournals_count += 1

    print(f"Found {biojournals_count} Biology-related journals.")


def clean_text(text: str) -> str:
    # Remove string control characters:
    text = re.sub(r"[\n\r\t]", "", text)
    # Remove special characters but not space
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text)
    return text


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
            # Identify title abstract and remove everything else:
            if "abstract" in abstract:
                abstract = abstract.split("abstract", 1)[-1]
            # Identify introduction and take everything before:
            if "introduction" in abstract:
                abstract = abstract.split("introduction", 1)[0]
            found_abstract = True
        return found_abstract, abstract
    except:
        print("PDF Not found.")
        return found_abstract, None


def _get_abstract_w_bioarxiv(doi: str) -> t.Union[bool, t.Optional[str]]:
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


def _get_abstract_w_crossref(doi: str) -> t.Union[bool, t.Optional[str]]:
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
                if "link" in data["message"].keys():
                    url = data["message"]["link"][0]["URL"]
                    if url.endswith(".pdf"):
                        found_abstract, abstract = _get_abstract_from_pdf(url)
                        return found_abstract, abstract
                    else:
                        return found_abstract, None

                # print('Abstract not found, returning None.')
                return found_abstract, None
    except:
        # print('Abstract not found, returning None.')
        return found_abstract, None


def _get_abstract_w_pubmed(doi: str) -> t.Union[bool, t.Optional[str]]:
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
        # print('Abstract not found, returning None.')
        return found_abstract, None
    except:
        print("Unknown exception, returning None")
        return found_abstract, None


def _get_abstract_w_selenium(doi_url: str) -> t.Union[bool, t.Optional[str]]:
    found_abstract = False
    try:
        vdisplay = Xvfb(width=1280, height=740)
        vdisplay.start()
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
        vdisplay.stop()
        # Attempt to find PDF url in page
        html_page = BeautifulSoup(doi_html_page)
        pdf_links = [link.get('href') for link in html_page.find_all('a') if link.get('href').endswith('pdf')]
        found_abstract, abstract = _get_abstract_from_pdf(pdf_links[0])
        if found_abstract and abstract:
            print("Found Abstract from PDF")
            return found_abstract, abstract
        else:
            soup = BeautifulSoup(doi_html_page, "html.parser")
            text = soup.get_text().lower()
            # Remove string control characters:
            text = re.sub(r"[\n\r\t]", "", text)
            # Remove special characters but not space
            text = re.sub(r"[^a-zA-Z0-9]+", " ", text)
            # Extract all text after "Abstract"
            abstract = text.split("abstract", 1)[-1]
            # TODO: We could add some other clean up functions here
            if len(abstract) > 0:
                found_abstract = True
                return found_abstract, abstract
            else:
                return found_abstract, None
    except:
        try:
            web_session.quit()
            vdisplay.stop()
            return found_abstract, None
        except:
            return found_abstract, None


def get_abstract(paper_dict: dict) -> dict:
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
    abstract_status, abstract = _get_abstract_w_bioarxiv(doi)
    if abstract_status and abstract:
        paper_dict["abstract"] = abstract
        paper_dict["abstract_source"] = "bioarxiv"
    else:
        # Attempt to use Pubmed:
        abstract_status, abstract = _get_abstract_w_pubmed(doi)
        if abstract_status and abstract:
            paper_dict["abstract"] = abstract
            paper_dict["abstract_source"] = "pubmed"
        else:
            # Attempt to use Crossref:
            abstract_status, abstract = _get_abstract_w_crossref(doi)
            if abstract_status and abstract:
                paper_dict["abstract"] = abstract
                paper_dict["abstract_source"] = "crossref"
            else:
                # Attempt to use Selenium
                print("No methods have extracted the abstract, trying Selenium")
                abstract_status, abstract = _get_abstract_w_selenium(doi_url)
                if abstract_status and abstract:
                    paper_dict["abstract"] = abstract[:650]
                    paper_dict["abstract_source"] = "selenium"
                else:
                    print("Abstract not found at all.")
                    paper_dict["abstract"] = ""
                    paper_dict["abstract_source"] = "na"

    return paper_dict


def obtain_and_save_abstract(
    biopapers_path: Path = BIOPAPERS_JSON_PATH,
    output_path_with_abstract: Path = BIOPAPERS_W_ABSTRACT_JSON_PATH,
    output_path_without_abstract: Path = BIOPAPERS_WOUT_ABSTRACT_JSON_PATH,
) -> dict:
    """
    Creates a loop through all papers and attempts to find an abstract. Uses
    multiprocessing to speed up the search process

    Parameters
    ----------
    biopapers_path: path
        Path to biopapers jsonl file
    output_path: path
        Output of biopapers jsonl file

    Returns
    -------
    results_stats: dict
        Dictionary {source_type: count}
    """
    # Create stats for results
    results_stats = {k: 0 for k in ["bioarxiv", "pubmed", "crossref", "selenium", "na"]}
    # Calculate last papers searched overall so they can be skipped
    try:
        with jsonlines.open(output_path_with_abstract, mode="r") as wab, jsonlines.open(
            output_path_without_abstract, mode="r"
        ) as woutab:
            last_checkpoint = len(list(wab)) + len(list(woutab))
    except:
        last_checkpoint = 0
    # Open output and input files:
    with jsonlines.open(biopapers_path) as reader, jsonlines.open(
        output_path_with_abstract, mode="a"
    ) as writer, jsonlines.open(output_path_without_abstract, mode="a") as writer2:

        # Create Muliprocessing Pool:
        pool = mp.Pool()
        # For each paper, extract abstract:
        # for paper_w_abstract_dict in pool.imap(get_abstract, reader):
        for paper_w_abstract_dict in pool.imap(
            get_abstract, itertools.islice(reader, last_checkpoint, None)
        ):
            if paper_w_abstract_dict["abstract_source"] == "na":
                writer2.write(paper_w_abstract_dict)
            else:
                writer.write(paper_w_abstract_dict)
            # Logging the source of the paper
            results_stats[paper_w_abstract_dict["abstract_source"]] += 1
            print(results_stats)
            del paper_w_abstract_dict

    print("Finished processing results")
    print(results_stats)
    return results_stats


if __name__ == "__main__":
    _ = obtain_and_save_abstract()
