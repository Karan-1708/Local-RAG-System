from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from src.utils import logger
import config

def split_documents(documents: List[Dict], chunk_size: int = None, chunk_overlap: int = None) -> List[Document]:
    """
    Splits a list of raw document dictionaries into smaller chunks.
    Uses values from config if not provided.
    """
    size = chunk_size or config.CHUNK_SIZE
    overlap = chunk_overlap or config.CHUNK_OVERLAP
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        length_function=len,
        is_separator_regex=False,
    )
    
    chunked_docs = []
    
    logger.info(f"Splitting {len(documents)} raw documents with size={size}, overlap={overlap}...")
    
    for doc in documents:
        try:
            raw_text = doc["text"]
            metadata = {
                "source": doc["source"], 
                "page": doc.get("page", 1)
            }
            
            # Create Document objects
            chunks = text_splitter.create_documents([raw_text], metadatas=[metadata])
            chunked_docs.extend(chunks)
        except Exception as e:
            logger.error(f"Failed to split document {doc.get('source', 'Unknown')}: {e}")
        
    logger.info(f"✔ Created {len(chunked_docs)} chunks.")
    return chunked_docs
