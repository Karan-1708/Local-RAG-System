# Developer Documentation: Local RAG Technical Reference

## 📂 1. Project Structure & File Manifest

### Root Directory
- `app.py`: Entry point. Streamlit UI orchestration, session state management, and async streaming logic.
- `api.py`: FastAPI backend providing a secure REST API and interactive Swagger UI.
- `Dockerfile` & `docker-compose.yml`: Containerization configuration with persistent volumes.
- `install.py`: Comprehensive system validator. Detects OS/Hardware/Python versions. Handles hardware-specific PyTorch logic and resource checks (RAM/Disk/VRAM).
- `config.py`: Central constant repository. Loads `.env` and defines directory paths, model names, and strict security validation for the internal API key.
- `run_app.bat` / `run_app.sh`: Wrapper scripts with Python version management and virtual environment selection.
- `.env.example`: Template for environment configuration.
- `session_state.json`: Local persistence for multiple chats, pinned status, API keys, and per-chat evaluation settings.

### Source Directory (`src/`)
- `ingestion.py`: Document extraction using `Unstructured`. Supports PDF, DOCX, TXT, CSV, MD, PNG, JPG.
- `chunks.py`: Text segmentation using `RecursiveCharacterTextSplitter`.
- `vector_store.py`: ChromaDB and BM25 wrapper. Implements secure `reset_database` which wipes physical data files.
- `generation.py`: Multi-provider LLM factory. Implements Hybrid Search, RRF fusion, Cross-Encoder re-ranking, and **Streaming Generators**.
- `ollama_utils.py`: Logic for model management, pulls, and live connectivity health checks (`is_ollama_running`).
- `evaluation.py`: RAGAS and Perplexity scoring. Dynamically switches the scoring model to match the generation provider.
- `api_config.py`: Configuration for Frontier API models and key management URLs.
- `utils.py`: Core helpers for hardware detection (`get_hardware_info`), secure path handling, and directory clearing.

---

## 🔄 2. Data Flow & Pipeline

### 2.1 Conversational Memory
The system maintains context across exchanges. 
1. `app.py` collects the chat history from the active session.
2. The last 5 turns are passed to `query_rag`.
3. `generation.py` formats these turns into the system prompt under the `CHAT HISTORY` section.

### 2.2 Security Quarantine
Before context injection, every chunk is scanned against a list of 20+ regex patterns to detect prompt injection attempts within documents. If a chunk matches, it is **blocked** and never reaches the LLM.

### 2.3 Local-First Privacy
1. **Redaction:** PII is scrubbed locally using Microsoft Presidio before indexing and before querying Frontier APIs.
2. **Offline Guard:** `config.py` supports `HF_HUB_OFFLINE=1` to prevent any phone-home behavior from Transformers.

---

## 🖥️ 3. Hardware Optimization

### Enhanced Reporting
The system uses `get_hardware_info()` to provide a descriptive status in the UI:
- **NVIDIA:** `🚀 NVIDIA GPU (Model Name)`
- **Apple:** `🍎 Apple Silicon (Metal)`
- **CPU:** `💻 Standard CPU`

### Intelligent Setup (`install.py`)
- Automatically detects Python **3.11 - 3.13**.
- Performs a clean uninstallation of `torch` to ensure no build conflicts.
- Installs `cu124` optimized wheels for modern NVIDIA hardware.

---

## 📊 4. Evaluation & Metrics

### RAGAS Integration
- **Faithfulness:** Derives accuracy from retrieved context.
- **Answer Relevancy:** Measures alignment with the user's prompt.
- **Provider Parity:** If the user is on OpenAI, RAGAS uses OpenAI for scoring to ensure high-fidelity evaluation.

### Local Perplexity
- Uses `distilgpt2` to measure answer fluency.
- Lower score = more coherent and confident response.
