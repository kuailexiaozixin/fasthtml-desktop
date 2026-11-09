#!/bin/sh
# build_windows_exe.sh — 通过 dash 间接调用 PowerShell 脚本
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
dash -c "powershell.exe -ExecutionPolicy Bypass -File \"$SCRIPT_DIR/build_windows_exe.ps1\""
