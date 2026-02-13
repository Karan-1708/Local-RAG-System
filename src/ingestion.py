import os
import sys

# --- CRITICAL FIX: FORCE TESSERACT INTO PATH ---
# We define the folder path (without 'tesseract.exe')
tesseract_folder = r'H:\AI_Apps\TesseractOCR'

# We check if the executable actually exists there (sanity check)
tesseract_exe = os.path.join(tesseract_folder, 'tesseract.exe')
if not os.path.exists(tesseract_exe):
    print(f"CRITICAL ERROR: Could not find Tesseract at: {tesseract_exe}")
    print("Please check if the folder name or drive letter is correct.")
    sys.exit(1)

# We add this folder to the system PATH for this script's execution only
if tesseract_folder not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + tesseract_folder

# Now we import the heavy libraries
import pytesseract
from typing import List, Dict
from unstructured.partition.auto import partition

# We also set the direct pointer for good measure
pytesseract.pytesseract.tesseract_cmd = tesseract_exe

def clean_text(text: str) -> str:
    """Basic text cleaning."""
    return " ".join(text.split())

def load_documents(directory_path: str) -> List[Dict]:
    documents = []
    
    if not os.path.exists(directory_path):
        print(f"Error: Directory '{directory_path}' not found.")
        return []

    print(f"Scanning directory: {directory_path}...")
    
    # Supported extensions
    valid_extensions = {
        ".pdf", ".docx", ".doc", ".odt", ".pptx", ".ppt", ".xlsx", ".csv",
        ".txt", ".html", ".htm", ".jpg", ".jpeg", ".png", ".bmp", ".tiff"
    }

    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        ext = os.path.splitext(filename)[1].lower()

        if ext not in valid_extensions:
            continue

        try:
            print(f"Processing: {filename}...", end=" ", flush=True)
            
            # The magic function
            elements = partition(filename=file_path)
            
            full_text = "\n\n".join([str(el) for el in elements])
            cleaned_text = clean_text(full_text)
            
            if cleaned_text:
                documents.append({
                    "text": cleaned_text,
                    "source": filename,
                    "page": 1 
                })
                print(f"Success ({len(elements)} elements found)")
            else:
                print(f"Warning: No text found in {filename}")

        except Exception as e:
            print(f"\nFAILED to process {filename}")
            # print(f"Error: {str(e)}") # Uncomment to see full ugly error

    print(f"\nTotal documents successfully loaded: {len(documents)}")
    return documents

if __name__ == "__main__":
    test_data_dir = os.path.join(os.getcwd(), "data", "raw")
    if not os.path.exists(test_data_dir):
        os.makedirs(test_data_dir)
    
    docs = load_documents(test_data_dir)
    
    if docs:
        print("\n--- Sample Output ---")
        print(f"Source: {docs[0]['source']}")
        print(f"Text Snippet: {docs[0]['text'][:200]}...")