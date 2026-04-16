import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "raw"
DB_DIR = BASE_DIR / "chroma_db"

# Tesseract OCR path
TESSERACT_CMD = os.getenv("TESSERACT_CMD", r"H:\AI_Apps\TesseractOCR\tesseract.exe")

# Models
# Options: "llama3:8b", "phi3:mini", "mistral"
LLM_MODEL = os.getenv("LLM_MODEL", "llama3:8b") 
# Options: "all-MiniLM-L6-v2", "nomic-embed-text"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# --- Security ---
# Internal key to protect FastAPI endpoints
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
if not INTERNAL_API_KEY:
    _argv_str = " ".join(sys.argv)
    _is_setup = any(s in _argv_str for s in ["install.py", "spacy", "pytest"])
    if not _is_setup:
        raise ValueError(
            "CRITICAL SECURITY ERROR: INTERNAL_API_KEY is not set in the .env file. "
            "The application cannot start in an insecure state."
        )
    INTERNAL_API_KEY = "setup_mode_placeholder"

# RAG Parameters
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1000))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))
RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", 5))

# Evaluation
# Threshold for ambiguous queries (if similarity score < threshold, treat as ambiguous)
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.6))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "local_rag.log")

# Ensure critical directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)
