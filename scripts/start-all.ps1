# Civitas Full-Stack Startup Script (PowerShell)
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Starting Civitas Civic Intelligence     " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Run Database Migrations
Write-Host "`n[1/3] Running database migrations..." -ForegroundColor Yellow
& .venv\Scripts\python.exe scripts\migrate.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Migration finished with code $LASTEXITCODE. Continuing startup..." -ForegroundColor DarkYellow
}

# 2. Start FastAPI Backend in background
Write-Host "`n[2/3] Starting FastAPI Backend on port 8000..." -ForegroundColor Yellow
$env:PYTHONPATH="apps/api/src;services/workflow/src;services/knowledge/src;services/evaluation/src;services/ml/src;services/operations/src;services/policies/src;services/storage/src;ml/vision/src;ml/clustering/src;ml/routing/src;ml/resolution/src;ml/duplicates/src;ml/risk/src;geospatial/src;schemas/src"

Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m uvicorn civitas_api.main:app --host 127.0.0.1 --port 8000 --reload" -NoNewWindow

# 3. Start Next.js Frontend
Write-Host "`n[3/3] Starting Next.js Web Application on port 3000..." -ForegroundColor Green
npm --workspace apps/web run dev
