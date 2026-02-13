import os
import time
from typing import List
from langchain_chroma import Chroma
from langchain_core.documents import Document
from src.embeddings import get_embedding_function

CHROMA_PATH = "chroma_db"

def reset_database():
    """
    Resets the database by deleting the DATA, not the FOLDER.
    This avoids Windows file lock errors.
    """
    embedding_function = get_embedding_function()
    
    if os.path.exists(CHROMA_PATH):
        try:
            # Connect to the existing DB
            db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
            
            # Get all document IDs
            existing_data = db.get()
            existing_ids = existing_data['ids']
            
            if existing_ids:
                print(f"🗑️ Deleting {len(existing_ids)} existing documents from DB...")
                # Delete the specific entries
                db.delete(ids=existing_ids)
                print("✔ Database cleared successfully (Soft Reset).")
            else:
                print("✔ Database was already empty.")
                
            return True
        except Exception as e:
            print(f"❌ Error clearing database: {e}")
            return False
    return True

def save_to_chroma(chunks: List[Document]):
    """
    Saves a list of document chunks to the local ChromaDB.
    """
    # 1. Clear out old data (Soft Reset)
    reset_database()

    # 2. Load the embedding model
    embedding_function = get_embedding_function()
    
    # 3. Create the database from chunks
    print(f"Saving {len(chunks)} chunks to ChromaDB...")
    
    try:
        # We don't need a loop anymore because we aren't fighting file locks
        db = Chroma.from_documents(
            documents=chunks, 
            embedding=embedding_function, 
            persist_directory=CHROMA_PATH
        )
        print(f"✔ Saved! Database contains {len(chunks)} chunks.")
    except Exception as e:
        print(f"❌ Error saving to DB: {e}")