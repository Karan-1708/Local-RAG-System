# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# - tesseract-ocr: for OCR on PDFs/images
# - libgl1: for OpenCV
# - poppler-utils: for PDF processing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    poppler-utils \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# We install a standard torch distribution. For GPU acceleration inside Docker, 
# a different base image (nvidia/cuda) and specific flags would be needed.
RUN pip install --no-cache-dir -r requirements.txt

# Download the required spaCy model for PII redaction
RUN python -m spacy download en_core_web_sm

# Copy the rest of the application code
COPY . .

# Expose ports:
# 8501: Streamlit
# 8000: FastAPI
EXPOSE 8501 8000

# Default command: Launch both FastAPI and Streamlit
# We use a shell script to orchestrate multiple processes
RUN echo '#!/bin/bash\nuvicorn api:app --host 0.0.0.0 --port 8000 & \nstreamlit run app.py --server.port=8501 --server.address=0.0.0.0' > /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
