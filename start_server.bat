@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
title PyGrow Server Start

echo.
echo ╔══════════════════════════════════════════════╗
echo ║         PyGrow 一键启动脚本                  ║
echo ╚══════════════════════════════════════════════╝
echo.

:: 定位 backend 目录（与脚本同目录）
set SCRIPT_DIR=%~dp0
set BACKEND_DIR=%SCRIPT_DIR%backend

if not exist "%BACKEND_DIR%\app\main.py" (
    echo [ERR] 找不到 backend\app\main.py
    echo       请确保 start_server.bat 放在项目根目录
    echo       当前路径: %SCRIPT_DIR%
    pause
    exit /b 1
)

echo 项目目录: %SCRIPT_DIR%
echo.

:: ============================================
:: 1. 检查 MySQL
:: ============================================
echo [1/4] 检查 MySQL ...
mysql -uroot -proot -e "SELECT 1;" >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ERR] MySQL 未启动或无法连接！
    echo.
    echo   请先在 phpStudy 面板中启动 MySQL，然后再运行本脚本。
    echo.
    pause
    exit /b 1
)
echo   [ OK ] MySQL 连接正常

:: 检查数据库是否存在，不存在则创建
mysql -uroot -proot -e "SHOW DATABASES LIKE 'jyjs2313';" 2>nul | findstr "jyjs2313" >nul
if !errorlevel! neq 0 (
    echo   [INFO] 创建数据库 jyjs2313 ...
    mysql -uroot -proot -e "CREATE DATABASE IF NOT EXISTS jyjs2313 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>nul
    echo   [ OK ] 数据库 jyjs2313 已创建
) else (
    echo   [ OK ] 数据库 jyjs2313 已存在
)

:: ============================================
:: 2. 检查 .env
:: ============================================
echo [2/4] 检查 .env 配置 ...
if not exist "%BACKEND_DIR%\.env" (
    echo   [ERR] .env 文件不存在！
    echo       请先配置 backend\.env，参考 SERVER_SETUP.md 第五节
    pause
    exit /b 1
)
echo   [ OK ] .env 已配置

:: ============================================
:: 3. 检查端口是否被占用
:: ============================================
echo [3/4] 检查端口 8000 ...
set PORT_FREE=1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>nul') do (
    set PID=%%a
    set PORT_FREE=0
)
if !PORT_FREE! equ 0 (
    echo   [WARN] 端口 8000 已被占用 (PID: !PID!)
    echo.
    echo   可能是之前的后端还在运行。
    set /p KILL="   是否结束该进程并重新启动? [Y/n]: "
    if /i "!KILL!" neq "n" (
        taskkill /PID !PID! /F >nul 2>&1
        echo   [ OK ] 已结束进程 !PID!
        timeout /t 1 /nobreak >nul
    ) else (
        echo   已取消。请手动处理端口冲突后重试。
        pause
        exit /b 1
    )
)
echo   [ OK ] 端口 8000 可用

:: ============================================
:: 4. 启动后端
:: ============================================
echo [4/4] 启动后端服务 ...
echo.
echo ══════════════════════════════════════════════
echo   后端启动中，请勿关闭本窗口...
echo .
echo   后端地址: http://127.0.0.1:8000
echo   API 文档: http://127.0.0.1:8000/docs
echo ══════════════════════════════════════════════
echo.
cd /d "%BACKEND_DIR%"
uvicorn app.main:app --host 127.0.0.1 --port 8000

:: 如果 uvicorn 退出
echo.
echo ══════════════════════════════════════════════
echo   后端已停止运行
echo ══════════════════════════════════════════════
pause
