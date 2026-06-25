@echo off
cd /d "%~dp0frontend"

echo ============================================
echo   PyGrow Frontend
echo   URL: http://localhost:5173
echo ============================================
echo.

if not exist "node_modules\" (
    echo Installing dependencies...
    npm install
    echo.
)

npm run dev
pause
