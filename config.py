import pathlib

PROJECT_ROOT_DIR = pathlib.Path(__file__).parent
DATA_FOLDER = PROJECT_ROOT_DIR / "data"
BIOJOURNALS_FILE = DATA_FOLDER / "journals" / "journals.txt"
PAPERS_FOLDER = DATA_FOLDER / "papers"
PAPERS_JSON_FOLDER = PAPERS_FOLDER / "papers.jsonl"
BIOPAPERS_JSON_FOLDER = PAPERS_FOLDER / "biopapers.jsonl"
