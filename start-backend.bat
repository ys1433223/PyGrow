@echo off
cd /d "%~dp0backend"

echo ============================================
echo   PyGrow Backend
echo   URL: http://localhost:8000
echo   API: http://localhost:8000/docs
echo ============================================
echo.

pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

python -m uvicorn app.main:app --reload --port 8000
pause
