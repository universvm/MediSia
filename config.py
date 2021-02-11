import pathlib

PROJECT_ROOT_DIR = pathlib.Path(__file__).parent
DATA_FOLDER = PROJECT_ROOT_DIR / "data"
BIOJOURNALS_FILE = DATA_FOLDER / "journals" / "journals.txt"
PAPERS_FOLDER = DATA_FOLDER / "papers"
PAPERS_JSON_FOLDER = PAPERS_FOLDER / "papers.jsonl"
BIOPAPERS_JSON_PATH = PAPERS_FOLDER / "biopapers.jsonl"
BIOPAPERS_W_ABSTRACT_JSON_PATH = PAPERS_FOLDER / "biopapers_abstract.jsonl"
BIOPAPERS_WOUT_ABSTRACT_JSON_PATH = PAPERS_FOLDER / "biopapers_wout_abstract.jsonl"
TFIDF_VECTORIZER = DATA_FOLDER / "tfidf.pkl.bz2"
SEARCH_UTILS_FOLDER = DATA_FOLDER / "search_utils"
BOW_PATH = SEARCH_UTILS_FOLDER / "bow.pkl.bz2"
DEFAULT_DICT_SIZE = 100000