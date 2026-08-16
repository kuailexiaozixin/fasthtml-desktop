@echo off
chcp 65001 >nul
REM ============================================================
REM  PyWebView 原生界面质检 · 一键启动器（在有显示器的电脑上用）
REM  
REM  用途：对正在运行的 FastHTML 应用做原生界面质检，并截出真实 PNG。
REM        全程 PyWebView 原生能力，不依赖 Chrome / 额外浏览器 / 浏览器授权。
REM
REM  前提：
REM   1) 本机已安装 Python 且能 import webview（pywebview）。
REM   2) 目标 FastHTML 应用已在运行，并能通过下面的地址访问。
REM
REM  用法（二选一）：
REM   A) 双击本文件（用默认地址 http://127.0.0.1:5001）
REM   B) 命令行：run_ui_verify.bat http://127.0.0.1:5001
REM ============================================================

set "URL=%1"
if "%URL%"=="" set "URL=http://127.0.0.1:5001"

echo 正在对 %URL% 做 PyWebView 原生界面质检（会弹出真实窗口并截图）...
python "%~dp0ui_window_verify.py" --url %URL% --show
echo.
echo 质检完成。截图保存在脚本同目录的 ui-window-screenshot.png
echo 若提示"未生成像素截图"，说明当前环境没有显示器——请在有桌面的电脑上运行本启动器。
pause
