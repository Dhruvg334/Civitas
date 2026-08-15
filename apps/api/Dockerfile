# Multi-stage Dockerfile for Civitas API & ML Engine (FastAPI + Python 3.12)
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

# Copy local source code and python modules
COPY . .

# Install dependencies and local workspace packages
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    pydantic \
    pydantic-settings \
    psycopg[binary] \
    python-dotenv \
    pyjwt \
    httpx \
    pillow \
    numpy \
    langgraph \
    langgraph-checkpoint-postgres

ENV PYTHONPATH="apps/api/src:services/workflow/src:services/knowledge/src:services/evaluation/src:services/ml/src:services/operations/src:services/policies/src:services/storage/src:ml/vision/src:ml/clustering/src:ml/routing/src:ml/resolution/src:ml/duplicates/src:ml/risk/src:geospatial/src:schemas/src"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/ready || exit 1

CMD ["uvicorn", "civitas_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
