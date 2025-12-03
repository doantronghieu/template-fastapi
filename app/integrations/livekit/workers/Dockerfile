# LiveKit Voice Agent Worker
FROM python:3.12-slim

WORKDIR /app

# Install system deps and uv
RUN apt-get update && apt-get install -y --no-install-recommends gcc libffi-dev curl \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:$PATH"

# Install dependencies
COPY app/integrations/livekit/workers/requirements.txt ./
RUN uv pip install --system -r requirements.txt

# Copy app code
COPY app/ ./app/

ENV PYTHONPATH=/app

CMD ["python", "-m", "app.integrations.livekit.workers.voice_agent"]
