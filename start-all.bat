@echo off
cd /d "%~dp0"

echo ============================================
echo   PyGrow Start All
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo ============================================
echo.

echo Starting backend...
start "PyGrow-Backend" cmd /c "cd /d %~dp0backend && python -m uvicorn app.main:app --reload --port 8000"

echo Waiting...
timeout /t 3 /nobreak >nul

echo Starting frontend...
start "PyGrow-Frontend" cmd /c "cd /d %~dp0frontend && npm run dev"

echo.
echo Both services started in separate windows.
echo Close each window to stop.
pause
