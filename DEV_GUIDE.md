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
Run the validator script to ensure your specific hardware (CUDA/MPS) is recognized:
```powershell
python install.py
```

### 3. Environment Configuration
Create a `.env` file from the template and add your credentials:
```powershell
cp env.template .env
```
Key variables:
*   `HF_TOKEN`: Required for faster model downloads from HuggingFace.
*   `TESSERACT_CMD`: Path to your Tesseract executable (for image OCR).

---

## 🏗️ Architecture Overview

The system follows a modular RAG architecture:

### 1. Ingestion Layer (`src/ingestion.py`, `src/chunks.py`)
*   **Loaders:** Uses `Unstructured` to handle mixed file types.
*   **Splitting:** `RecursiveCharacterTextSplitter` ensures semantic coherence.

### 2. Storage Layer (`src/vector_store.py`)
*   **ChromaDB:** Handles high-dimensional vector embeddings.
*   **BM25:** Persists a keyword index for hybrid retrieval.
*   **Persistence:** Session state is saved in `session_state.json`.

### 3. Retrieval Pipeline (`src/retrieval.py`, `src/generation.py`)
*   **Hybrid Search:** Performs parallel Vector + BM25 search.
*   **Fusion:** Uses **Reciprocal Rank Fusion (RRF)** to combine results.
*   **Re-ranking:** Employs a `Cross-Encoder` (`ms-marco-MiniLM-L-6-v2`) to prune irrelevant context.

### 4. Safety & Privacy (`src/privacy.py`)
*   **Redaction:** Microsoft Presidio masks PII before any external API calls or LLM processing.
*   **Injection Guard:** Regex-based scanner in `generation.py` filters malicious document chunks.

---

## 🧪 Development Workflow

### Testing Hardware Acceleration
Run the included check script to verify GPU status:
```powershell
python check_gpu.py
```

### Running the App
```powershell
streamlit run app.py
```

### Contribution Guidelines
1.  **Branching:** Create a feature branch (`feat/your-feature`).
2.  **Linting:** Follow PEP8 standards.
3.  **Efficiency:** Use `@st.cache_resource` for any heavy ML model loading.
4.  **Logging:** Use the unified logger from `src.utils`.
