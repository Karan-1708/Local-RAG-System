import os
import pickle
from typing import List
from langchain_chroma import Chroma
from langchain_core.documents import Document
from src.embeddings import get_embedding_function
from src.utils import logger, clear_directory
import config

def reset_database() -> bool:
    """
    Clears all documents from the local Chroma vector store, BM25 corpus, 
    and deletes all raw uploaded files.
    """
    try:
        embedding_function = get_embedding_function()
        
        # 1. Clear ChromaDB
        # Check if DB directory exists and is not empty
        if config.DB_DIR.exists() and any(config.DB_DIR.iterdir()):
            # Connect to DB
            db = Chroma(
                persist_directory=str(config.DB_DIR), 
                embedding_function=embedding_function
            )
            
            # Get all IDs
            existing_data = db.get()
            existing_ids = existing_data.get('ids', [])
            
            if existing_ids:
                logger.info(f"🗑️ Deleting {len(existing_ids)} existing documents from Vector DB...")
                db.delete(ids=existing_ids)
                logger.info("✔ ChromaDB cleared successfully.")
        else:
            logger.info("✔ Vector DB was already empty or non-existent.")

        # 2. Clear BM25 Corpus
        bm25_path = config.DB_DIR / "bm25_corpus.pkl"
        if bm25_path.exists():
            logger.info("🗑️ Deleting BM25 corpus file...")
            os.remove(bm25_path)
            logger.info("✔ BM25 corpus cleared.")
            
        # 3. Securely Clear Raw Data Files
        if not clear_directory(config.DATA_DIR):
            logger.warning("Failed to clear raw data directory. Check permissions.")
            
        return True

    except Exception as e:
        logger.error(f"❌ Error during full reset: {e}")
        return False

def save_to_chroma(chunks: List[Document]):
    """
    Saves a list of document chunks to the local ChromaDB and persists a BM25 corpus.
    Resets the database before saving.
    """
    if not chunks:
        logger.warning("No chunks provided to save.")
        return

    # 1. Clear existing data
    if not reset_database():
        logger.warning("Proceeding with save despite potential reset failure.")

    try:
        # 2. Get embedding model
        embedding_function = get_embedding_function()
        
        # 3. Create/Update Chroma DB
        logger.info(f"Indexing {len(chunks)} chunks into ChromaDB at {config.DB_DIR}...")
        
        Chroma.from_documents(
            documents=chunks, 
            embedding=embedding_function, 
            persist_directory=str(config.DB_DIR)
        )

        # 4. Save chunks for BM25 retrieval
        bm25_path = config.DB_DIR / "bm25_corpus.pkl"
        logger.info(f"Saving BM25 corpus to {bm25_path}...")
        with open(bm25_path, "wb") as f:
            pickle.dump(chunks, f)
        
        logger.info(f"✔ Successfully saved {len(chunks)} chunks to vector store and BM25 corpus.")

    except Exception as e:
        logger.error(f"❌ Critical Error saving to database: {e}")
        raise
