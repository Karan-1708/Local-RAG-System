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

def delete_document(source_name: str) -> bool:
    """
    Deletes all chunks associated with a specific source filename 
    from ChromaDB and the BM25 corpus.
    """
    try:
        embedding_function = get_embedding_function()
        db = Chroma(persist_directory=str(config.DB_DIR), embedding_function=embedding_function)
        
        # 1. Remove from ChromaDB
        # We find documents where the metadata 'source' matches the provided name
        # Note: 'source' in metadata often contains the full path
        results = db.get()
        ids_to_delete = []
        for i, metadata in enumerate(results['metadatas']):
            if source_name in metadata.get('source', ''):
                ids_to_delete.append(results['ids'][i])
        
        if ids_to_delete:
            db.delete(ids=ids_to_delete)
            logger.info(f"🗑️ Deleted {len(ids_to_delete)} chunks for '{source_name}' from ChromaDB.")
        
        # 2. Update BM25 Corpus
        bm25_path = config.DB_DIR / "bm25_corpus.pkl"
        if bm25_path.exists():
            with open(bm25_path, "rb") as f:
                corpus = pickle.load(f)
            
            new_corpus = [doc for doc in corpus if source_name not in doc.metadata.get('source', '')]
            
            with open(bm25_path, "wb") as f:
                pickle.dump(new_corpus, f)
            logger.info(f"✔ BM25 corpus updated (removed chunks for {source_name}).")

        # 3. Delete physical file
        file_path = config.DATA_DIR / source_name
        if file_path.exists():
            os.remove(file_path)
            logger.info(f"✔ File '{source_name}' deleted from storage.")

        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete document '{source_name}': {e}")
        return False

def save_to_chroma(chunks: List[Document]):
    """
    Saves a list of document chunks to the local ChromaDB and persists a BM25 corpus.
    Appends to existing data instead of resetting.
    """
    if not chunks:
        logger.warning("No chunks provided to save.")
        return

    try:
        # 1. Get embedding model
        embedding_function = get_embedding_function()
        
        # 2. Create/Update Chroma DB
        logger.info(f"Indexing {len(chunks)} chunks into ChromaDB at {config.DB_DIR}...")
        
        db = Chroma(
            persist_directory=str(config.DB_DIR), 
            embedding_function=embedding_function
        )
        db.add_documents(chunks)

        # 3. Update BM25 corpus (append)
        bm25_path = config.DB_DIR / "bm25_corpus.pkl"
        existing_corpus = []
        if bm25_path.exists():
            with open(bm25_path, "rb") as f:
                existing_corpus = pickle.load(f)
        
        full_corpus = existing_corpus + chunks
        
        logger.info(f"Updating BM25 corpus at {bm25_path}...")
        with open(bm25_path, "wb") as f:
            pickle.dump(full_corpus, f)
        
        logger.info(f"✔ Successfully added {len(chunks)} chunks to vector store and BM25 corpus.")

    except Exception as e:
        logger.error(f"❌ Critical Error saving to database: {e}")
        raise

