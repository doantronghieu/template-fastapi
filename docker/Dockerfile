FROM python:3.12.11-slim-bookworm

WORKDIR /app

# Install system dependencies and security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml .
COPY .python-version* ./

# Install dependencies
RUN uv sync

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Expose FastAPI port (configurable via PORT env var)
EXPOSE 8000

# Run FastAPI with uvicorn (respects PORT env var from settings)
CMD ["sh", "-c", "uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
