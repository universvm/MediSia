import re
import multiprocessing as mp
from pathlib import Path

import jsonlines
import numpy as np

from config import PAPERS_JSON_FOLDER, BIOPAPERS_JSON_FOLDER, BIOJOURNALS_FILE

# Load Biojournals from text and normalize text:
biojournals = np.genfromtxt(BIOJOURNALS_FILE, delimiter='\n', dtype="str").tolist()
biojournals = [j.lower() for j in biojournals]
biojournals = [re.sub('\W+','', j) for j in biojournals]


def is_bio_journal(journal_dict):
    if journal_dict["journal_name"]:
        curr_journal = journal_dict["journal_name"].lower()
        curr_journal = re.sub('\W+','', curr_journal)
        if curr_journal in biojournals:
            return journal_dict
        else:
            return None


def select_and_save_biopapers(
    unpaywall_path: Path = PAPERS_JSON_FOLDER,
    output_path: Path = BIOPAPERS_JSON_FOLDER,
    biojournals_path: Path = BIOJOURNALS_FILE,
):
    """
    Loads unpaywall jsonlines, filters for biojournals and saves them to a file.

    Parameters
    ----------
    unpaywall_path: Path
        Path to unpaywall's JSONL file.
    output_path: Path
        Output path for JSONL file with biopaper only.
    biojournals_path: Path
        Path to .txt file containing all bio-papers journals in unpaywall.

    """
    biojournals_count = 0

    # Open JSONL Unpaywall file:
    with jsonlines.open(unpaywall_path) as reader, jsonlines.open(output_path, mode="a") as writer:
        # Create Muliprocessing Pool:
        pool = mp.Pool()
        # Open output:
        for ret in pool.imap(is_bio_journal, reader):
            if ret:
                writer.write(ret)
                biojournals_count += 1

    print(f'Found {biojournals_count} Biology-related journals.')


if __name__ == '__main__':
    select_and_save_biopapers()
