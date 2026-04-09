#!/bin/bash

echo "🛡️ Local RAG System: Starter"
echo "-----------------------------------"

# 1. Check for Python
if ! command -v python3 &> /dev/null
then
    echo "[ERROR] Python3 is not installed."
    echo "Please install Python 3.10+ and try again."
    exit 1
fi

# 2. Setup Virtual Environment
if [ ! -d ".venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv .venv
fi

# 3. Activate Environment
echo "[INFO] Activating environment..."
source .venv/bin/activate

# 4. Run Smart Installer
if [ ! -f ".venv/installed.flag" ]; then
    echo "[INFO] First time setup: Installing dependencies..."
    python3 install.py
    if [ $? -eq 0 ]; then
        echo "Done" > .venv/installed.flag
    else
        echo "[ERROR] Installation failed."
        exit 1
    fi
fi

# 5. Setup .env if missing
if [ ! -f ".env" ]; then
    echo "[INFO] Creating .env from template..."
    cp env.template .env
    echo "[ACTION] Please edit .env to add your HF_TOKEN if needed."
fi

# 6. Launch Application
echo "[SUCCESS] Starting Local RAG..."
streamlit run app.py
