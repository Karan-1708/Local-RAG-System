import subprocess
import sys
import platform
import os
import shutil

def run_command(command, is_install=True):
    """Executes a pip command. Handles both install and uninstall."""
    action = "install" if is_install else "uninstall -y"
    print(f"Executing: pip {action} {command}")
    try:
        args = [sys.executable, "-m", "pip"] + action.split() + command.split()
        subprocess.check_call(args)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during {action}: {e}")
        return False

def detect_hardware():
    """Returns: 'cuda', 'mps', or 'cpu'"""
    os_name = platform.system()
    try:
        subprocess.check_output(['nvidia-smi'], stderr=subprocess.STDOUT)
        return 'cuda'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    if os_name == "Darwin":
        processor = platform.processor().lower()
        if "arm" in processor or "apple" in processor:
            return 'mps'
    return 'cpu'

def check_system_dependencies():
    """Check for external tools like Tesseract."""
    print("\nChecking System dependencies...")
    tesseract_exists = shutil.which("tesseract") is not None
    if tesseract_exists:
        print("✅ Tesseract OCR: Found")
    else:
        print("⚠️  Tesseract OCR: NOT FOUND in PATH.")
        print("   -> Image/PDF OCR may fail. Download from: https://github.com/UB-Mannheim/tesseract/wiki")

def setup():
    # 1. Environment Detection
    py_major, py_minor = sys.version_info[:2]
    py_version = f"{py_major}.{py_minor}"
    os_name = platform.system()
    hardware = detect_hardware()

    print(f"--- 🛡️ Advanced System Validation ---")
    print(f"Python:   {py_version}")
    print(f"OS:       {os_name}")
    print(f"Hardware: {hardware.upper()}")
    print(f"--------------------------------------\n")

    # 2. Version Validation
    if py_major < 3 or (py_major == 3 and py_minor < 10):
        print("❌ ERROR: This application requires Python 3.10 or higher.")
        sys.exit(1)

    # 3. Handle Conflicts (Uninstall old logic)
    print("Preparing clean environment...")
    if hardware in ['cuda', 'mps']:
        run_command("torch torchvision torchaudio", is_install=False)
    
    # 4. Step-by-Step Installation
    print("\nStep 1: Installing Core Frameworks...")
    run_command("streamlit nest_asyncio ollama python-dotenv fpdf2")

    print("\nStep 2: Installing hardware-optimized ML core...")
    if hardware == 'cuda':
        run_command("torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124")
    elif hardware == 'mps':
        run_command("torch torchvision torchaudio")
    else:
        run_command("torch torchvision torchaudio")

    print("\nStep 3: Installing LangChain Ecosystem...")
    # Pinning specific versions known to be stable with Python 3.10-3.13
    run_command("langchain langchain-community langchain-ollama langchain-openai langchain-google-genai langchain-anthropic langchain-chroma langchain-huggingface")

    print("\nStep 4: Installing Document Processing & OCR...")
    run_command("unstructured[all-docs] pytesseract pdf2image opencv-python pillow")

    print("\nStep 5: Installing Analytics & Evaluation...")
    # Pin transformers to avoid the v5 __path__ bug
    run_command("transformers<5.0.0 ragas sentence-transformers rank_bm25")

    print("\nStep 6: Installing Privacy & Redaction...")
    run_command("presidio-analyzer presidio-anonymizer spacy")
    run_command("spacy download en_core_web_sm")

    print("\nStep 7: Fixing Library Conflicts...")
    # Important: Many AI libs break with Numpy 2.0+ on older Python versions
    if py_minor >= 12:
        run_command("numpy<=2.3.0")
    else:
        run_command("numpy<2.0.0")

    # 5. Final System Check
    check_system_dependencies()

    print("\n✅ Setup complete! Environment is fully optimized and validated.")
    print(f"Ready to run on {hardware.upper()} with Python {py_version}")

if __name__ == "__main__":
    setup()
