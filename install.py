"""
Local RAG System — Universal Setup Engine
==========================================
Handles system scanning, Python validation, virtual environment management,
Tesseract detection, GPU-aware PyTorch selection, and .env creation.

Designed to be friendly for non-technical users.
Run directly:  python install.py
Or called by:  run_app.bat / run_app.sh
"""

import os
import sys
import platform
import subprocess
import shutil
import json
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
#  ANSI COLOUR HELPERS  (enabled on Windows 10+, Mac, Linux)
# ══════════════════════════════════════════════════════════════════════════════

def _enable_ansi_windows():
    if platform.system() == "Windows":
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetConsoleMode(k.GetStdHandle(-11), 7)
        except Exception:
            pass

_enable_ansi_windows()

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"

# ── Print helpers ─────────────────────────────────────────────────────────────

def banner():
    print(f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════╗
║       🛡️  Local RAG System  ·  Setup Engine              ║
║          Privacy-First AI  ·  All Platforms              ║
╚══════════════════════════════════════════════════════════╝{C.RESET}
""")

def section(n, total, title):
    bar = "─" * 52
    print(f"\n{C.BOLD}{C.BLUE}┌{bar}┐{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}│{C.RESET}  {C.BOLD}Step {n}/{total}{C.RESET}  {C.WHITE}{title:<44}{C.RESET}{C.BOLD}{C.BLUE}│{C.RESET}")
    print(f"{C.BOLD}{C.BLUE}└{bar}┘{C.RESET}")

def ok(msg):    print(f"  {C.GREEN}✔{C.RESET}  {msg}")
def info(msg):  print(f"  {C.CYAN}ℹ{C.RESET}  {msg}")
def warn(msg):  print(f"  {C.YELLOW}⚠{C.RESET}  {msg}")
def err(msg):   print(f"  {C.RED}✘{C.RESET}  {C.RED}{msg}{C.RESET}")

def fatal(msg):
    print(f"\n{C.RED}{C.BOLD}  ✘  FATAL: {msg}{C.RESET}")
    print(f"{C.RED}  Setup cannot continue. Fix the issue above, then try again.{C.RESET}\n")
    sys.exit(1)

def progress_bar(label, pct, width=28):
    filled = int(width * pct / 100)
    bar    = f"{C.CYAN}{'█' * filled}{'░' * (width - filled)}{C.RESET}"
    print(f"\r  {C.DIM}{label}{C.RESET} [{bar}] {C.BOLD}{pct:3d}%{C.RESET}", end="", flush=True)

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1 — SYSTEM SCAN
# ══════════════════════════════════════════════════════════════════════════════

def scan_system() -> dict:
    """Collect OS, CPU, RAM, GPU details. Returns a structured dict."""
    s = {}

    s["os"]         = platform.system()
    s["os_release"] = platform.release()
    s["machine"]    = platform.machine()
    s["arch"]       = platform.architecture()[0]
    s["cpu_name"]   = _cpu_name()
    s["cpu_cores"]  = os.cpu_count() or 1
    s["ram_gb"]     = _ram_gb()
    s["gpu"]        = _detect_gpu()
    s["python_version"] = platform.python_version()
    s["python_tuple"]   = tuple(sys.version_info[:3])
    s["python_exe"]     = sys.executable

    return s


def _cpu_name() -> str:
    try:
        if platform.system() == "Windows":
            try:
                cmd = "powershell -command \"(Get-CimInstance Win32_Processor).Name\""
                r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if r.returncode == 0 and r.stdout.strip():
                    return r.stdout.strip()
            except: pass
            try:
                r = subprocess.run("wmic cpu get Name", shell=True, capture_output=True, text=True)
                lines = [l.strip() for l in r.stdout.splitlines() if l.strip() and l.strip().lower() != "name"]
                if lines: return lines[0]
            except: pass
            return os.environ.get("PROCESSOR_IDENTIFIER", "Generic Windows CPU")
        elif platform.system() == "Darwin":
            r = subprocess.run("sysctl -n machdep.cpu.brand_string", shell=True, capture_output=True, text=True)
            return r.stdout.strip() or "Apple Silicon"
        else:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return "Unknown CPU"


def _ram_gb() -> float:
    try:
        if platform.system() == "Windows":
            r = subprocess.run("wmic OS get TotalVisibleMemorySize", shell=True, capture_output=True, text=True)
            lines = [l.strip() for l in r.stdout.splitlines() if l.strip() and l.strip().isdigit()]
            if lines:
                return round(int(lines[0]) / (1024 * 1024), 1)
            r = subprocess.run("systeminfo", shell=True, capture_output=True, text=True)
            for line in r.stdout.splitlines():
                if "Total Physical Memory" in line:
                    parts = line.split(":", 1)[1].strip().replace(",", "").split()
                    if parts:
                        val = int(parts[0])
                        return round(val / 1024, 1) if "MB" in line else round(val, 1)
        elif platform.system() == "Darwin":
            r = subprocess.run("sysctl -n hw.memsize", shell=True, capture_output=True, text=True)
            return round(int(r.stdout.strip()) / 1024 ** 3, 1)
        else:
            with open("/proc/meminfo") as f:
                for line in f:
                    if "MemTotal" in line:
                        return round(int(line.split()[1]) / (1024 * 1024), 1)
    except Exception:
        pass
    return 0.0


def _detect_gpu() -> dict:
    """Returns {vendor, name, cuda, mps, backend, vram_gb}"""
    gpu = {"vendor": "none", "name": "None detected", "cuda": False, "mps": False, "backend": "cpu", "vram_gb": 0.0}

    # NVIDIA via nvidia-smi
    if shutil.which("nvidia-smi"):
        try:
            r = subprocess.run(
                "nvidia-smi --query-gpu=name,memory.total --format=csv,noheader",
                shell=True, capture_output=True, text=True
            )
            if r.returncode == 0 and r.stdout.strip():
                line = r.stdout.splitlines()[0].strip()
                parts = line.split(",")
                name = parts[0].strip()
                vram = round(int(parts[1].strip().split()[0]) / 1024, 1) if len(parts) > 1 else 0.0
                gpu.update(vendor="nvidia", name=name, cuda=True, backend="cuda", vram_gb=vram)
                return gpu
        except Exception:
            pass

    # Apple Silicon MPS
    if platform.system() == "Darwin" and platform.machine() in ("arm64", "arm64e"):
        gpu.update(vendor="apple", name="Apple Silicon GPU (MPS)", mps=True, backend="mps")
        return gpu

    # Windows fallback — show AMD/Intel GPU name
    if platform.system() == "Windows":
        try:
            r = subprocess.run("wmic path win32_VideoController get name", shell=True, capture_output=True, text=True)
            lines = [l.strip() for l in r.stdout.splitlines() if l.strip() and l.strip().lower() != "name"]
            if lines:
                name = lines[0]
                vendor = "amd" if ("amd" in name.lower() or "radeon" in name.lower()) else \
                         "intel" if "intel" in name.lower() else "other"
                gpu.update(vendor=vendor, name=name, backend="cpu")
                return gpu
        except Exception:
            pass

    return gpu


def print_system_report(s: dict):
    gpu     = s["gpu"]
    accel   = ""
    vram    = ""
    if gpu["cuda"]:
        accel = f"  {C.GREEN}[CUDA]{C.RESET}"
        if gpu["vram_gb"] > 0:
            vram = f"  {C.DIM}({gpu['vram_gb']} GB VRAM){C.RESET}"
    elif gpu["mps"]:
        accel = f"  {C.GREEN}[MPS]{C.RESET}"

    print(f"""
  {C.DIM}┌───────────────────────────────────────────────┐{C.RESET}
  {C.DIM}│{C.RESET}  {C.BOLD}System Scan Results{C.RESET}
  {C.DIM}│{C.RESET}
  {C.DIM}│{C.RESET}  {C.DIM}OS               {C.RESET}   {C.WHITE}{s['os']} {s['os_release']}{C.RESET}
  {C.DIM}│{C.RESET}  {C.DIM}Architecture     {C.RESET}   {C.WHITE}{s['machine']}  ({s['arch']}){C.RESET}
  {C.DIM}│{C.RESET}  {C.DIM}CPU              {C.RESET}   {C.WHITE}{s['cpu_name']}{C.RESET}
  {C.DIM}│{C.RESET}  {C.DIM}CPU Threads      {C.RESET}   {C.WHITE}{s['cpu_cores']}{C.RESET}
  {C.DIM}│{C.RESET}  {C.DIM}RAM              {C.RESET}   {C.WHITE}{s['ram_gb']} GB{C.RESET}
  {C.DIM}│{C.RESET}  {C.DIM}GPU              {C.RESET}   {C.WHITE}{gpu['name']}{C.RESET}{accel}{vram}
  {C.DIM}│{C.RESET}  {C.DIM}Python           {C.RESET}   {C.WHITE}{s['python_version']}{C.RESET}
  {C.DIM}│{C.RESET}
  {C.DIM}│{C.RESET}  {C.DIM}PyTorch Backend  {C.RESET}   {C.CYAN}{C.BOLD}{gpu['backend'].upper()}{C.RESET}
  {C.DIM}└───────────────────────────────────────────────┘{C.RESET}""")

    # Resource warnings
    if s["ram_gb"] > 0 and s["ram_gb"] < 8:
        warn("Low RAM (<8 GB). Large models (e.g. Llama3-70B) may be unstable.")
    if gpu["cuda"] and gpu["vram_gb"] > 0 and gpu["vram_gb"] < 6:
        warn("Limited VRAM (<6 GB). Use quantized Ollama models (4-bit) for best results.")

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2 — PYTHON VERSION GATE
# ══════════════════════════════════════════════════════════════════════════════

MIN_PYTHON = (3, 11)

def check_python():
    major, minor, micro = sys.version_info[:3]
    ver = f"{major}.{minor}.{micro}"
    if (major, minor) < MIN_PYTHON:
        fatal(
            f"Python {ver} is too old.\n"
            f"  This application requires Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer.\n"
            f"  Download the latest version from:  https://www.python.org/downloads/"
        )
    ok(f"Python {ver}  ✓")

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — VIRTUAL ENVIRONMENT  (interactive scan + selection)
# ══════════════════════════════════════════════════════════════════════════════

VENV_DIR = Path(".venv")

def _venv_python() -> Path:
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _probe_venv(venv_path: Path) -> dict | None:
    if platform.system() == "Windows":
        py = venv_path / "Scripts" / "python.exe"
    else:
        py = venv_path / "bin" / "python"

    if not py.exists():
        return None

    r = subprocess.run([str(py), "--version"], capture_output=True, text=True)
    if r.returncode != 0:
        return {"path": venv_path, "python_exe": py, "version": "?", "healthy": False}

    ver = (r.stdout.strip() or r.stderr.strip()).replace("Python ", "").strip()
    return {"path": venv_path, "python_exe": py, "version": ver, "healthy": True}


def _scan_for_venvs(root: Path = Path("."), max_depth: int = 2) -> list[dict]:
    """Detect venv directories by structure (not name)."""
    candidates = []
    IS_WINDOWS = platform.system() == "Windows"

    SKIP_NAMES = {
        "node_modules", "__pycache__", ".git", ".hg", ".svn",
        "dist", "build", "site-packages", ".mypy_cache", ".pytest_cache",
        ".tox", ".nox", "htmlcov", ".eggs", "example",
    }

    def _looks_like_venv(path: Path) -> bool:
        if IS_WINDOWS:
            return (path / "Scripts" / "python.exe").exists()
        return (path / "bin" / "python").exists() or (path / "bin" / "python3").exists()

    def _walk(path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for child in sorted(path.iterdir()):
                if not child.is_dir() or child.name in SKIP_NAMES:
                    continue
                if _looks_like_venv(child):
                    probe = _probe_venv(child)
                    if probe:
                        candidates.append(probe)
                else:
                    _walk(child, depth + 1)
        except PermissionError:
            pass

    _walk(root, 0)
    candidates.sort(key=lambda v: (0 if v["healthy"] else 1, str(v["path"])))
    return candidates


def _ask_choice(prompt: str, options: list[str], default: int = 0) -> int:
    print()
    for i, opt in enumerate(options):
        marker = f"{C.CYAN}►{C.RESET}" if i == default else " "
        print(f"  {marker} {C.BOLD}[{i + 1}]{C.RESET}  {opt}")
    print()

    while True:
        try:
            raw = input(f"  {C.YELLOW}Enter number (default {default + 1}): {C.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            fatal("Setup cancelled by user.")

        if raw == "":
            return default
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return idx
        print(f"  {C.RED}Invalid choice — please enter a number between 1 and {len(options)}.{C.RESET}")


def _create_new_venv(target: Path):
    if target.exists():
        warn(f"{target} already exists — removing it first...")
        shutil.rmtree(target)
    info(f"Creating virtual environment at {C.CYAN}{target}{C.RESET} …")
    r = subprocess.run([sys.executable, "-m", "venv", str(target)], capture_output=True, text=True)
    if r.returncode != 0:
        fatal(f"Could not create virtual environment:\n  {r.stderr}")
    ok(f"Virtual environment created at {target}")


def ensure_venv():
    global VENV_DIR

    info("Scanning for existing virtual environments…")
    found = _scan_for_venvs()

    options = []
    meta    = []

    for v in found:
        status = f"{C.GREEN}healthy{C.RESET}" if v["healthy"] else f"{C.RED}damaged{C.RESET}"
        label  = (
            f"Use existing  {C.CYAN}{v['path']}{C.RESET}"
            f"  —  Python {v['version']}  [{status}]"
        )
        options.append(label)
        meta.append(("existing", v))

    options.append(f"Create a {C.BOLD}new{C.RESET} .venv in this folder  {C.DIM}(recommended){C.RESET}")
    meta.append(("new", None))

    if found:
        print(f"\n  {C.WHITE}Found {len(found)} virtual environment(s). Choose one to use:{C.RESET}")
        default_idx = 0
    else:
        info("No existing virtual environments found.")
        print(f"  {C.WHITE}Choose an option:{C.RESET}")
        default_idx = len(options) - 1

    chosen_idx = _ask_choice("Select virtual environment", options, default=default_idx)
    kind, data = meta[chosen_idx]

    if kind == "new":
        target   = Path(".venv")
        _create_new_venv(target)
        VENV_DIR = target
    else:
        venv_path = data["path"]
        VENV_DIR  = venv_path

        if not data["healthy"]:
            warn(f"The selected environment at {venv_path} appears damaged.")
            fix_choice = _ask_choice(
                "Fix damaged venv",
                [
                    f"Rebuild it  {C.DIM}(delete and recreate at the same path){C.RESET}",
                    f"Use it anyway  {C.DIM}(may cause errors){C.RESET}",
                ],
                default=0,
            )
            if fix_choice == 0:
                _create_new_venv(venv_path)
            else:
                warn("Proceeding with damaged environment — some packages may not load.")
        else:
            ok(f"Using  {C.CYAN}{venv_path}{C.RESET}  (Python {data['version']})")

    print(f"  {C.DIM}Active venv → {VENV_DIR.resolve()}{C.RESET}")

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 4 — TESSERACT OCR CHECK
# ══════════════════════════════════════════════════════════════════════════════

def check_tesseract():
    """Check for Tesseract OCR. Warn with install instructions if missing."""
    os_name = platform.system()

    # 1. Check system PATH
    if shutil.which("tesseract"):
        try:
            r = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
            ver_line = r.stdout.splitlines()[0] if r.stdout else "found"
            ok(f"Tesseract OCR on PATH  ({ver_line})")
        except Exception:
            ok("Tesseract OCR found on PATH")
        return

    # 2. Check common install paths (Windows)
    if os_name == "Windows":
        common_paths = [
            Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
            Path(r"H:\AI_Apps\TesseractOCR\tesseract.exe"),
        ]
        for p in common_paths:
            if p.exists():
                ok(f"Tesseract OCR found at {p}")
                info(f"Set TESSERACT_CMD={p} in your .env file if OCR fails.")
                return

    # 3. Not found — provide platform-specific install instructions
    warn("Tesseract OCR not found. Image/PDF OCR will be unavailable.")
    if os_name == "Windows":
        info("Install from: https://github.com/UB-Mannheim/tesseract/wiki")
        info("Then set TESSERACT_CMD=<path>\\tesseract.exe in your .env file.")
    elif os_name == "Darwin":
        info("Install via Homebrew:  brew install tesseract")
    else:
        info("Install via apt:  sudo apt-get install tesseract-ocr")
    info("OCR features will be disabled until Tesseract is installed.")

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 5 — DEPENDENCIES  (PyTorch + app packages)
# ══════════════════════════════════════════════════════════════════════════════

# All app packages (torch handled separately below)
APP_PACKAGES = [
    # Core UI & Framework
    "streamlit",
    "nest_asyncio",
    "pydantic",
    "fastapi",
    "uvicorn",
    "python-dotenv",
    "fpdf2",
    # LangChain Ecosystem
    "langchain",
    "langchain-community",
    "langchain-ollama",
    "ollama",
    "langchain-openai",
    "langchain-google-genai",
    "langchain-anthropic",
    "langchain-chroma",
    "langchain-huggingface",
    # Document Processing & OCR
    "unstructured[all-docs]",
    "pytesseract",
    "pdf2image",
    "opencv-python",
    "pillow",
    # Embeddings & Re-ranking
    "sentence-transformers",
    "rank_bm25",
    # Evaluation & Confidence
    "transformers<5.0.0",
    "ragas",
    "datasets",
    # Privacy & Redaction
    "presidio-analyzer",
    "presidio-anonymizer",
    "spacy",
    # Utilities
    "numpy<=2.3.0",
]

TORCH_INDEXES = {
    "cuda_new": "https://download.pytorch.org/whl/cu124",  # Python 3.12+, CUDA 12.4
    "cuda_old": "https://download.pytorch.org/whl/cu121",  # Python 3.11,  CUDA 12.1
    "cpu":      "https://download.pytorch.org/whl/cpu",
}


def install_dependencies(sys_info: dict):
    python = str(_venv_python())

    # ── Upgrade pip ──────────────────────────────────────────────────────────
    info("Upgrading pip…")
    subprocess.run(
        [python, "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
        check=False
    )

    # ── PyTorch (GPU-aware) ──────────────────────────────────────────────────
    _install_torch(python, sys_info)

    # ── App packages ─────────────────────────────────────────────────────────
    info("Installing application packages…")
    success = _pip_install(python, APP_PACKAGES)
    if success:
        ok("All application packages installed")
    else:
        err("Some packages failed. Re-running with verbose output…")
        _pip_install(python, APP_PACKAGES, quiet=False)

    # ── spaCy language model ──────────────────────────────────────────────────
    info("Downloading spaCy English model (en_core_web_sm)…")
    r = subprocess.run(
        [python, "-m", "spacy", "download", "en_core_web_sm"],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        ok("spaCy model en_core_web_sm ready")
    else:
        warn(f"spaCy model download failed: {r.stderr[:200]}")
        warn("PII redaction may not work. Run manually: python -m spacy download en_core_web_sm")


def _get_installed_torch_info(python: str) -> dict | None:
    probe = (
        "import torch, json; "
        "print(json.dumps({"
        "'version': torch.__version__, "
        "'cuda_version': torch.version.cuda, "
        "'is_cpu_only': torch.version.cuda is None"
        "}))"
    )
    r = subprocess.run([python, "-c", probe], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout.strip())
    except Exception:
        return None


def _force_uninstall_torch(python: str):
    packages = ["torch", "torchaudio", "torchvision", "triton"]
    subprocess.run(
        [python, "-m", "pip", "uninstall"] + packages + ["-y"],
        capture_output=True, text=True
    )


def _install_torch(python: str, sys_info: dict):
    backend  = sys_info["gpu"]["backend"]
    py_tuple = sys_info["python_tuple"]

    cuda_index = TORCH_INDEXES["cuda_new"] if py_tuple >= (3, 12) else TORCH_INDEXES["cuda_old"]
    cuda_label = "CUDA 12.4" if py_tuple >= (3, 12) else "CUDA 12.1"

    existing = _get_installed_torch_info(python)

    if existing:
        installed_ver = existing["version"]

        if backend == "cuda" and existing["is_cpu_only"]:
            warn(f"PyTorch {installed_ver} is a CPU-only build but NVIDIA GPU detected.")
            _force_uninstall_torch(python)
            info(f"Reinstalling with {cuda_label} support…")
            _pip_install_indexed(python, ["torch", "torchvision", "torchaudio"], cuda_index, cuda_label)
            return

        if backend == "cuda" and not existing["is_cpu_only"]:
            installed_cuda = existing.get("cuda_version") or ""
            expected_cu    = "12.4" if py_tuple >= (3, 12) else "12.1"
            if not installed_cuda.startswith(expected_cu.replace(".", "")):
                warn(f"PyTorch {installed_ver} uses CUDA {installed_cuda}, expected {expected_cu}.")
                _force_uninstall_torch(python)
                _pip_install_indexed(python, ["torch", "torchvision", "torchaudio"], cuda_index, cuda_label)
            else:
                ok(f"PyTorch {installed_ver} ({cuda_label}) already installed — skipping")
            return

        if backend == "mps":
            ok(f"PyTorch {installed_ver} (MPS) already installed — skipping")
            return

        ok(f"PyTorch {installed_ver} (CPU) already installed — skipping")
        return

    # ── Not installed ─────────────────────────────────────────────────────────
    if backend == "cuda":
        info(f"NVIDIA GPU detected — installing PyTorch ({cuda_label})…")
        _pip_install_indexed(python, ["torch", "torchvision", "torchaudio"], cuda_index, cuda_label)
    elif backend == "mps":
        info("Apple Silicon detected — installing PyTorch with MPS support…")
        _pip_install(python, ["torch", "torchvision", "torchaudio"])
        ok("PyTorch (MPS / Apple Silicon) installed")
    else:
        info("No GPU detected — installing PyTorch (CPU)…")
        _pip_install_indexed(python, ["torch", "torchvision", "torchaudio"], TORCH_INDEXES["cpu"], "CPU")


def _pip_install(python: str, packages: list, quiet: bool = True) -> bool:
    cmd = [python, "-m", "pip", "install"] + packages
    if quiet:
        cmd.append("--quiet")
    r = subprocess.run(cmd, capture_output=quiet, text=True)
    if r.returncode != 0:
        if quiet:
            warn(f"Some packages may have failed:\n  {r.stderr[:300]}")
        return False
    return True


def _pip_install_indexed(python: str, packages: list, index_url: str, label: str):
    info(f"Installing PyTorch ({label}) — this may take a few minutes…")
    cmd = [python, "-m", "pip", "install"] + packages + [
        "--index-url", index_url,
        "--force-reinstall",
        "--no-cache-dir",
        "--quiet",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        warn(f"PyTorch ({label}) install issue: {r.stderr[:200]}")
        warn("Falling back to CPU-only PyTorch…")
        _pip_install_indexed(python, packages, TORCH_INDEXES["cpu"], "CPU fallback")
    else:
        ok(f"PyTorch ({label}) installed")

# ══════════════════════════════════════════════════════════════════════════════
#  STEP 6 — .env FILE
# ══════════════════════════════════════════════════════════════════════════════

def ensure_env_file():
    env_path     = Path(".env")
    example_path = Path(".env.example")

    if env_path.exists():
        ok(".env file already exists")
        return

    if example_path.exists():
        shutil.copy(example_path, env_path)
        ok(".env created from .env.example")
        info("Open .env and set INTERNAL_API_KEY and any API keys you need.")
    else:
        warn(".env.example not found — creating a minimal .env")
        import secrets
        key = secrets.token_hex(24)
        env_path.write_text(
            f"# Local RAG System Configuration\n"
            f"INTERNAL_API_KEY={key}\n"
            f"LLM_MODEL=llama3:8b\n"
            f"EMBEDDING_MODEL=all-MiniLM-L6-v2\n"
        )
        ok(f".env created with a generated INTERNAL_API_KEY")
        info("Open .env to review and add any optional API keys.")

# ══════════════════════════════════════════════════════════════════════════════
#  VERIFY INSTALL
# ══════════════════════════════════════════════════════════════════════════════

def verify_install(sys_info: dict):
    python  = str(_venv_python())
    backend = sys_info["gpu"]["backend"]

    checks = {
        "streamlit":          "import streamlit",
        "fastapi":            "import fastapi",
        "torch":              "import torch",
        "langchain":          "import langchain",
        "langchain_chroma":   "import langchain_chroma",
        "sentence_transformers": "import sentence_transformers",
        "presidio_analyzer":  "import presidio_analyzer",
    }

    all_ok = True
    for name, stmt in checks.items():
        r = subprocess.run([python, "-c", stmt], capture_output=True)
        if r.returncode == 0:
            ok(f"{name}")
        else:
            err(f"{name}  ← could not import")
            all_ok = False

    if backend == "cuda":
        r = subprocess.run([python, "-c", "import torch; assert torch.cuda.is_available()"], capture_output=True)
        if r.returncode == 0: ok("CUDA acceleration verified")
        else: warn("CUDA not detected at runtime — will use CPU")
    elif backend == "mps":
        r = subprocess.run([python, "-c", "import torch; assert torch.backends.mps.is_available()"], capture_output=True)
        if r.returncode == 0: ok("MPS acceleration verified")
        else: warn("MPS not available — will use CPU")

    return all_ok

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

TOTAL_STEPS = 6

def setup():
    banner()
    section(1, TOTAL_STEPS, "Scanning Your System")
    sys_info = scan_system()
    print_system_report(sys_info)

    section(2, TOTAL_STEPS, "Checking Python Version")
    check_python()

    section(3, TOTAL_STEPS, "Preparing Virtual Environment")
    ensure_venv()

    section(4, TOTAL_STEPS, "Checking Tesseract OCR")
    check_tesseract()

    section(5, TOTAL_STEPS, "Installing Dependencies")
    install_dependencies(sys_info)

    section(6, TOTAL_STEPS, "Setting Up Configuration")
    ensure_env_file()

    print(f"\n{C.BOLD}{C.MAGENTA}  Verifying installation…{C.RESET}")
    all_ok = verify_install(sys_info)

    print(f"\n{C.GREEN}{C.BOLD}╔══════════════════════════════════════════════════════════╗")
    print(f"║           Setup Complete! Run run_app.bat to start.      ║")
    print(f"╚══════════════════════════════════════════════════════════╝{C.RESET}")
    if not all_ok:
        warn("Some issues were detected. Check the warnings above.")

    return str(_venv_python())

if __name__ == "__main__":
    setup()
