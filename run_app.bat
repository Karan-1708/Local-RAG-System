@echo off
TITLE Local RAG System
echo ===================================================
echo   Local RAG System - Startup
echo ===================================================

:: 1. Run Setup/Install logic (handles venv, packages, .env)
python install.py
if %errorlevel% neq 0 (
    echo [ERROR] Setup failed. Please check the logs above.
    pause
    exit /b
)

:: 2. Launch API backend in a new window
echo.
echo [3/4] Starting API backend...
start "Local RAG - API" cmd /k "call .venv\Scripts\activate.bat && python -m uvicorn api:app --host 0.0.0.0 --port 8000"

:: 3. Wait for backend to initialise
echo [INFO] Waiting for backend to start...
timeout /t 5 /nobreak >nul

:: 4. Launch Streamlit frontend
echo.
echo [4/4] Launching dashboard...
echo [INFO] Opening Local RAG System in your browser...
call .venv\Scripts\activate.bat && streamlit run app.py

echo.
echo [INFO] Application closed.
pause
