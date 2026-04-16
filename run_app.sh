#!/bin/bash

echo "🛡️ Local RAG System: Starter"
echo "-----------------------------------"

# 1. Validate Python Version (3.11 - 3.13)
PYTHON_CMD="python3"
if ! command -v $PYTHON_CMD &> /dev/null; then
    PYTHON_CMD="python"
fi

VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
MAJOR=$(echo $VERSION | cut -d. -f1)
MINOR=$(echo $VERSION | cut -d. -f2)

VALID=0
if [ "$MAJOR" == "3" ] && [ "$MINOR" -ge 11 ] && [ "$MINOR" -le 13 ]; then
    VALID=1
fi

if [ "$VALID" == "0" ]; then
    echo "[WARNING] Current Python ($VERSION) is not supported (Requires 3.11 - 3.13)."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "[INFO] Attempting to install Python 3.12 via Homebrew..."
        brew install python@3.12
    else
        echo "[INFO] Attempting to install Python 3.12 via apt..."
        sudo apt-get update && sudo apt-get install -y python3.12 python3.12-venv
    fi
    
    if [ $? -ne 0 ]; then
        echo "[ERROR] Automated installation failed. Please install Python 3.12 manually."
        exit 1
    fi
    echo "[SUCCESS] Python 3.12 installed. Please restart this script."
    exit 0
fi

# 2. Discover Virtual Environments
echo "[INFO] Scanning for virtual environments..."
ENVS=($(find . -maxdepth 1 -type d -name ".*venv*"))
TARGET_ENV=".venv"

if [ ${#ENVS[@]} -gt 0 ]; then
    echo "[INFO] Found existing environment(s): ${ENVS[*]}"
    echo
    echo "1. Use existing [${ENVS[0]}]"
    echo "2. Create a new environment alongside"
    echo "3. Exit"
    echo
    read -p "Select an option (1-3): " CHOICE
    
    if [ "$CHOICE" == "1" ]; then
        TARGET_ENV="${ENVS[0]}"
    elif [ "$CHOICE" == "2" ]; then
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        TARGET_ENV=".venv_$TIMESTAMP"
        echo "[INFO] Creating new environment: $TARGET_ENV..."
        $PYTHON_CMD -m venv $TARGET_ENV
    else
        exit 0
    fi
else
    echo "[INFO] No environment found. Creating standard .venv..."
    $PYTHON_CMD -m venv .venv
fi

# 3. Activate Environment
echo "[INFO] Activating environment: $TARGET_ENV..."
source $TARGET_ENV/bin/activate

# 4. Run Smart Installer
if [ ! -f "$TARGET_ENV/installed.flag" ]; then
    echo "[INFO] Installing/Optimizing dependencies..."
    python3 install.py
    if [ $? -eq 0 ]; then
        echo "Done" > "$TARGET_ENV/installed.flag"
    else
        echo "[ERROR] Installation failed."
        exit 1
    fi
fi

# 5. Setup .env
if [ ! -f ".env" ]; then
    echo "[INFO] Creating .env from example..."
    cp .env.example .env
fi

# 6. Launch
echo "[SUCCESS] Starting Local RAG Suite..."
echo "[INFO] Launching API Server (Swagger at http://localhost:8000/docs)..."
uvicorn api:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &

echo "[INFO] Launching Streamlit UI..."
streamlit run app.py
