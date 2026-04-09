# 🛡️ Local RAG: Secure & Private AI Assistant

**Local RAG** is a production-grade, privacy-first Retrieval-Augmented Generation (RAG) system designed to let you chat with your own documents without ever leaking data to the cloud. By combining local LLM orchestration with advanced privacy scrubbing and hardware-aware optimization, it brings the power of frontier AI models directly to your desktop.

---

## 🎯 The Goal

The primary objective of this project is **Data Sovereignty**. In an era where corporate data and personal information are frequently used to train cloud models, Local RAG provides a "Clean Room" environment. 

We aim to bridge the gap between high-performance AI and strict privacy requirements, ensuring that your architecture diagrams, legal contracts, and private codebases remain exclusively on your machine.

---

## ✨ Appealing Features

### 🛡️ Privacy & Security First

- **PII Redaction:** Automatically detects and masks Names, Emails, IP Addresses, and Locations before they reach the LLM.
- **Security Quarantine:** Scans your own documents for "Prompt Injection" patterns to prevent malicious files from hijacking the AI session.
- **100% Local Mode:** Fully compatible with Ollama for a completely air-gapped experience.

### 🚀 Smart Performance

- **Hardware-Aware Installer:** Automatically detects NVIDIA GPUs (CUDA), Apple Silicon (MPS), or Linux environments to install the most optimized version of PyTorch.
- **Hybrid Search:** Combines semantic vector search (ChromaDB) with keyword-based retrieval (BM25) for pinpoint accuracy.
- **Cross-Encoder Re-ranking:** Uses a secondary AI model to re-score results, ensuring only the most relevant context is sent to the LLM.

### 📊 Transparent Reliability

- **Quality Metrics:** Every answer is scored for **Faithfulness** (fact-checking) and **Relevancy**.
- **Confidence Scoring:** Uses **Perplexity** to tell you exactly how "confused" or "confident" the AI is about its response.
- **Verifiable Citations:** See exactly which document and which chunk the AI used to generate its answer.

### 🤖 Hybrid Intelligence

- **Local Inference:** Powered by **Ollama**. Perfect for 100% air-gapped, zero-leakage workflows.
- **Frontier Inference:** Integrated with **OpenAI, Google Gemini, and Anthropic** via secure API for complex reasoning tasks.

### ⚠️ Privacy Disclaimer

While this system includes advanced **PII Redaction**, please note:

- **100% Local Mode:** Only applies when using local **Ollama** models. In this mode, no data ever leaves your hardware.
- **Frontier Mode:** When using external APIs (OpenAI, Gemini, Anthropic), your (redacted) prompts and document context are transmitted to the respective providers. Use these for non-sensitive data or when high-reasoning capabilities are required.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit (Modern, responsive dashboard)
- **Orchestration:** LangChain (State-of-the-art RAG pipeline)
- **Vector DB:** ChromaDB
- **Embeddings:** HuggingFace `all-MiniLM-L6-v2`
- **Privacy Engine:** Microsoft Presidio + Spacy
- **Evaluation:** RAGAS framework + Local Perplexity models

---

## 🚀 Getting Started

- **For Users:** See the [User Guide](./USER_GUIDE.md) for the one-click "No-Code" setup.
- **For Developers:** See the [Developer Guide](./DEV_GUIDE.md) for manual setup and internal architecture.
- **Deep Dive:** See the [Project Documentation](./DOCUMENTATION.md) for a full technical analysis of the codebase.

