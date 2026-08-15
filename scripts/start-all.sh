#!/usr/bin/env bash
set -e

echo "========================================="
echo " Starting Civitas Civic Intelligence     "
echo "========================================="

# 1. Run Database Migrations
echo -e "\n[1/3] Running database migrations..."
python3 scripts/migrate.py || echo "[WARNING] Migration failed or already applied."

# 2. Set PYTHONPATH
export PYTHONPATH="apps/api/src:services/workflow/src:services/knowledge/src:services/evaluation/src:services/ml/src:services/operations/src:services/policies/src:services/storage/src:ml/vision/src:ml/clustering/src:ml/routing/src:ml/resolution/src:ml/duplicates/src:ml/risk/src:geospatial/src:schemas/src"

# 3. Start API in background
echo -e "\n[2/3] Starting FastAPI Backend on port 8000..."
python3 -m uvicorn civitas_api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

trap "kill $API_PID 2>/dev/null || true" EXIT

# 4. Start Next.js Frontend
echo -e "\n[3/3] Starting Next.js Web Application on port 3000..."
npm --workspace apps/web run dev
