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
echo  FastDataGov  http://127.0.0.1:5062
echo  默认演示模式；PostgreSQL 后端需先配置 DB_URL / REPOSITORY_MODE=postgres
echo  关闭此窗口即停止服务
echo ========================================
cd /d "%~dp0FastDataGov"
start "" "http://127.0.0.1:5062"
"%PY%" main.py
if errorlevel 1 pause
