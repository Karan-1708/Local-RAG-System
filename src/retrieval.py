import pickle
from typing import Optional
from langchain_community.retrievers import BM25Retriever
from src.utils import logger
import config


def get_bm25_retriever(chat_id: str, k: int = 10) -> Optional[BM25Retriever]:
    """
    Initializes and returns a BM25Retriever using the persisted corpus for a
    specific chat. Returns None if no corpus exists for that chat yet.
    """
    bm25_path = config.DB_DIR / f"bm25_{chat_id.replace('-', '_')}.pkl"

    if not bm25_path.exists():
        logger.info(f"No BM25 corpus for chat {chat_id[:8]}. Keyword retrieval skipped.")
        return None

    try:
        with open(bm25_path, "rb") as f:
            chunks = pickle.load(f)

        if not chunks:
            logger.warning(f"BM25 corpus for chat {chat_id[:8]} is empty.")
            return None

        retriever = BM25Retriever.from_documents(chunks)
        retriever.k = k
        logger.info(f"BM25 retriever ready for chat {chat_id[:8]} ({len(chunks)} docs, k={k}).")
        return retriever

    except Exception as e:
        logger.error(f"❌ Failed to load BM25 retriever for chat {chat_id[:8]}: {e}")
        return None
