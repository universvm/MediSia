import pathlib
import os
import re
import string
from gensim.parsing.preprocessing import STOPWORDS

PROJECT_ROOT_DIR = pathlib.Path(__file__).parent
DATA_FOLDER = PROJECT_ROOT_DIR / "data"
BIOJOURNALS_FILE = DATA_FOLDER / "journals" / "journals.txt"
BIOJOURNALS_CATEGORIES_FILE = DATA_FOLDER / "journals" / "journals_categories.txt"
PAPERS_FOLDER = DATA_FOLDER / "papers"
PAPERS_JSON_FOLDER = PAPERS_FOLDER / "papers.jsonl"
BIOPAPERS_JSON_PATH = PAPERS_FOLDER / "biopapers.jsonl"
BIOPAPERS_W_ABSTRACT_JSON_PATH = PAPERS_FOLDER / "biopapers_abstract.jsonl"
BIOPAPERS_WOUT_ABSTRACT_JSON_PATH = PAPERS_FOLDER / "biopapers_wout_abstract.jsonl"
SEARCH_UTILS_FOLDER = DATA_FOLDER / "search_utils"
SEARCH_UTILS_FOLDER.mkdir(parents=True, exist_ok=True)
TFIDF_VECTORIZER = SEARCH_UTILS_FOLDER / "tfidf.pkl.bz2"
BOW_PATH = SEARCH_UTILS_FOLDER / "bow.pkl.bz2"
INDECES_FOLDER = DATA_FOLDER / "indeces"
INDECES_FOLDER.mkdir(parents=True, exist_ok=True)
BOW_LENGTH = 300000
# Cleaning regex:
punctuation = re.compile(r'([%s])+' % re.escape(string.punctuation), re.UNICODE)
html_tags = re.compile(r"<([^>]+)>", re.UNICODE)
numbers = re.compile(r"[0-9]+", re.UNICODE)
non_letters = re.compile(r"\W", re.UNICODE)
alpha_num = re.compile(r"([a-z]+)([0-9]+)", flags=re.UNICODE)
num_alpha = re.compile(r"([0-9]+)([a-z]+)", flags=re.UNICODE)
spaces = re.compile(r"(\s)+", re.UNICODE)
# Stop words:
MEDICAL_STOPWORDS = set(["disease", "diseases", "disorder", "symptom", "symptoms", "drug", "drugs", "problems", "problem", "prob", "probs", "med", "meds", "pill", "pills", "medicine", "medicines", "medication", "medications", "treatment", "treatments", "caps", "capsules", "capsule", "tablet", "tablets", "tabs", "doctor", "dr", "dr.", "doc", "physician", "physicians", "test", "tests", "testing", "specialist", "specialists", "side-effect", "side-effects", "pharmaceutical", "pharmaceuticals", "pharma", "diagnosis", "diagnose", "diagnosed", "exam", "challenge", "device", "condition", "conditions", "suffer", "suffering suffered", "feel", "feeling", "prescription", "prescribe", "prescribed", "over-the-counter", "otc"])
# from https://cs.stanford.edu/people/sonal/gupta14jamia_supl.pdf
MEDICAL_STOPWORDS2 = set(["a", "about", "again", "all", "almost", "also", "although", "always", "among", "an", "and", "another", "any", "are", "as", "at", "be", "because", "been", "before", "being", "between", "both", "but", "by", "can", "could", "did", "do", "does", "done", "due", "during", "each", "either", "enough", "especially", "etc", "for", "found", "from", "further", "had", "has", "have", "having", "here", "how", "however", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "kg", "km", "made", "mainly", "make", "may", "mg", "might", "ml", "mm", "most", "mostly", "must", "nearly", "neither", "no", "nor", "obtained", "of", "often", "on", "our", "overall", "perhaps", "pmid", "quite", "rather", "really", "regarding", "seem", "seen", "several", "should", "show", "showed", "shown", "shows", "significantly", "since", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "then", "there", "therefore", "these", "they", "this", "those", "through", "thus", "to", "upon", "various", "very", "was", "we", "were", "what", "when", "which", "while", "with", "within", "without", "would"])
# from https://pubmed.ncbi.nlm.nih.gov/help/#help-stopwords
GENERAL_STOPWORDS = set(STOPWORDS)
OTHER_STOPWORDS = set(["copyright", "facebook", "twitter", "email", "journal", "review", "volume", "date", "none", "pdf"])
DEFAULT_STOPWORDS = MEDICAL_STOPWORDS | GENERAL_STOPWORDS | MEDICAL_STOPWORDS2 | OTHER_STOPWORDS
