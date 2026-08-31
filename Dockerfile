# Multi-stage lightweight Python Dockerfile for Academic-ScreenX
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies for compilation if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final runtime image
FROM python:3.11-slim

WORKDIR /app

# Copy installed wheels from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application source
COPY . .

# Ensure storage directories exist
RUN mkdir -p /app/uploads /app/sample_pdfs

# Pre-generate sample test PDFs
RUN python tests/generate_samples.py

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    PORT=8000 \
    USE_MOCK_LLM=True

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/submissions/stats')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
