# 🛡️ Secure Local RAG System

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![AI Model](https://img.shields.io/badge/Model-Llama3-orange)
![Security](https://img.shields.io/badge/Security-Defense%20in%20Depth-red)
![Status](https://img.shields.io/badge/Status-InDevelopment-red)

## 📖 Overview

The **Secure Local RAG System** is an enterprise-grade, privacy-first implementation of Retrieval-Augmented Generation (RAG). Unlike standard RAG systems that rely on external APIs (like OpenAI), this project runs **100% locally** on your hardware, ensuring that sensitive data never leaves your network.

It features a **Defense-in-Depth** security architecture designed to detect and neutralize "Prompt Injection" attacks, making it suitable for analyzing untrusted documents in secure environments.

---

## 🚀 Key Features

### 🔒 Privacy & Security
- **Fully Offline:** Powered by **Ollama (Llama 3)** and local embeddings (`all-MiniLM-L6-v2`). No internet connection required for inference.
- **Defense-in-Depth Architecture:**
  - **Layer 1 (Sanitization):** Regex-based filtering of known attack patterns.
  - **Layer 2 (Quarantine):** Per-chunk scanning to discard malicious segments before they reach the context window.
  - **Layer 3 (AI Guardrail):** A dedicated "Chain-of-Thought" security model that analyzes intent before generating answers.
  - **Layer 4 (Narrator Defense):** System prompts that force a neutral, third-person perspective to resist persona adoption attacks.

### 🧠 Advanced RAG Pipeline
- **Multi-Modal Ingestion:** Supports **PDFs** and **Images** (via Tesseract OCR).
- **Hybrid Search:** Combines vector similarity search with keyword matching.
- **Re-Ranking:** Uses a Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) to re-score retrieved documents, ensuring high precision.
- **Confidence Metrics:** Calculates Perplexity scores for every response to gauge hallucination risk.

### 💻 Hardware Agnostic
- **Universal Compatibility:** Runs on Windows, Linux, and macOS.
- **Optimized Inference:** Supports NVIDIA GPUs (CUDA), Apple Silicon (Metal), and CPU-only fallback.

---

## 🏗️ Architecture

The system follows a modular ETL (Extract, Transform, Load) pipeline:

1.  **Ingestion:** Documents (PDF/Images) are processed into raw text.
2.  **Chunking:** Text is split into semantic chunks with overlap.
3.  **Vector Store:** Chunks are embedded and stored in **ChromaDB** (persistent local storage).
4.  **Retrieval:** Top-k relevant chunks are fetched based on user query.
5.  **Re-Ranking:** A Cross-Encoder model refines the selection.
6.  **Security Scan:** Selected chunks pass through the Quarantine and Guardrail layers.
7.  **Generation:** Safe context is passed to **Llama 3** for final answer synthesis.

---

## 🛠️ Installation

### Prerequisites
1.  **Python 3.10+**
2.  **Ollama:** Download and install from [ollama.com](https://ollama.com).
3.  **Tesseract OCR:**
    - *Windows:* [Install Installer](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.
    - *Mac:* `brew install tesseract`
    - *Linux:* `sudo apt install tesseract-ocr`

### Setup Steps

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/Secure-Local-RAG.git](https://github.com/YOUR_USERNAME/Secure-Local-RAG.git)
    cd Local-RAG-System
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Pull the AI Models**
    Run this in your terminal to download the Llama 3 model locally:
    ```bash
    ollama pull llama3
    ```

---

## ▶️ Usage

1.  **Start the Application**
    ```bash
    streamlit run app.py
    ```

2.  **Workflow**
    - **Upload:** Drag and drop PDF or Image files in the sidebar.
    - **Process:** Click "Process Documents" to ingest and embed data.
    - **Ask:** Chat with your documents in the main window.
    - **Reset:** Use the "Reset System" button to wipe the database memory.

---

## 📊 Evaluation & Performance

The system includes a built-in evaluation module that calculates the **Perplexity** of the generated response.

- **Low Score (< 30):** High confidence, fluent response.
- **High Score (> 100):** Robotic or uncertain response (often triggered by security protocols).

---

## 🤝 Contributing

This is a College project. Contributions, issues, and feature requests are welcome!

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

## 📄 License

Distributed under the PolyForm Noncommercial License 1.0.0. See `LICENSE` for more information.

---

**Built with 💙 using Streamlit, LangChain, and Ollama.**
