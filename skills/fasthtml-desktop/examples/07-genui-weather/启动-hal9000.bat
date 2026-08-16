@echo off
setlocal
set GENUI_DEMO=hal9000
cd /d "%~dp0"
python -c "import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
if errorlevel 1 (echo [launcher] Python 3.10+ required. Install from https://www.python.org/downloads/ & pause & exit /b 1)
python "%~dp0launcher.py" %*
if errorlevel 1 pause
