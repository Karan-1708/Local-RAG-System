import os
import streamlit as st
from langchain_huggingface import HuggingFaceEmbeddings
from src.utils import logger, get_device
import config

@st.cache_resource
def get_embedding_function() -> HuggingFaceEmbeddings:
    """
    Returns the HuggingFace embedding model.
    Cached for performance using Streamlit.
    """
    # Force offline mode if needed (set HF_HUB_OFFLINE=1 in .env)
    is_offline = os.getenv("HF_HUB_OFFLINE", "0") == "1"
    device = get_device()
    
    try:
        logger.debug(f"Loading embedding model: {config.EMBEDDING_MODEL} (Device: {device}, Offline: {is_offline})...")
        
        embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL,
            model_kwargs={'device': device}, 
            encode_kwargs={'normalize_embeddings': True}
        )
        
        return embeddings
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        if not is_offline:
            logger.info("Attempting to load model again... connection might be slow.")
        raise
