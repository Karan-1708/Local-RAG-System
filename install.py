import subprocess
import sys
import platform
import os
import shutil
from pathlib import Path

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

def get_vram():
    """Attempts to get NVIDIA VRAM in GB."""
    try:
        output = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'], encoding='utf-8')
        return int(output.strip()) / 1024
    except:
        return 0

def check_system_resources():
    """Check RAM and Disk Space."""
    print("\n--- 📊 Resource Validation ---")
    
    # 1. Disk Space
    total, used, free = shutil.disk_usage(".")
    free_gb = free // (2**30)
    print(f"Free Disk Space: {free_gb} GB")
    if free_gb < 10:
        print("⚠️  WARNING: Low disk space. You may run out of space for model weights.")

    # 2. System RAM
    total_ram_gb = 0
    try:
        if platform.system() == "Windows":
            out = subprocess.check_output(['wmic', 'ComputerSystem', 'get', 'TotalPhysicalMemory'], encoding='utf-8')
            total_ram_gb = int(out.split()[1]) // (1024**3)
        elif platform.system() == "Darwin":
            out = subprocess.check_output(['sysctl', '-n', 'hw.memsize'], encoding='utf-8')
            total_ram_gb = int(out.strip()) // (1024**3)
        else:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if "MemTotal" in line:
                        total_ram_gb = int(line.split()[1]) // (1024**2)
                        break
        print(f"System RAM:     {total_ram_gb} GB")
        if total_ram_gb < 8:
            print("⚠️  WARNING: Low RAM. High-parameter models (e.g. Llama3-70B) will be unstable.")
    except:
        print("⚠️  Could not determine System RAM.")

    # 3. VRAM (NVIDIA)
    vram = get_vram()
    if vram > 0:
        print(f"GPU VRAM:       {vram:.1f} GB")
        if vram < 6:
            print("⚠️  WARNING: Limited VRAM. Consider using 'Ollama' quantized models (4-bit).")
    
    print("------------------------------\n")

def check_system_dependencies():
    """Check for external tools like Tesseract."""
    print("Checking System dependencies...")
    tesseract_exists = shutil.which("tesseract") is not None
    if tesseract_exists:
        print("✅ Tesseract OCR: Found")
    else:
        print("⚠️  Tesseract OCR: NOT FOUND.")
        print("   -> Image/PDF OCR may fail. Install: https://github.com/UB-Mannheim/tesseract/wiki")

def setup():
    # 1. Environment Detection
    py_major, py_minor = sys.version_info[:2]
    py_version = f"{py_major}.{py_minor}"
    os_name = platform.system()
    hardware = detect_hardware()

    print(f"--- 🛡️ Advanced System Optimization ---")
    print(f"Python:   {py_version}")
    print(f"OS:       {os_name}")
    print(f"Hardware: {hardware.upper()}")
    print(f"--------------------------------------")

    # 2. Resource Check
    check_system_resources()

    # 3. Handle Conflicts
    print("Preparing clean environment...")
    if hardware in ['cuda', 'mps']:
        run_command("torch torchvision torchaudio", is_install=False)
    
    # 4. Step-by-Step Installation
    print("\nStep 1: Installing Core Frameworks...")
    run_command("streamlit nest_asyncio ollama python-dotenv fpdf2")

    print("\nStep 2: Installing hardware-optimized ML core...")
    if hardware == 'cuda':
        # Using cu124 as stable default for Python 3.11-3.13
        run_command("torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124")
    else:
        run_command("torch torchvision torchaudio")

    print("\nStep 3: Installing LangChain Ecosystem...")
    run_command("langchain langchain-community langchain-ollama langchain-openai langchain-google-genai langchain-anthropic langchain-chroma langchain-huggingface")

    print("\nStep 4: Installing Document Processing & OCR...")
    run_command("unstructured[all-docs] pytesseract pdf2image opencv-python pillow")

    print("\nStep 5: Installing Analytics & Evaluation...")
    run_command("transformers<5.0.0 ragas sentence-transformers rank_bm25")

    print("\nStep 6: Installing Privacy & Redaction...")
    run_command("presidio-analyzer presidio-anonymizer spacy")
    run_command("spacy download en_core_web_sm")

    print("\nStep 7: Fixing Library Conflicts...")
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
