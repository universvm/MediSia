from pathlib import Path

import jsonlines
import numpy as np

from config import PAPERS_JSON_FOLDER, BIOPAPERS_JSON_FOLDER, BIOJOURNALS_FILE


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
    biojournals = np.genfromtxt(biojournals_path, delimiter='\n', fmt="%s")
    biojournals_count = 0
    # Open JSONL Unpaywall file:
    with jsonlines.open(unpaywall_path) as reader:
        # Check if output file already exists:
        if output_path.exists():
            raise ValueError(f"ATTENTION: outfile {output_path} already exists. Please rename it.")
        # If outfile does not exist
        else:
            # Open output:
            with jsonlines.open(output_path, mode="a") as writer:
                for obj in reader:
                    if obj["journal_name"] in biojournals:
                        writer.write(obj)
                        biojournals_count += 1

    print(f'Found {biojournals_count} Biology-related journals.')
