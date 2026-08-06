@echo off
call .venv\Scripts\activate.bat
python -m uvicorn civitas_api.main:app --app-dir apps/api/src --reload --host 0.0.0.0 --port 8000
