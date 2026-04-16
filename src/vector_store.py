import os
import pickle
import shutil
from typing import List
from langchain_chroma import Chroma
from langchain_core.documents import Document
from src.embeddings import get_embedding_function
from src.utils import logger, clear_directory
import config


def _collection_name(chat_id: str) -> str:
    """Returns a ChromaDB-safe collection name for a chat ID.
    ChromaDB requires: starts with letter, 3-63 chars, alphanumeric/hyphen/underscore only.
    """
    return f"chat_{chat_id.replace('-', '_')}"


def _bm25_path(chat_id: str):
    return config.DB_DIR / f"bm25_{chat_id.replace('-', '_')}.pkl"


def save_to_chroma(chunks: List[Document], chat_id: str):
    """
    Saves chunks to a chat-specific ChromaDB collection and BM25 corpus.
    Appends to existing data — does not overwrite.
    """
    if not chunks:
        logger.warning("No chunks provided to save.")
        return

    try:
        embedding_function = get_embedding_function()
        collection = _collection_name(chat_id)

        logger.info(f"Indexing {len(chunks)} chunks into collection '{collection}'...")
        db = Chroma(
            persist_directory=str(config.DB_DIR),
            embedding_function=embedding_function,
            collection_name=collection
        )
        db.add_documents(chunks)

        # Update chat-specific BM25 corpus
        bm25 = _bm25_path(chat_id)
        existing_corpus = []
        if bm25.exists():
            try:
                with open(bm25, "rb") as f:
                    existing_corpus = pickle.load(f)
            except (pickle.UnpicklingError, EOFError) as e:
                logger.warning(f"BM25 corpus corrupt, rebuilding from scratch: {e}")

        with open(bm25, "wb") as f:
            pickle.dump(existing_corpus + chunks, f)

        logger.info(f"✔ Added {len(chunks)} chunks to chat {chat_id[:8]}.")

    except Exception as e:
        logger.error(f"❌ Critical error saving to database: {e}")
        raise


def delete_document(source_name: str, chat_id: str) -> bool:
    """
    Deletes all chunks for a specific file from a chat's ChromaDB collection,
    BM25 corpus, and the physical file on disk.
    """
    try:
        embedding_function = get_embedding_function()
        db = Chroma(
            persist_directory=str(config.DB_DIR),
            embedding_function=embedding_function,
            collection_name=_collection_name(chat_id)
        )

        # 1. Remove from ChromaDB
        results = db.get()
        ids_to_delete = [
            results['ids'][i]
            for i, meta in enumerate(results['metadatas'])
            if source_name in meta.get('source', '')
        ]
        if ids_to_delete:
            db.delete(ids=ids_to_delete)
            logger.info(f"🗑️ Deleted {len(ids_to_delete)} chunks for '{source_name}'.")

        # 2. Update BM25 corpus
        bm25 = _bm25_path(chat_id)
        if bm25.exists():
            try:
                with open(bm25, "rb") as f:
                    corpus = pickle.load(f)
                new_corpus = [doc for doc in corpus if source_name not in doc.metadata.get('source', '')]
                with open(bm25, "wb") as f:
                    pickle.dump(new_corpus, f)
                logger.info(f"✔ BM25 corpus updated for chat {chat_id[:8]}.")
            except (pickle.UnpicklingError, EOFError) as e:
                logger.warning(f"BM25 corpus corrupt, removing it: {e}")
                bm25.unlink()

        # 3. Delete physical file from chat's data directory
        file_path = config.DATA_DIR / chat_id / source_name
        if file_path.exists():
            file_path.unlink()
            logger.info(f"✔ File '{source_name}' deleted from chat {chat_id[:8]} storage.")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to delete '{source_name}': {e}")
        return False


def delete_chat_data(chat_id: str) -> bool:
    """
    Removes all data associated with a chat: ChromaDB collection, BM25 corpus,
    and the uploaded files directory. Called when a chat is deleted from the UI.
    """
    try:
        embedding_function = get_embedding_function()

        # 1. Delete ChromaDB collection via the client API to avoid
        #    Windows file-lock errors on chroma.sqlite3.
        collection = _collection_name(chat_id)
        try:
            import chromadb
            if config.DB_DIR.exists():
                client = chromadb.PersistentClient(path=str(config.DB_DIR))
                existing = [c.name for c in client.list_collections()]
                if collection in existing:
                    client.delete_collection(collection)
                    logger.info(f"🗑️ Deleted ChromaDB collection '{collection}'.")
        except Exception as e:
            logger.warning(f"Could not delete collection '{collection}': {e}")

        # 2. Delete BM25 corpus
        bm25 = _bm25_path(chat_id)
        if bm25.exists():
            bm25.unlink()
            logger.info(f"🗑️ Deleted BM25 corpus for chat {chat_id[:8]}.")

        # 3. Delete uploaded files directory
        chat_data_dir = config.DATA_DIR / chat_id
        if chat_data_dir.exists():
            shutil.rmtree(chat_data_dir)
            logger.info(f"🗑️ Deleted data directory for chat {chat_id[:8]}.")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to delete chat data for {chat_id}: {e}")
        return False


def reset_database() -> bool:
    """
    Full system reset: wipes all ChromaDB collections, all BM25 corpora,
    and all uploaded files across every chat.

    Uses the chromadb client API to delete collections instead of
    shutil.rmtree so that the SQLite file lock held by cached Chroma
    connections (e.g. @st.cache_resource embedding function) is respected
    on Windows.
    """
    try:
        # 1. Delete all collections via ChromaDB's own client API.
        #    This works even while other connections hold the SQLite file open.
        import chromadb
        if config.DB_DIR.exists():
            client = chromadb.PersistentClient(path=str(config.DB_DIR))
            for col in client.list_collections():
                client.delete_collection(col.name)
                logger.info(f"🗑️ Deleted ChromaDB collection '{col.name}'.")
            logger.info("✔ All ChromaDB collections removed.")

        # 2. Delete all BM25 pickle files
        for pkl in config.DB_DIR.glob("bm25_*.pkl"):
            pkl.unlink()
            logger.info(f"🗑️ Deleted BM25 corpus: {pkl.name}")

        # 3. Clear all uploaded files (all chat subdirectories)
        if not clear_directory(config.DATA_DIR):
            logger.warning("Failed to clear raw data directory. Check permissions.")

        return True

    except Exception as e:
        logger.error(f"❌ Error during full reset: {e}")
        return False
