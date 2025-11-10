# # syntax=docker/dockerfile:1
# # --- Base image ---
# FROM python:3.13-slim AS base

# # Prevent interactive prompts & set Python env flags
# ENV DEBIAN_FRONTEND=noninteractive \
#     PYTHONDONTWRITEBYTECODE=1 \
#     PYTHONUNBUFFERED=1 \
#     PIP_NO_CACHE_DIR=1 \
#     STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# # Install system dependencies
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     tesseract-ocr \
#     poppler-utils \
#     libgl1 \
#     libglib2.0-0 \
#     curl \
#     ca-certificates \
#     git \
#     && rm -rf /var/lib/apt/lists/*

# # Create non-root user
# RUN useradd -m appuser
# WORKDIR /app

# # Copy requirements and install Python packages
# COPY requirements.txt ./

# # Install pip packages with SSL verification disabled (for corporate proxy)
# RUN pip install --upgrade pip \
#     --trusted-host pypi.org \
#     --trusted-host pypi.python.org \
#     --trusted-host files.pythonhosted.org && \
#     pip install --no-cache-dir -r requirements.txt \
#     --trusted-host pypi.org \
#     --trusted-host pypi.python.org \
#     --trusted-host files.pythonhosted.org

# # Copy the pre-downloaded model files (NO NETWORK ACCESS NEEDED!)
# COPY ./models/all-MiniLM-L6-v2 /app/models/all-MiniLM-L6-v2

# # Set HuggingFace cache environment variables to use local model
# ENV TRANSFORMERS_CACHE=/app/models \
#     SENTENCE_TRANSFORMERS_HOME=/app/models \
#     HF_HOME=/app/models \
#     HF_HUB_OFFLINE=1

# # Copy application source
# COPY . .

# # Set ownership to appuser
# RUN chown -R appuser:appuser /app

# # Switch to non-root user
# USER appuser

# # Set environment variables
# ENV TESSERACT_CMD=/usr/bin/tesseract \
#     APP_FILE=stream_invoice_clean.py

# # Expose ports
# EXPOSE 8501 8000

# # Healthcheck
# HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
#     CMD curl -f http://localhost:8501/ || exit 1

# # Run Streamlit
# CMD ["streamlit", "run", "stream_invoice_clean.py", "--server.port=8501", "--server.address=0.0.0.0"]


# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libpq-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY stream_invoice_clean.py .
COPY rag.py .
COPY docker.env .env

# Copy the models folder if it exists
COPY models/ ./models/

# Create necessary directories
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata

# Expose Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the Streamlit app
CMD ["streamlit", "run", "stream_invoice_clean.py", "--server.port=8501", "--server.address=0.0.0.0"]