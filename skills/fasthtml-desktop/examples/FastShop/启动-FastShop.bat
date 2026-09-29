@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
set "VENV=%~dp0..\.venv"
if not exist "%~dp0..\.venv\Scripts\python.exe" (
    echo [错误] 共享虚拟环境不存在: %~dp0..\.venv
    echo 请先创建共享环境后再运行本脚本。
    pause & exit /b 1
)
set "PY=%~dp0..\.venv\Scripts\python.exe"

set "FASTSHOP_PORT=5025"
echo ========================================
echo  FastShop  http://127.0.0.1:5025
echo  关闭此窗口即停止服务
echo ========================================
start "" "http://127.0.0.1:5025"
"%PY%" web_app.py
if errorlevel 1 pause
