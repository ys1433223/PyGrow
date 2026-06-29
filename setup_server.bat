@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title PyGrow Server Setup
echo.
echo ╔══════════════════════════════════════════════╗
echo ║       PyGrow 服务器环境一键配置            ║
echo ╚══════════════════════════════════════════════╝
echo.

:: 定位脚本和 backend 目录
set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%backend

if not exist "%BACKEND_DIR%\requirements.txt" (
    echo [ERR] 找不到 backend\requirements.txt
    echo       请确保 setup_server.bat 与 backend/ 目录在同一级
    echo       当前路径: %SCRIPT_DIR%
    pause
    exit /b 1
)

echo 脚本目录: %SCRIPT_DIR%
echo 后端目录: %BACKEND_DIR%
echo.

:: ============================================
:: 1. Python
:: ============================================
echo [1/6] 检查 Python ...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [MISS] Python 未安装！
    echo.
    echo   请手动下载安装 Python 3.12+:
    echo   https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe
    echo   安装时务必勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo   [ OK ] Python !PYVER!

:: Check >= 3.12
for /f "tokens=2 delims=." %%a in ("!PYVER!") do set PY_MINOR=%%a
if !PY_MINOR! lss 12 (
    echo   [WARN] 需要 Python 3.12+, 当前 !PYVER! 可能不兼容
)

:: ============================================
:: 2. pip 镜像源
:: ============================================
echo [2/6] 配置 pip 镜像源 ...
pip config list 2>nul | findstr "tuna.tsinghua" >nul
if %errorlevel% neq 0 (
    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple >nul 2>&1
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn >nul 2>&1
    echo   [ OK ] 已配置清华镜像
) else (
    echo   [ OK ] 已配置
)

:: ============================================
:: 3. 逐条对照 requirements.txt 检查
:: ============================================
echo [3/6] 逐条检查 requirements.txt ...
set ALL_OK=1
set MISSING=
set COUNT_TOTAL=0
set COUNT_MISS=0

for /f "usebackq tokens=* delims=" %%L in ("%BACKEND_DIR%\requirements.txt") do (
    set LINE=%%L
    set LINE=!LINE: =!
    if not "!LINE!"=="" if not "!LINE:~0,1!"=="#" (
        for /f "tokens=1 delims==~;<>[ " %%P in ("!LINE!") do (
            set PKG=%%P
            set /a COUNT_TOTAL+=1
            pip show !PKG! >nul 2>&1
            if !errorlevel! neq 0 (
                set ALL_OK=0
                set /a COUNT_MISS+=1
                set MISSING=!MISSING!  !PKG!
            )
        )
    )
)

if !ALL_OK! equ 1 (
    echo   [ OK ] 全部 !COUNT_TOTAL! 个依赖已安装
) else (
    echo   [MISS] !COUNT_MISS!/!COUNT_TOTAL! 个缺失:!MISSING!
)

:: ============================================
:: 4. 安装缺失
:: ============================================
if !ALL_OK! equ 0 (
    echo.
    echo ══════════════════════════════════════════════
    echo [4/6] 安装缺失依赖 ...
    echo ══════════════════════════════════════════════
    cd /d "%BACKEND_DIR%"
    pip install -r requirements.txt
    if %errorlevel% equ 0 (
        echo   [ OK ] 全部依赖安装完成
    ) else (
        echo   [WARN] openai-whisper 可能失败 ^(需 PyTorch 约2GB^)
        echo           AI语音识别已设为 mock 模式，不影响核心功能
    )
    cd /d "%SCRIPT_DIR%"
) else (
    echo [4/6] 跳过 (全部已安装)
)

:: ============================================
:: 5. MySQL
:: ============================================
echo [5/6] 检查 MySQL ...
mysql -uroot -proot -e "SELECT 1;" >nul 2>&1
if %errorlevel% neq 0 (
    echo   [WARN] mysql 命令不可用
    echo          - 确认 phpStudy 面板 MySQL 已启动
    echo          - 或将 MySQL bin 目录加入系统 PATH
) else (
    for /f "tokens=*" %%v in ('mysql -uroot -proot -e "SELECT VERSION();" 2^>nul ^| findstr /v "VERSION"') do set MVER=%%v
    echo   [ OK ] MySQL !MVER!

    mysql -uroot -proot -e "SHOW DATABASES LIKE 'jyjs2313';" 2>nul | findstr "jyjs2313" >nul
    if !errorlevel! neq 0 (
        mysql -uroot -proot -e "CREATE DATABASE IF NOT EXISTS jyjs2313 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>nul
        echo   [ OK ] 数据库 jyjs2313 已创建
    ) else (
        echo   [ OK ] 数据库 jyjs2313 已存在
    )
)

:: ============================================
:: 6. FFmpeg
:: ============================================
echo [6/6] 检查 FFmpeg ...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [WARN] FFmpeg 未装 (可选, AI笔记视频需要)
) else (
    echo   [ OK ] FFmpeg 已安装
)

:: ============================================
:: 最终报告
:: ============================================
echo.
echo ╔══════════════════════════════════════════════╗
echo ║              最终状态                        ║
echo ╚══════════════════════════════════════════════╝

python --version >nul 2>&1 && echo   Python      : OK || echo   Python      : 需安装
pip show fastapi >nul 2>&1 && echo   依赖包      : OK || echo   依赖包      : 需安装
mysql -uroot -proot -e "SELECT 1;" >nul 2>&1 && echo   MySQL       : OK || echo   MySQL       : 检查 phpStudy
ffmpeg -version >nul 2>&1 && echo   FFmpeg      : OK || echo   FFmpeg      : 未装 (可选)
if exist "%BACKEND_DIR%\.env" (echo   .env 配置   : OK) else (echo   .env 配置   : 缺失！)
if exist "%BACKEND_DIR%\app\main.py" (echo   后端代码    : OK) else (echo   后端代码    : 缺失！)

echo.
echo ══════════════════════════════════════════════
echo   全部 OK 则执行以下命令启动后端:
echo.
echo     cd backend
echo     uvicorn app.main:app --host 127.0.0.1 --port 8000
echo.
echo   浏览器验证: http://127.0.0.1:8000/docs
echo ══════════════════════════════════════════════
echo.
pause
