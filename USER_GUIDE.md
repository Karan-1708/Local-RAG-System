# 📖 User Guide: Getting Started with Local RAG

Welcome! This guide is for users who want to use the Local RAG application without worrying about code or complex terminal commands.

---

## 🛠️ Prerequisites
Before starting, ensure you have these two things installed:
1.  **Python 3.11 - 3.13:** [Download from Python.org](https://www.python.org/downloads/) (Check the box "Add Python to PATH" during installation).
2.  **Ollama:** [Download from Ollama.com](https://ollama.com/) (This runs the AI models on your computer).

---

## 🚀 One-Click Setup

### 1. Download the Project
Download the project folder from the repository and extract it to your computer.

### 2. Run the Starter
*   **Windows:** Double-click the file named `run_app.bat`.
*   **Mac / Linux:** Open your terminal in the project folder and type `bash run_app.sh`.

### 3. What happens next?
A terminal window will open. It will automatically:
*   Validate your Python version and install 3.12 if needed.
*   Let you choose an existing virtual environment or create a new one.
*   Optimize your hardware (NVIDIA GPU, Apple Silicon, or CPU).
*   Launch both the **Secure Backend API** and the **Interactive Dashboard**.

---

## 🖥️ Using the Dashboard

### 1. Instant Document Ingestion
You can now drag and drop files directly into the chat area.
*   **Supported Formats:** PDF, DOCX, TXT, MD, PNG, JPG, CSV.
*   **Live Processing:** The system will immediately extract, chunk, and index your file. You'll see a green checkmark once it's ready.

### 2. Chat Management (Sidebar)
*   **Multiple Chats:** Use the **➕ New Conversation** button to start fresh topics.
*   **Rename & Pin:** Use the ⚙️ settings icon next to any chat to rename it or pin it (up to 3) to the top.
*   **PDF Export:** Download a professional technical report of any conversation for your records.

### 3. Intelligent Chatting
Type your questions at the bottom. The AI remembers the context of your current conversation, even if you switch providers.
*   **Streaming:** Answers appear in real-time as they are generated.
*   **Citations:** Click the **📄 Technical Sources** expander to see exactly which parts of your documents were used.

### 4. Evaluation Control
Click the **📊 icon** next to the chat box to toggle **Deep Eval (RAGAS)** for that specific conversation. 
*   It scores the AI on **Faithfulness** and **Relevancy**.
*   The system uses the same provider (e.g., GPT-4o or Llama 3) to grade the answer.

---

## 📂 Data Management & Safety
Located at the very bottom of the sidebar:
*   **Open Folders:** Use the **📁 Uploads** or **🗄️ Database** buttons to inspect your local storage.
*   **Nuclear Reset:** The **Full Reset** button now requires a two-step confirmation to prevent accidental data loss. It wipes everything, including chat history and API keys.

---

## ❓ Troubleshooting
*   **Ollama Error:** Ensure the Ollama app is running in your system tray.
*   **API Key Error:** If using Frontier models, ensure your key is correct. The app will provide a specific warning if authentication fails.
*   **OCR failure:** Ensure [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) is installed and the path is set in your `.env`.
