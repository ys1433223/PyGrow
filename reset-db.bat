@echo off
cd /d "%~dp0"

echo ============================================
echo   Reset PyGrow Database
echo ============================================
echo.

set /p confirm="Delete pygrow.db and rebuild? (y/n): "
if /i "%confirm%" neq "y" (
    echo Cancelled.
    pause
    exit /b
)

if exist "backend\pygrow.db" (
    del "backend\pygrow.db"
    echo [OK] Database deleted.
) else (
    echo No database file found.
)

echo.
echo Done. Next backend start will recreate DB with seed data.
pause
