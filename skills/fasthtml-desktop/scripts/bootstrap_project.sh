#!/bin/sh
# bootstrap_project.sh — 从 Git Bash 调用 PowerShell 生成项目骨架
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PS1="$(cygpath -w "$SCRIPT_DIR/bootstrap_project.ps1" 2>/dev/null || echo "$SCRIPT_DIR/bootstrap_project.ps1")"
exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$PS1" "$@"