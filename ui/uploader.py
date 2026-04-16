import streamlit as st
from pathlib import Path

from ui.state import ALLOWED_EXTENSIONS
from src.ingestion import load_documents
from src.chunks import split_documents
from src.vector_store import save_to_chroma
from src.utils import logger, get_safe_path, ensure_directory
import config


def render_uploader():
    """Renders the file upload widget and handles ingestion into the chat's vector store."""
    uploaded_files = st.file_uploader(
        "📎 Drag & Drop Documents (PDF, DOCX, TXT, CSV, MD, PNG, JPG)",
        accept_multiple_files=True
    )

    if not uploaded_files:
        return

    invalid = [f.name for f in uploaded_files if Path(f.name).suffix.lower() not in ALLOWED_EXTENSIONS]
    if invalid:
        st.error(f"🚨 Unsupported formats: {', '.join(invalid)}")
        return

    # Each chat stores its files in its own subdirectory: data/raw/<chat_id>/
    chat_id = st.session_state.active_chat_id
    chat_data_dir = config.DATA_DIR / chat_id

    with st.status("🚀 Processing Knowledge Base...", expanded=True) as status:
        try:
            ensure_directory(chat_data_dir)

            for f in uploaded_files:
                safe_path = get_safe_path(chat_data_dir, f.name)
                with open(safe_path, "wb") as file:
                    file.write(f.getbuffer())

            docs = load_documents(str(chat_data_dir))
            if not docs:
                status.update(label="⚠️ No text could be extracted from the uploaded files.", state="error")
                return

            chunks = split_documents(docs)
            save_to_chroma(chunks, chat_id)
            status.update(label=f"✅ Knowledge Base Updated ({len(chunks)} chunks)", state="complete")

        except ValueError as e:
            status.update(label=f"🚨 Security Error: {e}", state="error")
            logger.error(f"Path traversal attempt blocked: {e}")
        except Exception as e:
            status.update(label=f"❌ Processing failed: {e}", state="error")
            logger.error(f"Document processing error: {e}")
