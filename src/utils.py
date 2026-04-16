import logging
import os
import platform
import shutil
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
    if not target_path.is_relative_to(base_dir.resolve()):
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
                shutil.rmtree(item)
        
        logger.info(f"✔ Directory {path} cleared.")
        return True
    except Exception as e:
        logger = logging.getLogger("LocalRAG")
        logger.error(f"❌ Failed to clear directory {path}: {e}")
        return False

def _get_ram_gb() -> str:
    import subprocess
    try:
        if platform.system() == "Windows":
            # PowerShell CIM (works on Windows 10/11; wmic is deprecated/removed)
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 "(Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize"],
                capture_output=True, text=True
            )
            if r.returncode == 0 and r.stdout.strip().isdigit():
                return f"{round(int(r.stdout.strip()) / (1024 * 1024), 2)} GB"
        elif platform.system() == "Darwin":
            r = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
            if r.returncode == 0:
                return f"{round(int(r.stdout.strip()) / 1024 ** 3, 2)} GB"
        else:
            with open("/proc/meminfo") as f:
                for line in f:
                    if "MemTotal" in line:
                        return f"{round(int(line.split()[1]) / (1024 * 1024), 2)} GB"
    except Exception:
        pass
    return "Unknown"


def log_startup_info():
    """Logs system environment info at application startup."""
    _log = logging.getLogger("LocalRAG")

    os_name    = platform.system()
    os_release = platform.release()
    arch       = platform.architecture()[0]
    ram        = _get_ram_gb()

    # Tesseract
    import config as _cfg
    tess_path = shutil.which("tesseract") or (
        str(_cfg.TESSERACT_CMD) if Path(str(_cfg.TESSERACT_CMD)).exists() else None
    )
    tess_status = f"Detected [OK] ({tess_path})" if tess_path else "Not found"

    # PyTorch + CUDA/MPS
    try:
        import torch
        torch_ver   = torch.__version__
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            accel_status = f"Detected [OK] (Device: {device_name})"
            accel_label  = "CUDA"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            accel_status = "Detected [OK] (Apple Silicon)"
            accel_label  = "MPS"
        else:
            accel_status = "Not available — running on CPU"
            accel_label  = "GPU Acceleration"
    except Exception:
        torch_ver    = "Not installed"
        accel_status = "Unknown"
        accel_label  = "GPU Acceleration"

    _log.info(f"OS: {os_name} {os_release}")
    _log.info(f"Python: {sys.version}")
    _log.info(f"Python Executable: {sys.executable}")
    _log.info(f"Architecture: {arch}")
    _log.info(f"Total RAM: {ram}")
    _log.info(f"Tesseract OCR: {tess_status}")
    _log.info(f"PyTorch Version: {torch_ver}")
    _log.info(f"{accel_label}: {accel_status}")


# Initialize a default logger instance
logger = setup_logging()
