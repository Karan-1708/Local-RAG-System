# 🛡️ Local RAG System: Private Technical Q&A

A robust, local-first RAG system for querying confidential technical documents with built-in security, performance optimizations, and comprehensive error handling.

## 🚀 Key Features

- **Local Privacy:** All processing, embeddings, and LLM calls stay on your machine (via Ollama).
- **Security Quarantine:** Scans retrieved document chunks for prompt injection attacks before context injection.
- **Parallel Ingestion:** Multi-threaded document processing for faster indexing.
- **Hybrid Re-ranking:** Uses a Cross-Encoder to refine search results for high accuracy.
- **Robust Error Handling:** Integrated logging system and secure file path validation.
- **OCR Ready:** Automatic text extraction from images and scanned PDFs using Tesseract.

## 🛠️ Setup

1. **Prerequisites:**
   - Python 3.9+
   - [Ollama](https://ollama.com/) (Ensure Llama3:8b is pulled: `ollama pull llama3:8b`)
   - [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) (For image/PDF processing)

2. **Configuration:**
   - Copy `env.template` to `.env`.
   - Update `TESSERACT_CMD` with your local path (e.g., `C:\Program Files\Tesseract-OCR\tesseract.exe`).
   - Adjust model and chunk settings as needed.

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Application:**
   ```bash
   streamlit run app.py
   ```

## 🔒 Security Measures

- **Path Validation:** Prevents directory traversal attacks during file uploads.
- **Injection Defense:** Expanded detection patterns for "Ignore previous instructions" and other common jailbreak attempts.
- **Narrator Defense:** A strict technical-reporter system prompt to minimize hallucination and persona switching.

## 📊 Evaluation

Includes a **Perplexity Metric** (via `distilgpt2`) to measure the confidence and fluency of generated answers.
