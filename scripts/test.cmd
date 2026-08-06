@echo off
setlocal
call .venv\Scripts\activate.bat

python -m pytest apps/api/tests
if errorlevel 1 exit /b 1
python -m pytest services/workflow/tests
if errorlevel 1 exit /b 1
python -m pytest services/knowledge/tests
if errorlevel 1 exit /b 1
python -m pytest services/evaluation/tests
if errorlevel 1 exit /b 1
python -m pytest services/ml/tests
if errorlevel 1 exit /b 1

call npm run typecheck:web
if errorlevel 1 exit /b 1
call npm run lint:web
if errorlevel 1 exit /b 1
call npm run build:web
