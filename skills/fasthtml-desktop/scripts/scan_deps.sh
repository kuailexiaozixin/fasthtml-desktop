#!/bin/sh
# scan_deps.sh — 静态扫描所有 .py 文件的 import 语句，与已安装包对比
# 用法：cd <project_dir> && dash -c "sh /path/to/scan_deps.sh"

PROJ_DIR="${1:-.}"
cd "$PROJ_DIR" || exit 1

echo "=== 依赖静态扫描: $PROJ_DIR ==="

# 1. 提取所有 import 语句
echo ""
echo "--- 源代码引用的包 ---"
find src/ -name "*.py" -not -path "*/__pycache__/*" -exec grep -hE "^(import |from )" {} \; | \
  sed 's/^import //; s/^from \([^ ]*\).*/\1/' | \
  grep -v "^_" | grep -v "^\." | \
  sort -u | grep -v "^$" | head -30

# 2. 对比已安装的包
echo ""
echo "--- 已安装的核心依赖 ---"
if [ -f "pyproject.toml" ]; then
  grep -A50 "\[project\]" pyproject.toml | grep -A20 "dependencies" | \
    grep -v "^\[" | grep -v "^#" | grep "\"" | \
    sed 's/[", ]//g' | grep -v "^$"
fi

echo ""
echo "--- 检查是否有多余的包 ---"
if [ -d ".venv" ]; then
  pip list --format=columns 2>/dev/null | grep -v "^Package\|^----" | head -20
fi

echo ""
echo "=== 扫描完成 ==="
echo "提示：对比"源代码引用的包"和"已安装的核心依赖"，确认没有遗漏或多余的包。"
