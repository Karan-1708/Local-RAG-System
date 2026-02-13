import os

# Paths
DATA_DIR = os.path.join(os.getcwd(), "data", "raw")
DB_DIR = os.path.join(os.getcwd(), "chroma_db")

# Models
# Options: "llama3:8b", "phi3:mini", "mistral"
LLM_MODEL = "llama3:8b" 
# Options: "all-MiniLM-L6-v2", "nomic-embed-text"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# RAG Parameters
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVAL_K = 5  # Number of chunks to retrieve

# Evaluation
# Threshold for ambiguous queries (if similarity score < threshold, treat as ambiguous)
SIMILARITY_THRESHOLD = 0.6