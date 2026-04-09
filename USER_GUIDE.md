# 📖 User Guide: Getting Started with Local RAG

Welcome! This guide is for users who want to use the Local RAG application without worrying about code or complex terminal commands.

---

## 🛠️ Prerequisites
Before starting, ensure you have these two things installed:
1.  **Python 3.10 or 3.11:** [Download from Python.org](https://www.python.org/downloads/) (Check the box "Add Python to PATH" during installation).
2.  **Ollama:** [Download from Ollama.com](https://ollama.com/) (This runs the AI models on your computer).

---

## 🚀 One-Click Setup

### 1. Download the Project
Download the project folder from the repository and extract it to your computer.

### 2. Run the Starter
*   **Windows:** Double-click the file named `run_app.bat`.
*   **Mac / Linux:** Open your terminal in the project folder and type `bash run_app.sh`.

### 3. What happens next?
A black window (terminal) will open. It will automatically:
*   Create a safe space for the app to live (Virtual Environment).
*   Check if you have a GPU (like NVIDIA) to make the AI faster.
*   Install all necessary tools.
*   **Launch the Dashboard** in your web browser.

---

## 🖥️ Using the Dashboard

### 1. Uploading Documents
At the bottom of the screen, you will see a **"Drag & Drop"** area. 
*   Drop your PDFs, Word docs, or Text files here.
*   Wait for the green checkmark ✅. The AI now "knows" your files.

### 2. Managing your Knowledge
In the **Sidebar** (left side), you can see a list of your uploaded files.
*   Use the 🗑️ icon to make the AI "forget" a specific document.

### 3. Chatting
Simply type your question in the chat box at the bottom.
*   The AI will search your documents first.
*   It will show you **Sources & References** so you can verify the answer.

### 4. Advanced Evaluation
If you want to know if the AI is "hallucinating" (lying), turn on **Advanced Eval** in the sidebar. 
*   It will give the AI a grade for **Faithfulness** and **Relevancy**.
*   *Note: This makes the AI a bit slower as it double-checks its own work.*

---

## ❓ Troubleshooting
*   **App is slow:** Make sure you have a GPU and that `install.py` detected it.
*   **OCR Error:** If the app can't read images, you may need to install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki).
*   **Ollama Error:** Ensure the Ollama app is running in your system tray (near the clock).
