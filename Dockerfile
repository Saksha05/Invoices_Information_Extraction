# syntax=docker/dockerfile:1

# ============================================================================
# Multi-stage Dockerfile for Insurance RAG Application
# Optimized for production with minimal image size and enhanced security
# Compatible with both Docker and Podman
# ============================================================================

# ============================================================================
# Stage 1: Builder - Compile dependencies and prepare virtual environment
# ============================================================================
FROM python:3.11-slim AS builder

# Prevent Python from writing bytecode and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies required for compiling Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment for dependency isolation
WORKDIR /app
RUN python -m venv /app/venv

# Activate virtual environment
ENV PATH="/app/venv/bin:$PATH"

# Copy only requirements first for optimal layer caching
COPY requirements.txt .

# Install Python dependencies in virtual environment
# Using --no-cache-dir to reduce image size
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Minimal production image
# ============================================================================
FROM python:3.11-slim AS runtime

# Security: Create non-root user for running the application
RUN groupadd -r appuser && useradd -r -g appuser -u 1001 appuser

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libpq5 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/venv /app/venv

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/venv/bin:$PATH" \
    TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata \
    TRANSFORMERS_CACHE=/app/models \
    SENTENCE_TRANSFORMERS_HOME=/app/models \
    HF_HOME=/app/models \
    HF_HUB_OFFLINE=0 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Copy application code
COPY --chown=appuser:appuser stream_invoice_clean.py rag.py ./

# Copy models directory (for offline operation)
COPY --chown=appuser:appuser models/ ./models/

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs /app/.streamlit && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Health check to ensure container is running properly
HEALTHCHECK --interval=30s \
    --timeout=10s \
    --start-period=40s \
    --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit application
CMD ["streamlit", "run", "stream_invoice_clean.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.fileWatcherType=none"]