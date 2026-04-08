import logging
import os
import sys
from pathlib import Path
from typing import Optional

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = "app.log") -> logging.Logger:
    """Sets up a structured logger for the entire application."""
    logger = logging.getLogger("LocalRAG")
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (Optional)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to set up file logging: {e}")

    return logger

def get_safe_path(base_dir: Path, filename: str) -> Path:
    """Returns a safe path joined with filename, preventing traversal attacks."""
    # Ensure filename is just a name, not a path
    safe_filename = Path(filename).name
    target_path = (base_dir / safe_filename).resolve()
    
    # Ensure the resolved path is still under the base directory
    if not str(target_path).startswith(str(base_dir.resolve())):
        raise ValueError(f"Security Warning: Attempted path traversal to {target_path}")
    
    return target_path

def ensure_directory(path: Path) -> Path:
    """Ensures a directory exists, creating it if necessary."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except Exception as e:
        logger = logging.getLogger("LocalRAG")
        logger.error(f"Failed to create directory {path}: {e}")
        raise

def get_device() -> str:
    """Detects the best available hardware device (cuda, mps, or cpu)."""
    import torch
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"

def get_hardware_info() -> str:
    """Returns a descriptive string of the hardware being used."""
    import torch
    device = get_device()
    if device == "cuda":
        return f"NVIDIA GPU ({torch.cuda.get_device_name(0)})"
    elif device == "mps":
        return "Apple Silicon (Metal)"
    return "Standard CPU"

def clear_directory(path: Path) -> bool:
    """Securely deletes all files within a directory."""
    try:
        if not path.exists():
            return True
            
        logger = logging.getLogger("LocalRAG")
        logger.info(f"🗑️ Clearing directory: {path}...")
        
        for item in path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                import shutil
                shutil.rmtree(item)
        
        logger.info(f"✔ Directory {path} cleared.")
        return True
    except Exception as e:
        logger = logging.getLogger("LocalRAG")
        logger.error(f"❌ Failed to clear directory {path}: {e}")
        return False

# Initialize a default logger instance
logger = setup_logging()
