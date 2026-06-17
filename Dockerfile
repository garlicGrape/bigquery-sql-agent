FROM python:3.11-slim

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Install dependencies first (separate layer for cache)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY app/ ./app/

ENV PYTHONUNBUFFERED=1
# Make the venv's binaries directly accessible
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

# Cloud Run injects $PORT; default to 8080 for local docker run
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
