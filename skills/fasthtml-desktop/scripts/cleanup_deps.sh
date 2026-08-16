#!/bin/sh
# cleanup_deps.sh — 依赖清理：列出最小 venv 构造步骤和多余包检测
# 用法：cd <project_dir> && dash -c "sh /path/to/cleanup_deps.sh"

PROJ_DIR="${1:-.}"
cd "$PROJ_DIR" || exit 1

echo "=== 依赖清理: $PROJ_DIR ==="
echo ""

# 检查是否存在 .venv
if [ ! -d ".venv" ]; then
  echo ".venv 不存在。创建最小 venv 的步骤："
  echo ""
  echo "  python -m venv .venv"
  echo "  source .venv/Scripts/activate  # Windows Git Bash"
  echo "  pip install -e .               # 安装 pyproject.toml 中的依赖"
  echo "  pip install pyinstaller         # 打包工具"
  echo ""
  echo "注意：不要使用 uv sync（会拉取过多传递依赖导致打包膨胀）"
  exit 0
fi

# 分析 venv 大小
VENV_SIZE=$(du -sh .venv 2>/dev/null | cut -f1)
echo ".venv 大小: $VENV_SIZE"

# 列出核心依赖（与 pyproject.toml 对比）
if [ -f "pyproject.toml" ]; then
  echo ""
  echo "--- pyproject.toml 声明的依赖 ---"
  grep -A50 "^\[project\]" pyproject.toml | grep -A20 "dependencies" | \
    grep -v "^\[" | grep -v "^#" | grep "\"" | \
    sed 's/[", ]//g' | grep -v "^$"
fi

echo ""
echo "--- 可能导致体积膨胀的包 ---"
pip list --format=columns 2>/dev/null | grep -iE "numpy|pandas|matplotlib|scipy|torch|tensorflow|pillow" || echo "  (无大型包)"

echo ""
echo "建议："
echo "  1. 验证最小 venv：python -m venv .build-venv && source .build-venv/Scripts/activate"
echo "  2. 仅安装 pyproject.toml 中的依赖和 pyinstaller"
echo "  3. 对比两个 venv 的大小差异"
echo "  4. 确认无误后删除 .build-venv"
echo ""
echo "=== 完成 ==="
