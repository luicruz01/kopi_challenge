FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal - pure Python wheels)
RUN apt-get update && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ ./api/

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT:-8000}/healthz')" || exit 1

# Run the application
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
