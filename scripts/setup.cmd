@echo off
setlocal

where node >nul 2>nul || (echo Node.js is required. & exit /b 1)
where python >nul 2>nul || (echo Python is required. & exit /b 1)

if not exist .env copy .env.example .env >nul

call npm install
if errorlevel 1 exit /b 1

python -m venv .venv
if errorlevel 1 exit /b 1
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e "apps/api[dev]" -e "services/workflow[dev]" -e "services/knowledge[dev]" -e "services/evaluation[dev]" -e "services/ml[dev]"

echo Civitas local setup completed.
