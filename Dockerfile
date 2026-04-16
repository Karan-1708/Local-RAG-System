# ── Base image ───────────────────────────────────────────────────────────────
FROM python:3.12-slim

# ── System dependencies ──────────────────────────────────────────────────────
# tesseract-ocr   : OCR for scanned PDFs and image files
# poppler-utils   : pdf2image uses pdftoppm from poppler
# libgl1          : OpenCV / image libraries need this (replaces deprecated libgl1-mesa-glx)
# build-essential : compiling any C-extension wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies ──────────────────────────────────────────────────────
# Copy requirements first to leverage layer caching — only reinstalls when
# requirements.txt changes, not on every code change.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── spaCy language model ─────────────────────────────────────────────────────
# Required by Microsoft Presidio for PII entity recognition.
RUN python -m spacy download en_core_web_sm

# ── Application code ─────────────────────────────────────────────────────────
COPY . .

# ── Entrypoint script ────────────────────────────────────────────────────────
# Start FastAPI in the background, then exec Streamlit as PID 1 so that
# container signals (SIGTERM, SIGINT) are forwarded cleanly.
RUN printf '#!/bin/bash\nset -e\n# Ensure runtime directories exist (volumes may be empty on first start)\nmkdir -p /app/data/raw /app/chroma_db\n# Initialise session state file so Streamlit can persist chats\nif [ ! -f /app/data/session_state.json ]; then\n  echo "{}" > /app/data/session_state.json\nfi\nuvicorn api.main:app --host 0.0.0.0 --port 8000 &\nexec streamlit run ui/main.py --server.port=8501 --server.address=0.0.0.0\n' \
    > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# ── Ports ────────────────────────────────────────────────────────────────────
EXPOSE 8501 8000

CMD ["/app/entrypoint.sh"]
