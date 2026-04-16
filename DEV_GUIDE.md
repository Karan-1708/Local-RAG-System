# 💻 Developer Guide: Manual Setup & Architecture

This guide is for developers who want to inspect the codebase, run manual tests, or contribute to the project.

---

## 🛠️ Manual Environment Setup

If you prefer not to use the `.bat`/`.sh` launchers, follow these steps:

### 1. Initialize Virtual Environment
```powershell
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate
```

### 2. Smart Dependency Installation
Run the validator script to ensure your specific hardware (CUDA/MPS) is recognized and optimized:
```powershell
python install.py
```

### 3. Environment Configuration
Create a `.env` file from the example and add your credentials:
```powershell
cp .env.example .env
```
Key variables:
*   `INTERNAL_API_KEY`: Secret key required to access the REST API endpoints.
*   `TESSERACT_CMD`: Absolute path to your Tesseract executable.

---

## ⚡ REST API Standards

The project includes a high-performance **FastAPI** backend that follows industry standards.

### Swagger Documentation
Once the server is running, navigate to:
`http://localhost:8000/docs`
This provides an interactive UI to test the RAG pipeline programmatically.

### Security (X-API-Key)
All programmatic requests to `/api/v1/query` must include the following header:
`X-API-Key: <your_internal_api_key>`

---

## 🏗️ Architecture Overview

### 1. Unified Generation Factory (`src/generation.py`)
*   Supports **Ollama**, **OpenAI**, **Gemini**, and **Anthropic** via a single `get_llm` interface.
*   Implements **Streaming Generators** for real-time visual feedback.

### 2. Conversational Memory
*   State is managed in `app.py` and persisted in `session_state.json`.
*   The last 5 message exchanges are injected into the RAG system prompt for context-aware follow-up.

### 3. Multi-Provider Evaluation (`src/evaluation.py`)
*   Powered by **RAGAS**.
*   Dynamically selects the evaluation model to match the generation provider (e.g., uses Claude to grade Claude).

---

## 🐳 Docker Deployment

To run the full suite (Frontend + Backend) in an isolated container:

```bash
docker-compose up --build
```
*   **Persistent Volumes:** Uploaded files and database indexes are saved to your local disk, so they survive container restarts.
*   **Host Communication:** The container is configured to talk to your host's Ollama instance via `host.docker.internal`.

---

## 🧪 Development Workflow

### Testing Hardware Acceleration
```powershell
python check_gpu.py
```

### Running the Full Suite Manually
```powershell
# Terminal 1: Backend
uvicorn api:app --host 0.0.0.0 --port 8000
# Terminal 2: Frontend
streamlit run app.py
```
