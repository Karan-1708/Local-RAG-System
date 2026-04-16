@echo off
SETLOCAL EnableDelayedExpansion

echo 🛡️ Local RAG System: Starter
echo -----------------------------------

:: 1. Validate Python Version (3.11 - 3.13)
set "MIN_VER=11"
set "MAX_VER=13"

for /f "tokens=2 delims= " %%a in ('python --version 2^>^&1') do (
    for /f "tokens=1,2 delims=." %%b in ("%%a") do (
        set "MAJOR=%%b"
        set "MINOR=%%c"
    )
)

set "VALID=0"
if "!MAJOR!"=="3" (
    if !MINOR! GEQ %MIN_VER% if !MINOR! LEQ %MAX_VER% set "VALID=1"
)

if "!VALID!"=="0" (
    echo [WARNING] Current Python (!MAJOR!.!MINOR!) is not supported (Requires 3.11 - 3.13).
    echo [INFO] Attempting to install Python 3.12 via winget...
    winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo [ERROR] Automated installation failed. Please install Python 3.12 manually from python.org.
        pause
        exit /b
    )
    echo [SUCCESS] Python 3.12 installed. Please restart this script.
    pause
    exit /b
)

:: 2. Discover Virtual Environments
echo [INFO] Scanning for virtual environments...
set "ENV_COUNT=0"
set "ENVS="

for /d %%d in (.*venv*) do (
    if exist "%%d\Scripts\activate.bat" (
        set /a ENV_COUNT+=1
        set "ENV_!ENV_COUNT!=%%d"
        set "ENVS=!ENVS! %%d"
    )
)

set "TARGET_ENV=.venv"

if %ENV_COUNT% GTR 0 (
    echo [INFO] Found existing environment(s):!ENVS!
    echo.
    echo 1. Use existing [!ENV_1!]
    echo 2. Create a new environment alongside
    echo 3. Exit
    echo.
    set /p "CHOICE=Select an option (1-3): "
    
    if "!CHOICE!"=="1" (
        set "TARGET_ENV=!ENV_1!"
    ) else if "!CHOICE!"=="2" (
        set "TIMESTAMP=%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%"
        set "TARGET_ENV=.venv_!TIMESTAMP: =0!"
        echo [INFO] Creating new environment: !TARGET_ENV!...
        python -m venv !TARGET_ENV!
    ) else (
        exit /b
    )
) else (
    echo [INFO] No environment found. Creating standard .venv...
    python -m venv .venv
)

:: 3. Activate Environment
echo [INFO] Activating environment: !TARGET_ENV!...
call !TARGET_ENV!\Scripts\activate

:: 4. Run Smart Installer
if not exist "!TARGET_ENV!\installed.flag" (
    echo [INFO] Installing/Optimizing dependencies...
    python install.py
    if %errorlevel% equ 0 (
        echo Done > "!TARGET_ENV!\installed.flag"
    ) else (
        echo [ERROR] Installation failed.
        pause
        exit /b
    )
)

:: 5. Setup .env
if not exist ".env" (
    echo [INFO] Creating .env from example...
    copy .env.example .env
)

:: 6. Launch
echo [SUCCESS] Starting Local RAG Suite...
echo [INFO] Launching API Server (Swagger at http://localhost:8000/docs)...
start /b uvicorn api:app --host 0.0.0.0 --port 8000 > api.log 2>&1

echo [INFO] Launching Streamlit UI...
streamlit run app.py

pause
