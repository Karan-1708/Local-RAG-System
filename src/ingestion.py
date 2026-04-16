import os
import pytesseract
from typing import List, Dict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.utils import logger
from src.privacy import redact_text
import config

# Set the Tesseract pointer once
pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD

# ── Per-format extractors ─────────────────────────────────────────────────────

def _extract_pdf(file_path: Path) -> List[Dict]:
    """
    Extract text from a PDF using pdfminer.six page-by-page.
    Falls back to pdf2image + Tesseract OCR for image-based (scanned) pages.
    """
    from pdfminer.high_level import extract_pages
    from pdfminer.layout import LTTextContainer

    docs = []
    try:
        for page_num, page_layout in enumerate(extract_pages(str(file_path)), start=1):
            page_text = "".join(
                el.get_text() for el in page_layout if isinstance(el, LTTextContainer)
            )
            if page_text.strip():
                docs.append({"text": page_text, "source": file_path.name, "page": page_num})
    except Exception as e:
        logger.warning(f"pdfminer failed on {file_path.name}: {e} — falling back to OCR")

    if docs:
        return docs

    # Fallback: render each page as an image and OCR it
    return _ocr_pdf(file_path)


def _ocr_pdf(file_path: Path) -> List[Dict]:
    """OCR fallback for image-based / scanned PDFs."""
    try:
        from pdf2image import convert_from_path
        from PIL import Image
        docs = []
        images = convert_from_path(str(file_path))
        for page_num, img in enumerate(images, start=1):
            text = pytesseract.image_to_string(img)
            if text.strip():
                docs.append({"text": text, "source": file_path.name, "page": page_num})
        return docs
    except Exception as e:
        logger.error(f"OCR fallback failed for {file_path.name}: {e}")
        return []


def _extract_docx(file_path: Path) -> List[Dict]:
    """Extract text from .docx using python-docx."""
    try:
        import docx
        doc = docx.Document(str(file_path))
        text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        return [{"text": text, "source": file_path.name, "page": 1}] if text else []
    except Exception as e:
        logger.error(f"DOCX extraction failed for {file_path.name}: {e}")
        return []


def _extract_spreadsheet(file_path: Path) -> List[Dict]:
    """Extract text from .csv and .xlsx using pandas."""
    try:
        import pandas as pd
        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        text = df.to_string(index=False)
        return [{"text": text, "source": file_path.name, "page": 1}] if text.strip() else []
    except Exception as e:
        logger.error(f"Spreadsheet extraction failed for {file_path.name}: {e}")
        return []


def _extract_image(file_path: Path) -> List[Dict]:
    """OCR an image file directly with Tesseract."""
    try:
        from PIL import Image
        text = pytesseract.image_to_string(Image.open(file_path))
        return [{"text": text, "source": file_path.name, "page": 1}] if text.strip() else []
    except Exception as e:
        logger.error(f"Image OCR failed for {file_path.name}: {e}")
        return []


def _extract_text(file_path: Path) -> List[Dict]:
    """Read plain-text formats (txt, md, html)."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        return [{"text": text, "source": file_path.name, "page": 1}] if text.strip() else []
    except Exception as e:
        logger.error(f"Text extraction failed for {file_path.name}: {e}")
        return []


# ── Dispatcher ────────────────────────────────────────────────────────────────

_EXTRACTORS = {
    ".pdf":  _extract_pdf,
    ".docx": _extract_docx,
    ".doc":  _extract_docx,
    ".xlsx": _extract_spreadsheet,
    ".csv":  _extract_spreadsheet,
    ".txt":  _extract_text,
    ".md":   _extract_text,
    ".html": _extract_text,
    ".htm":  _extract_text,
    ".jpg":  _extract_image,
    ".jpeg": _extract_image,
    ".png":  _extract_image,
    ".bmp":  _extract_image,
    ".tiff": _extract_image,
}


def clean_text(text: str) -> str:
    return " ".join(text.split()) if text else ""


def process_single_file(file_path: Path) -> List[Dict]:
    """Processes a single file and returns a list of document dicts."""
    filename = file_path.name
    ext = file_path.suffix.lower()

    extractor = _EXTRACTORS.get(ext)
    if not extractor:
        logger.warning(f"Unsupported file type: {filename}")
        return []

    try:
        logger.info(f"Processing: {filename}...")
        raw_docs = extractor(file_path)

        results = []
        for doc in raw_docs:
            cleaned = clean_text(doc["text"])
            if not cleaned:
                continue
            redacted = redact_text(cleaned)
            results.append({"text": redacted, "source": doc["source"], "page": doc["page"]})

        if results:
            logger.debug(f"Extracted {len(results)} page(s) from {filename}")
        else:
            logger.warning(f"No text extracted from {filename}")

        return results

    except Exception as e:
        logger.error(f"Failed to process {filename}: {e}")
        return []


def load_documents(directory_path: str) -> List[Dict]:
    """Loads and processes all supported documents in parallel."""
    dir_path = Path(directory_path)
    if not dir_path.exists():
        logger.error(f"Directory '{directory_path}' not found.")
        return []

    files_to_process = [
        dir_path / f for f in os.listdir(dir_path)
        if (dir_path / f).is_file() and (dir_path / f).suffix.lower() in _EXTRACTORS
    ]

    if not files_to_process:
        logger.warning(f"No supported documents found in {directory_path}")
        return []

    logger.info(f"Processing {len(files_to_process)} document(s) in parallel...")

    documents = []
    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = {executor.submit(process_single_file, f): f for f in files_to_process}
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    documents.extend(result)
            except Exception as e:
                logger.error(f"Worker thread failed for {futures[future].name}: {e}")

    logger.info(f"Successfully loaded {len(documents)} document chunk(s).")
    return documents


if __name__ == "__main__":
    docs = load_documents(str(config.DATA_DIR))
    if docs:
        print(f"\nTotal chunks: {len(docs)}")
        print(f"Sample: {docs[0]['source']} p{docs[0]['page']} — {docs[0]['text'][:100]}...")
