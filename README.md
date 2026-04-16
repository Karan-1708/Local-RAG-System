# 🛡️ Local RAG System

**Local RAG** is a production-grade, privacy-first Retrieval-Augmented Generation system that lets you chat with your own documents — completely on your machine. No data leaves your network unless you explicitly choose a cloud provider.

It combines a **hybrid search pipeline** (ChromaDB vector search + BM25 keyword retrieval), **automatic PII scrubbing**, **prompt injection quarantine**, and support for both local Ollama models and frontier cloud APIs — all behind a clean Streamlit dashboard and a secured FastAPI backend.

---

## What makes it different

Most RAG demos send your documents and queries straight to a cloud API. Local RAG treats privacy as a pipeline stage, not an afterthought:

- Every document is **PII-redacted before indexing** — names, emails, phone numbers, IPs, and locations are masked before anything is written to the vector store.
- Every retrieved chunk is **scanned for prompt injection** before being placed in the LLM context window.
- Every user query is **redacted again at query time**, so even cloud providers never see raw personal data.
- In fully local mode (Ollama), **nothing leaves the machine at all**.

---

## Features

### Privacy & Security
- Automatic PII detection and masking via **Microsoft Presidio** (Names, Emails, Phone Numbers, Locations, IPs)
- Document **Security Quarantine** — 13 regex patterns block prompt injection attempts embedded in uploaded files
- **Path traversal protection** on all file uploads (`Path.is_relative_to()` enforcement)
- Internal API key authentication on all REST endpoints (`X-API-Key` header)
- Narrator Defense prompt architecture — the LLM is instructed to treat `<DATA_BLOCK>` content as untrusted data

### Retrieval Pipeline
- **Hybrid Search** — semantic vector search (ChromaDB + `all-MiniLM-L6-v2`) combined with keyword search (BM25)
- **Reciprocal Rank Fusion** — merges both result lists into a unified ranking without requiring score normalization
- **Cross-Encoder Re-ranking** — `cross-encoder/ms-marco-MiniLM-L-6-v2` re-scores shortlisted chunks for maximum relevance precision

### Document Support
| Format | Method |
|---|---|
| PDF (text-based) | pdfminer.six, page-by-page |
| PDF (scanned / image-based) | pdf2image + Tesseract OCR fallback |
| DOCX / DOC | python-docx |
| CSV / XLSX | pandas |
| PNG, JPG, BMP, TIFF | Pillow + Tesseract OCR |
| TXT, MD, HTML | Python built-in |

### LLM Providers
| Provider | Models |
|---|---|
| **Ollama** (local) | Any model pulled locally: Llama 3, Phi-3, Mistral, Gemma, etc. |
| **OpenAI** | gpt-5.4-nano, gpt-5-nano, o4-mini, gpt-4o-mini |
| **Google Gemini** | gemini-3-flash-preview, gemini-3.1-flash-lite-preview, gemini-2.5-flash-lite |
| **Anthropic** | claude-sonnet-4-6, claude-haiku-4-5, claude-sonnet-4-5, claude-sonnet-4-0 |

### Quality & Transparency
- **Perplexity scoring** on every answer (gpt2, stride-based sliding window, runs locally, no API cost)
- **RAGAS evaluation** (optional per-chat toggle) — Faithfulness and Answer Relevancy using a fast variant of the active provider (e.g., `gpt-4o-mini` for OpenAI, `claude-haiku-4-5` for Anthropic)
- **Verifiable citations** — every answer includes the source filename and a snippet of the exact chunk used
- **PDF export** — download any conversation as a formatted report

### User Experience
- Real-time **streaming output** with live token display
- **Multi-chat management** — create, rename, pin (up to 3), and delete conversations
- **Per-chat document isolation** — documents uploaded in one chat are never visible in another
- Chat history **persisted to disk** (`session_state.json`) — survives page refreshes and restarts
- Per-conversation RAGAS toggle
- Cross-platform folder shortcuts (📁 Uploads, 🗄️ Database)
- Two-step confirmation for destructive actions (Full Reset)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend API | FastAPI + Uvicorn |
| Orchestration | LangChain (langchain-chroma, langchain-ollama, langchain-openai, langchain-google-genai, langchain-anthropic) |
| Vector Database | ChromaDB |
| Keyword Search | BM25 (langchain-community) |
| Embeddings | HuggingFace sentence-transformers (`all-MiniLM-L6-v2`) |
| Re-ranking | sentence-transformers CrossEncoder (`ms-marco-MiniLM-L-6-v2`) |
| Privacy Engine | Microsoft Presidio + spaCy `en_core_web_sm` |
| OCR | Tesseract + pytesseract + pdf2image |
| Evaluation | RAGAS + gpt2 (stride-based perplexity) |
| PDF Generation | FPDF2 |
| Containerization | Docker + Docker Compose |

---

## Getting Started

| Audience | Guide |
|---|---|
| End users (no coding required) | [User Guide](./USER_GUIDE.md) |
| Developers & contributors | [Developer Guide](./DEV_GUIDE.md) |
| Full technical reference | [Documentation](./DOCUMENTATION.md) |

---

## Quick Start (one command)

**Windows:**
```bat
run_app.bat
```

**Mac / Linux:**
```bash
bash run_app.sh
```

The launcher will:
1. Verify Python 3.11+ (offer to install if missing on Mac/Linux)
2. Detect existing virtual environments or create `.venv`
3. Install all dependencies with the correct PyTorch build for your hardware (CUDA 12.4, CUDA 12.1, MPS, or CPU)
4. Download the spaCy language model
5. Generate a `.env` file with a secure `INTERNAL_API_KEY` if one doesn't exist
6. Start the FastAPI backend on `http://localhost:8000`
7. Open the Streamlit dashboard on `http://localhost:8501`

---

## Docker Deployment

```bash
docker-compose up --build
```

- **Dashboard:** `http://localhost:8501`
- **API + Swagger:** `http://localhost:8000/docs`

Uploaded files and the ChromaDB index are mounted as persistent volumes, surviving container restarts.

---

## Project Layout

```
Local-RAG-System/
│
├── api/                        # FastAPI backend package
│   ├── __init__.py
│   └── main.py                 # REST API, security, lifespan startup hook
│
├── ui/                         # Streamlit frontend package
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   ├── state.py                # Session state, load/save persistence
│   ├── sidebar.py              # Sidebar: chats, engine, eval, KB, storage
│   ├── chat.py                 # Chat history rendering + streaming input
│   ├── uploader.py             # File upload widget + ingestion trigger
│   └── pdf_export.py           # PDF report generation (FPDF2)
│
├── src/                        # Core RAG pipeline
│   ├── ingestion.py            # Multi-format document extraction
│   ├── chunks.py               # RecursiveCharacterTextSplitter
│   ├── embeddings.py           # HuggingFace embedding model
│   ├── vector_store.py         # ChromaDB + BM25 index management
│   ├── retrieval.py            # BM25 corpus loader
│   ├── generation.py           # Full RAG pipeline: query_rag()
│   ├── privacy.py              # Microsoft Presidio PII redaction
│   ├── evaluation.py           # RAGAS + perplexity scoring
│   ├── ollama_utils.py         # Ollama model listing, pulling, health check
│   ├── api_config.py           # Frontier provider model lists
│   ├── prompts.py              # LLM system prompt (Narrator Defense)
│   └── utils.py                # Logging, hardware detection, path safety
│
├── data/raw/{chat_id}/         # Per-chat uploaded documents (auto-created)
├── chroma_db/                  # Vector store + per-chat BM25 pickles (auto-created)
│
├── install.py                  # Hardware-aware installer
├── config.py                   # Central config + .env loader
├── run_app.bat                 # Windows launcher
├── run_app.sh                  # Mac/Linux launcher
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── session_state.json          # Persisted chat sessions (auto-generated)
├── Dockerfile
└── docker-compose.yml
```

---

## Prerequisites

- **Python 3.11, 3.12, or 3.13**
- **Ollama** (optional, required only for local inference) — [ollama.com](https://ollama.com)
- **Tesseract OCR** (optional, required only for scanned PDFs and image files) — [Installation guide](https://github.com/UB-Mannheim/tesseract/wiki)
- An API key from OpenAI, Google, or Anthropic if using cloud providers
