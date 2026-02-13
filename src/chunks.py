from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document  # Updated for modern LangChain

def split_documents(documents: List[Dict], chunk_size: int = 1000, chunk_overlap: int = 300) -> List[Document]:
    """
    Splits a list of raw document dictionaries into smaller chunks.
    """
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    
    chunked_docs = []
    
    print(f"Splitting {len(documents)} raw documents...")
    
    for doc in documents:
        raw_text = doc["text"]
        metadata = {"source": doc["source"], "page": doc.get("page", 1)}
        
        # Create Document objects
        chunks = text_splitter.create_documents([raw_text], metadatas=[metadata])
        chunked_docs.extend(chunks)
        
    print(f"✔ Created {len(chunked_docs)} chunks.")
    return chunked_docs

# --- Test Block ---
if __name__ == "__main__":
    import os
    # We must use the module path since we are running with -m
    from src.ingestion import load_documents 
    
    # 1. Load Data
    data_dir = os.path.join(os.getcwd(), "data", "raw")
    raw_docs = load_documents(data_dir)
    
    # 2. Split Data
    if raw_docs:
        final_chunks = split_documents(raw_docs)
        
        # 3. Show a sample
        if final_chunks:
            print("\n--- Sample Chunk ---")
            print(f"Content: {final_chunks[0].page_content[:200]}...")
            print(f"Metadata: {final_chunks[0].metadata}")