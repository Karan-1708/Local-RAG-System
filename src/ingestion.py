import os
import sys
import pytesseract
import logging
from typing import List, Dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from unstructured.partition.auto import partition
from src.utils import logger, get_safe_path
from src.privacy import redact_text
import config

# --- OCR Setup ---
# Set the Tesseract pointer once
pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD

def clean_text(text: str) -> str:
    """Basic text cleaning."""
    if not text:
        return ""
    return " ".join(text.split())

def process_single_file(file_path: Path) -> List[Dict]:
    """Processes a single file and returns a list of document objects."""
    filename = file_path.name
    try:
        logger.info(f"Processing: {filename}...")
        
        # We use partition with auto OCR if needed
        # It's better to wrap this in a try-except specifically for unstructured
        elements = partition(filename=str(file_path))
        
        full_text = "\n\n".join([str(el) for el in elements])
        cleaned_text = clean_text(full_text)
        
        if cleaned_text:
            logger.debug(f"Successfully extracted {len(elements)} elements from {filename}")
            
            # --- PII Redaction ---
            logger.debug(f"Applying PII scrubbing to {filename}...")
            redacted_text = redact_text(cleaned_text)
            
            return [{
                "text": redacted_text,
                "source": filename,
                "page": 1 
            }]
        else:
            logger.warning(f"No text extracted from {filename}")
            return []

    except Exception as e:
        logger.error(f"Failed to process {filename}: {str(e)}")
        return []

def load_documents(directory_path: str) -> List[Dict]:
    """Loads and processes documents from the specified directory in parallel."""
    documents = []
    dir_path = Path(directory_path)
    
    if not dir_path.exists():
        logger.error(f"Directory '{directory_path}' not found.")
        return []

    # Supported extensions
    valid_extensions = {
        ".pdf", ".docx", ".doc", ".odt", ".pptx", ".ppt", ".xlsx", ".csv",
        ".txt", ".html", ".htm", ".jpg", ".jpeg", ".png", ".bmp", ".tiff"
    }

    # Gather valid files
    files_to_process = [
        dir_path / f for f in os.listdir(dir_path) 
        if (dir_path / f).suffix.lower() in valid_extensions and (dir_path / f).is_file()
    ]

    if not files_to_process:
        logger.warning(f"No valid documents found in {directory_path}")
        return []

    logger.info(f"Scanning {len(files_to_process)} documents in parallel...")

    # Parallel processing using ThreadPoolExecutor
    # Max workers can be adjusted based on CPU/Memory
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        future_to_file = {executor.submit(process_single_file, f): f for f in files_to_process}
        
        for future in as_completed(future_to_file):
            res = future.result()
            if res:
                documents.extend(res)

    logger.info(f"Successfully loaded {len(documents)} document objects.")
    return documents

if __name__ == "__main__":
    # Test block
    import config
    docs = load_documents(str(config.DATA_DIR))
    if docs:
        print(f"\nTotal: {len(docs)}")
        print(f"Sample: {docs[0]['source']} - {docs[0]['text'][:100]}...")
