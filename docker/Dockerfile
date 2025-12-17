FROM python:3.12.11-slim-bookworm AS base

WORKDIR /app

# System dependencies:
# - curl, gnupg: health checks, repo setup
# - WeasyPrint: libpango*, libharfbuzz*, libgdk-pixbuf*, libcairo*, libglib*, fonts-* (PDF generation)
# - CUDA libs: runtime for PyTorch (excludes ~3GB nvidia-* Python packages via pyproject.toml)
# See: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl gnupg \
        libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 \
        libharfbuzz-subset0 libgdk-pixbuf-2.0-0 \
        libffi-dev libcairo2 libglib2.0-0 \
        fonts-liberation fonts-dejavu-core && \
    curl -fsSL https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.1-1_all.deb -o /tmp/cuda-keyring.deb && \
    dpkg -i /tmp/cuda-keyring.deb && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        cuda-libraries-12-8 libcudnn9-cuda-12 libcusparselt0-cuda-12 \
        libnccl2 libnvshmem3-cuda-12 cuda-cupti-12-8 && \
    echo "/usr/lib/x86_64-linux-gnu/libcusparseLt/12" > /etc/ld.so.conf.d/cuda-extra.conf && \
    echo "/usr/lib/x86_64-linux-gnu/nvshmem/12" >> /etc/ld.so.conf.d/cuda-extra.conf && \
    ldconfig && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/cuda-keyring.deb

# Install uv (copy from official image is faster than pip install)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# More timeout for large packages
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_HTTP_TIMEOUT=300

# Copy dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Dependencies only (cache mount persists downloads across rebuilds)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

# Copy application code
COPY . .

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Set Python path
ENV PYTHONPATH=/app

# ============================================================
# API target
# ============================================================
FROM base AS api

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================================
# Celery worker target
# ============================================================
FROM base AS celery

CMD ["uv", "run", "celery", "-A", "app.core.celery:celery_app", "worker", "--loglevel=info"]
