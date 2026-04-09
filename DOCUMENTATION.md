# Developer Documentation: Local RAG Technical Reference

## 📂 1. Project Structure & File Manifest

### Root Directory
- `app.py`: Entry point. Streamlit UI orchestration, session state management, and async streaming logic.
- `install.py`: Comprehensive system validator. Detects OS/Hardware/Python versions. Installs grouped dependencies and handles hardware-specific PyTorch logic.
- `config.py`: Central constant repository. Loads `.env` and defines directory paths, model names, and RAG hyperparameters.
- `run_app.bat` / `run_app.sh`: Wrapper scripts for venv initialization and app launch.
- `check_gpu.py`: Diagnostic script for PyTorch/CUDA availability.
- `requirements.txt`: Static dependency list (hardware-independent packages).
- `session_state.json`: Local persistence for chat history, pinned status, and API keys.

### Source Directory (`src/`)
- `ingestion.py`: Document extraction using `Unstructured`. Handles PDF, DOCX, TXT, CSV, MD, PNG, JPG.
- `chunks.py`: Text segmentation using `RecursiveCharacterTextSplitter`. Defaults: 1000 size, 200 overlap.
- `vector_store.py`: ChromaDB wrapper. Implements `delete_document` (mapping metadata source to IDs) and additive `save_to_chroma`.
- `retrieval.py`: Initializes `BM25Retriever` from serialized corpus.
- `generation.py`: Pipeline orchestration. Implements PII redaction, Hybrid Search, RRF fusion, Cross-Encoder re-ranking, and LLM streaming.
- `privacy.py`: Microsoft Presidio integration. Cached singleton initialization for `AnalyzerEngine` and `AnonymizerEngine`.
- `evaluation.py`: RAGAS and Perplexity scoring. Logic for moving tensors to GPU (`.to(device)`) for local scoring.
- `utils.py`: Logging configuration, hardware detection (`get_device`), and path traversal protection.
- `ollama_utils.py`: REST API interaction with Ollama (model pulls, status checks).
- `api_config.py`: Hardcoded model lists and key URLs for OpenAI, Gemini, and Anthropic.
- `prompts.py`: System prompt templates for RAG context injection.

---

## ⚙️ 2. Environment Variables (`.env`)
| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `HF_TOKEN` | None | HuggingFace Hub authentication for model downloads. |
| `TESSERACT_CMD` | System Path | Absolute path to `tesseract.exe` for OCR. |
| `LLM_MODEL` | `llama3:8b` | Default Ollama model name. |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | HuggingFace embedding model ID. |
| `CHUNK_SIZE` | `1000` | Token/Char count per chunk. |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks for context preservation. |
| `RETRIEVAL_K` | `5` | Number of final context chunks sent to LLM. |
| `SIMILARITY_THRESHOLD` | `0.6` | Cutoff for relevant vs irrelevant documents. |

---

## 🔄 3. Retrieval & Generation Pipeline

### 3.1 Hybrid Search Mechanics
1.  **Vector Search:** `Chroma.similarity_search_with_score` (K*2 results).
2.  **Keyword Search:** `BM25Retriever` (K*2 results).
3.  **Fusion (RRF):** Results are merged using Reciprocal Rank Fusion.
    - Formula: `Score(d) = Σ (1 / (60 + rank(d)))`
4.  **Re-ranking:** Top fused results are processed by `CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')`.
    - Pairs: `[Query, Chunk_Content]`
    - Sorting: Descending order based on Cross-Encoder logit score.

### 3.2 Security Quarantine
Before context injection, every chunk is scanned against a list of 15+ regex patterns (e.g., `system override`, `ignore previous instructions`, `administrative session`) to detect prompt injection attempts within documents.

### 3.3 Privacy Scrubbing
- **Analyzer:** Detects `PERSON`, `EMAIL_ADDRESS`, `PHONE_NUMBER`, `LOCATION`, `IP_ADDRESS`.
- **Anonymizer:** Replaces detected entities with generic placeholders (e.g., `<PERSON>`).
- **Timing:** Scrubbing occurs on the user query *before* retrieval and the final answer *after* generation.

---

## 🖥️ 4. Hardware Optimization Logic

### Device Selection Hierarchy
1.  `cuda`: If `torch.cuda.is_available()` is True.
2.  `mps`: If `torch.backends.mps.is_available()` is True (Apple Silicon).
3.  `cpu`: Fallback for all other systems.

### Installation Strategy (`install.py`)
- **Clean Install:** Uninstalls `torch`, `torchvision`, `torchaudio` if a GPU is detected to prevent CPU-build conflicts.
- **CUDA Target:** Installs with `--index-url https://download.pytorch.org/whl/cu124` for NVIDIA RTX 30/40 series compatibility.
- **Numpy Pinning:**
    - Python < 3.12: `numpy<2.0.0`
    - Python >= 3.12: `numpy<=2.3.0`
- **Transformers Pinning:** `transformers<5.0.0` to avoid dynamic module loading warnings and `__path__` errors.

---

## 📊 5. Evaluation Metrics

### RAGAS Metrics
- **Faithfulness:** `Faithfulness()`. Measures if the answer can be derived solely from the retrieved context.
- **Answer Relevancy:** `AnswerRelevancy()`. Measures how well the answer addresses the specific user prompt.
- **Cliping:** Values are clipped to `[0.0, 1.0]` using `max(0.0, score)` to prevent negative display artifacts from cosine similarity math.

### Local Fluency (Perplexity)
- **Model:** `distilgpt2` (approx. 82M parameters).
- **Math:** `exp(loss)` where loss is the cross-entropy of the generated text against the evaluator model.
- **Qualitative Mapping:**
    - `<= 20`: Excellent
    - `<= 50`: Good
    - `<= 100`: Okay
    - `> 100`: Confused

---

## 💾 6. Data Storage & State

### Session State (`session_state.json`)
```json
{
  "active_chat_id": "uuid-string",
  "api_keys": { "OpenAI": "sk-...", "Anthropic": "..." },
  "chats": {
    "uuid-string": {
      "name": "Chat Title",
      "messages": [
        { "role": "user", "content": "..." },
        { "role": "assistant", "content": "...", "metrics": "...", "citations": [] }
      ],
      "pinned": false,
      "enable_ragas": false,
      "created_at": "iso-timestamp"
    }
  }
}
```

### Knowledge Base
- **Raw Files:** Stored in `data/raw/`.
- **Vector DB:** ChromaDB persisted in `chroma_db/` using Parquet files.
- **BM25 Corpus:** Pickled list of `Document` objects stored as `chroma_db/bm25_corpus.pkl`.

---

## 🤖 7. Hybrid Inference Strategy

### 7.1 Local Inference (Zero Leakage)
- **Engine:** Ollama (Local REST API).
- **Security:** In this mode, document chunks and user prompts are processed entirely on the local CPU/GPU. No data is transmitted over the internet.
- **Ideal Use Case:** Highly sensitive proprietary documents, legal contracts, private codebases.

### 7.2 Frontier Inference (Hybrid Privacy)
- **Engine:** OpenAI (GPT-4o), Google (Gemini 1.5 Pro), Anthropic (Claude 3.5 Sonnet).
- **Logic:** The system applies **PII Redaction** first, then transmits the redacted prompt and context chunks to the cloud provider via SSL-encrypted API.
- **Privacy Disclaimer:** Please note that while PII (names, emails, etc.) is masked, the **technical context and conceptual data** within your documents still reach third-party servers. 100% data sovereignty is **not** guaranteed in Frontier Mode.
- **Ideal Use Case:** Complex reasoning tasks, cross-lingual analysis, or when local hardware performance is insufficient.

