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

echo ========================================
echo  FastERP  http://127.0.0.1:5011
echo  关闭此窗口即停止服务
echo ========================================
cd /d "%~dp0FastERP"
start "" "http://127.0.0.1:5011"
"%PY%" -m uvicorn web_app:app --host 127.0.0.1 --port 5011
if errorlevel 1 pause
