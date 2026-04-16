# User Guide

Welcome to Local RAG — a private AI assistant that reads your own documents and answers questions about them. Your files never leave your computer in local mode.

This guide requires no coding knowledge. Just follow the steps in order.

---

## Table of Contents

1. [Before You Start](#1-before-you-start)
2. [One-Click Setup](#2-one-click-setup)
3. [First Launch](#3-first-launch)
4. [Uploading Documents](#4-uploading-documents)
5. [Chatting with Your Documents](#5-chatting-with-your-documents)
6. [Choosing an AI Model](#6-choosing-an-ai-model)
7. [Managing Conversations](#7-managing-conversations)
8. [Exporting a Conversation](#8-exporting-a-conversation)
9. [Managing Your Knowledge Base](#9-managing-your-knowledge-base)
10. [Understanding Metrics & Citations](#10-understanding-metrics--citations)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Before You Start

You need two things installed before running Local RAG.

### Python 3.11, 3.12, or 3.13

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download the latest **Python 3.12** installer for your operating system
3. **Windows users:** on the first screen of the installer, check the box that says **"Add Python to PATH"** before clicking Install

To verify: open a terminal and type `python --version`. You should see `Python 3.12.x` (or similar).

### Ollama (for local AI — recommended)

Ollama runs AI models entirely on your computer. No API key needed, no data sent anywhere.

1. Go to [ollama.com](https://ollama.com) and download the installer for your OS
2. Install and launch it — you should see the Ollama icon in your system tray
3. Open a terminal and run: `ollama pull llama3:8b`
   This downloads the Llama 3 model (~5GB). You only need to do this once.

> **No GPU?** Ollama works on CPU too. Responses will be slower but the system is fully functional.

### Tesseract OCR (optional — for scanned PDFs and images)

Only needed if you plan to upload **scanned PDFs** (image-based PDFs), **photos of documents**, or **image files** (PNG, JPG).

- **Windows:** Download the installer from [github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki). During installation, note the install path (e.g., `C:\Program Files\Tesseract-OCR\`). You will need to add this path to your `.env` file (the setup process will guide you).
- **Mac:** `brew install tesseract`
- **Linux (Ubuntu/Debian):** `sudo apt-get install tesseract-ocr`

---

## 2. One-Click Setup

### Windows

Double-click the file named **`run_app.bat`** in the project folder.

### Mac / Linux

Open a terminal in the project folder and run:
```bash
bash run_app.sh
```

### What happens automatically

A terminal window will open and walk through the setup:

| Step | What it does |
|---|---|
| Python check | Confirms Python 3.11+ is available |
| Virtual environment | Detects existing environments or creates a new `.venv` folder |
| Hardware detection | Identifies your GPU (NVIDIA/Apple Silicon) or CPU |
| Dependency install | Installs all required packages with the best PyTorch build for your hardware |
| Language model | Downloads the spaCy English model used for privacy scrubbing |
| Environment file | Creates a `.env` file with a secure API key if one doesn't exist |
| Backend startup | Starts the secure API server on port 8000 |
| Dashboard launch | Opens the chat dashboard in your browser |

The first run takes 5–15 minutes depending on your internet speed (downloading AI models and packages). Subsequent launches take under 30 seconds.

---

## 3. First Launch

Once setup completes, your browser opens automatically to `http://localhost:8501`.

You'll see:
- A **sidebar** on the left with conversation management, AI engine settings, and knowledge base controls
- A **chat area** in the centre
- A **file upload section** below the chat

Before you can ask questions, you need to upload at least one document.

---

## 4. Uploading Documents

At the bottom of the main area, you'll see the upload widget:

**"📎 Drag & Drop Documents (PDF, DOCX, TXT, CSV, MD, PNG, JPG)"**

### Supported file types

| Type | Extensions |
|---|---|
| PDF documents | `.pdf` |
| Word documents | `.docx` |
| Plain text | `.txt`, `.md` |
| Spreadsheets | `.csv` |
| Images | `.png`, `.jpg`, `.jpeg` |

### How to upload

1. Drag files directly onto the upload area, or click it to browse
2. You can upload multiple files at once
3. A progress indicator appears: **"🚀 Processing Knowledge Base..."**
4. When complete, you'll see: **"✅ Knowledge Base Updated (N chunks)"**

The system automatically:
- Extracts text from each file (including OCR for image-based content)
- Scrubs any personal information (names, emails, phone numbers, addresses) before indexing
- Splits the content into searchable chunks
- Indexes everything for fast retrieval

You can now start asking questions.

---

## 5. Chatting with Your Documents

Type your question in the input box at the bottom of the page and press Enter.

### What you'll see

1. Your question appears immediately in the chat
2. The AI's answer streams in word by word in real time
3. Below the answer, a metrics bar shows the quality score
4. A **"📚 Sources & References"** expander shows exactly which part of which document the AI used to form its answer

### Tips for better answers

- **Be specific.** "What are the authentication requirements in section 3?" works better than "Tell me about auth."
- **Follow up naturally.** The AI remembers the last 5 exchanges in your conversation. You can say "Can you expand on that?" or "What about the error handling?"
- **Ask about comparisons.** "How does the ingestion flow differ from the retrieval flow?" works well with technical documents.
- **Quote terms from your documents.** If your PDF uses a specific term, use the same term in your question.

### When there are no relevant documents

If no documents match your question, the AI will say so directly rather than making something up. Upload more relevant documents and try again.

---

## 6. Choosing an AI Model

The **AI Engine** section in the sidebar lets you switch between local and cloud models at any time. Your choice applies to new messages in the current conversation.

### Ollama (Local — Private by default)

- Select **Ollama** from the provider dropdown
- Choose a model from the list (populated from your locally installed models)
- Click **🔄** to refresh the model list after pulling a new model
- To pull a new model: type the model name (e.g., `phi3:mini`) in the input box and click **Pull**

Popular local models to try:

| Model | Size | Best for |
|---|---|---|
| `llama3:8b` | ~5 GB | General Q&A, coding |
| `phi3:mini` | ~2.3 GB | Faster responses, lighter hardware |
| `mistral:7b` | ~4 GB | Strong reasoning |
| `llama3:70b` | ~40 GB | Best quality (needs high-end GPU or 64GB+ RAM) |

### Cloud Providers (OpenAI, Google Gemini, Anthropic)

1. Select the provider from the dropdown
2. Choose the model
3. Paste your API key into the secure key field
4. Your key is saved in the session for the rest of your browser session

> **Privacy note:** When using cloud providers, your **questions** are sent to the cloud API. However, PII scrubbing still runs on your query first, so names, emails, and other identifiers are replaced with placeholders before anything is transmitted. The **documents themselves** stay local — only relevant text snippets are included in the API request.

To get API keys:
- **OpenAI:** [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Google Gemini:** [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- **Anthropic:** [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys)

---

## 7. Managing Conversations

### Starting a new conversation

Click **"➕ New Conversation"** in the sidebar. Each conversation has its own independent chat history.

### Renaming a conversation

Click the **⚙️ gear icon** next to any conversation name, type a new name in the text field, and click **Rename**.

### Pinning a conversation

Pinned conversations always appear at the top of the list. You can pin up to **3 conversations**. Click ⚙️ → **Pin**.

### Deleting a conversation

Click ⚙️ → **Delete**. This removes the conversation history but does not affect your documents or the knowledge base.

### Switching conversations

Click any conversation name in the sidebar to switch to it. Your current conversation is automatically saved.

---

## 8. Exporting a Conversation

To save a conversation as a PDF report:

1. Click the ⚙️ icon next to the conversation you want to export
2. Click **"📄 Export PDF"**
3. A download starts immediately — the file is named after the conversation

The PDF includes all messages with role labels, timestamps, and a watermark. It is formatted for sharing or archiving.

---

## 9. Managing Your Knowledge Base

The **Knowledge Base** section in the sidebar shows all documents currently indexed.

### Deleting a specific document

Click the 🗑️ button next to any file name. This removes the file and all its chunks from both the vector index and the keyword index.

### Opening your files folder

Click **📁 Uploads** to open the folder where your uploaded files are stored on your local disk.

### Viewing the database

Click **🗄️ Database** to open the ChromaDB folder where the vector index is stored.

### Full Reset

The **Full Reset** button wipes everything: all indexed documents, the vector database, the BM25 index, all uploaded files, and all conversation history.

**This cannot be undone.** The button requires two clicks to confirm:
1. First click: a confirmation prompt appears
2. Second click: everything is deleted

Use this when you want to start completely fresh with a different set of documents.

---

## 10. Understanding Metrics & Citations

### Perplexity Score

Shown as **"📊 Perplexity (Label): score"** below every answer.

Perplexity measures how fluent and coherent the response is. It runs locally on every answer at no cost.

| Label | Score | Meaning |
|---|---|---|
| Excellent | ≤ 30 | Very clear and fluent response |
| Good | 31–80 | Readable and coherent |
| Okay | 81–160 | Some awkward phrasing, check the answer carefully |
| Confused | > 160 | May be off-topic or garbled — try rephrasing your question |

### RAGAS Deep Evaluation (optional)

Toggle the **📊 Deep Eval** switch in the sidebar to enable RAGAS scoring for a conversation. This adds two additional metrics:

- **Faithfulness** — Did the AI only say things that are actually in your documents? A score of 1.0 means everything is grounded in the source material. Lower scores mean the AI may have added information not present in your files.
- **Relevancy** — How directly does the answer address what you asked? A score close to 1.0 means the answer is on-point.

RAGAS uses the same AI model you're using for generation — so if you're on GPT-4o, it uses GPT-4o to evaluate the answer. This consumes additional API credits.

### Citations

Every answer includes a **"📚 Sources & References"** expander. Click it to see:
- The filename each piece of information came from
- The exact text snippet that was used

If the answer contradicts your documents or the citations look unrelated to your question, try rephrasing or uploading a more relevant document.

---

## 11. Troubleshooting

### The browser didn't open / "This site can't be reached"

Wait 30 seconds and try navigating to `http://localhost:8501` manually. On first launch, downloading models can take a few minutes. If it still fails, check the terminal window for error messages.

### "No relevant documents found"

No chunks in the knowledge base matched your question. Try:
- Rephrasing your question using terms that appear in your documents
- Uploading additional documents that cover the topic
- Checking that the upload completed successfully (green checkmark in the status bar)

### Ollama error / model not responding

1. Make sure Ollama is running — look for the icon in your system tray
2. Verify the model is downloaded: open a terminal and run `ollama list`
3. If the model isn't listed, pull it: `ollama pull llama3:8b`
4. Click the **🔄** refresh button in the AI Engine section of the sidebar

### OCR not working / scanned PDFs show no text

Tesseract is not installed or the path is not configured:
1. Install Tesseract from [github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)
2. Open the `.env` file in the project folder with any text editor
3. Add or update the line: `TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe` (adjust the path to your installation)
4. Restart the application

### API key error (cloud providers)

- Double-check the key was pasted correctly (no extra spaces)
- Confirm the key is for the correct provider and has not expired
- Verify your account has credits / active subscription
- The sidebar will show a specific error message indicating whether it's an authentication failure or a model access issue

### Slow responses

- Local models are CPU-limited without a GPU. Consider pulling a smaller model like `phi3:mini`
- Ensure no other heavy applications are consuming GPU/RAM
- For faster responses with full quality, use a cloud provider (OpenAI, Gemini, Anthropic)

### The app crashed / terminal shows an error

1. Close the terminal window
2. Re-run the launcher (`run_app.bat` or `bash run_app.sh`)
3. If the error persists, delete the `.venv` folder and run the launcher again — it will reinstall everything fresh:
   ```bash
   # Windows (PowerShell)
   Remove-Item -Recurse -Force .venv
   run_app.bat

   # Mac/Linux
   rm -rf .venv && bash run_app.sh
   ```
