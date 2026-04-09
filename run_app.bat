@echo off
SETLOCAL EnableDelayedExpansion

echo 🛡️ Local RAG System: Starter
echo -----------------------------------

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python from python.org and try again.
    pause
    exit /b
)

:: 2. Setup Virtual Environment
if not exist ".venv" (
    echo [INFO] Creating virtual environment...
    python -m venv .venv
)

:: 3. Activate Environment
echo [INFO] Activating environment...
call .venv\Scripts\activate

:: 4. Run Smart Installer
if not exist ".venv\installed.flag" (
    echo [INFO] First time setup: Installing dependencies...
    python install.py
    if %errorlevel% equ 0 (
        echo Done > .venv\installed.flag
    ) else (
        echo [ERROR] Installation failed. Please check the logs above.
        pause
        exit /b
    )
)

:: 5. Setup .env if missing
if not exist ".env" (
    echo [INFO] Creating .env from template...
    copy env.template .env
    echo [ACTION] Please edit .env to add your HF_TOKEN if needed.
)

:: 6. Launch Application
echo [SUCCESS] Starting Local RAG...
streamlit run app.py

pause
