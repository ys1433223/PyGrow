@echo off
cd /d D:\phpstudy_pro\www\jyjs2313\backend
echo PyGrow Backend Starting...
echo http://127.0.0.1:8000/docs
echo.
uvicorn app.main:app --host 127.0.0.1 --port 8000
pause
