import subprocess
import sys
from src.utils import logger

def setup_spacy_model():
    """
    Downloads the required spaCy model for Microsoft Presidio.
    """
    model_name = "en_core_web_sm"
    logger.info(f"Downloading spaCy model: {model_name}...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "spacy", "download", model_name])
        logger.info(f"✔ Successfully downloaded and installed {model_name}.")
    except Exception as e:
        logger.error(f"❌ Failed to download spaCy model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_spacy_model()
