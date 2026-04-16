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
- **Internal API Key:** Protects the REST API backend from unauthorized access with header-based authentication.
- **100% Local Mode:** Fully compatible with Ollama for a completely air-gapped experience.

### 🚀 Smart Performance

- **Hardware-Aware Installer:** Automatically detects NVIDIA GPUs (CUDA), Apple Silicon (MPS), or Linux environments to install the most optimized version of PyTorch.
- **Streaming Generation:** Real-time answer rendering with a live typing effect for immediate feedback.
- **Hybrid Search:** Combines semantic vector search (ChromaDB) with keyword-based retrieval (BM25) for pinpoint accuracy.
- **Cross-Encoder Re-ranking:** Uses a secondary AI model to re-score results, ensuring only the most relevant context is sent to the LLM.

### 📊 Transparent Reliability

- **Multi-Chat Management:** Organize, rename, and pin up to 3 important conversations.
- **Professional PDF Export:** Generate clean, formatted technical reports of your chats.
- **Quality Metrics:** Every answer is scored for **Faithfulness** (fact-checking) and **Relevancy** using the RAGAS framework.
- **Verifiable Citations:** Interactive expanders showing exactly which document snippet the AI used.

### 🤖 Hybrid Intelligence

- **Local Inference:** Powered by **Ollama**. Supports Llama 3.1, Phi-3, Mistral, and more.
- **Frontier Inference:** Integrated with **OpenAI, Google Gemini, and Anthropic** via secure API.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit (Modern, responsive dashboard)
- **Backend API:** FastAPI (Standardized REST interface with Swagger docs)
- **Containerization:** Docker & Docker Compose (Persistent volumes & isolated environment)
- **Orchestration:** LangChain (State-of-the-art RAG pipeline)
- **Vector DB:** ChromaDB
- **Privacy Engine:** Microsoft Presidio + Spacy
- **Evaluation:** RAGAS framework + Local Perplexity models

---

## 🐳 Docker Deployment

The fastest way to get started with the full suite is using Docker:

```powershell
docker-compose up --build
```
- **UI:** `http://localhost:8501`
- **REST API:** `http://localhost:8000/docs`

---

## 🚀 Getting Started

- **For Users:** See the [User Guide](./USER_GUIDE.md) for the one-click "No-Code" setup and drag-and-drop features.
- **For Developers:** See the [Developer Guide](./DEV_GUIDE.md) for manual setup and REST API details.
- **Deep Dive:** See the [Project Documentation](./DOCUMENTATION.md) for a full technical analysis of the codebase.
