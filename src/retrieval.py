import pickle
import logging
from typing import Optional
from langchain_community.retrievers import BM25Retriever
from src.utils import logger
import config

def get_bm25_retriever(k: int = 10) -> Optional[BM25Retriever]:
    """
    Initializes and returns a LangChain BM25Retriever using the persisted corpus.
    Returns None if the corpus file does not exist.
    """
    bm25_path = config.DB_DIR / "bm25_corpus.pkl"
    
    if not bm25_path.exists():
        logger.info("BM25 corpus not found. Keyword retrieval will be skipped.")
        return None

    try:
        logger.info(f"Loading BM25 corpus from {bm25_path}...")
        with open(bm25_path, "rb") as f:
            chunks = pickle.load(f)
        
        if not chunks:
            logger.warning("BM25 corpus is empty.")
            return None

        logger.info(f"Initializing BM25Retriever with {len(chunks)} documents (k={k})...")
        retriever = BM25Retriever.from_documents(chunks)
        retriever.k = k
        
        return retriever

    except Exception as e:
        logger.error(f"❌ Failed to initialize BM25Retriever: {e}")
        return None
