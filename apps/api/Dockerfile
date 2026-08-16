# Production Dockerfile for Civitas API & ML Engine (FastAPI + Python 3.12)
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy local source code and python packages
COPY . .

# Install workspace packages from their declared dependency graphs.
# civitas-vision owns the tested NumPy constraint (>=1.26,<2.0).
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install ./geospatial && \
    python -m pip install "./ml/vision[video]" && \
    python -m pip install "./ml/duplicates[geo,vision]" && \
    python -m pip install "./ml/risk[geo,duplicates]" && \
    python -m pip install "./ml/resolution[vision]" && \
    python -m pip install ./services/knowledge && \
    python -m pip install "./services/ml[full,video,http]" && \
    python -m pip install "./services/workflow[postgres]" && \
    python -m pip install ./apps/api

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/live || exit 1

CMD ["sh", "-c", "uvicorn civitas_api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
