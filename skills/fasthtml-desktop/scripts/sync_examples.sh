#!/bin/sh
# sync_examples.sh — 将 templates/shared/main.py 同步到各示例目录
#
# 注意：启动器（launcher.py 决策层 + 启动.bat 派发壳）的同步由 scripts/gen_launchers.py
#       统一负责，与本脚本正交。本脚本在前向同步（无参数）时会顺带调用它，保持 examples
#       启动器与 templates/shared/launcher.py 一致；--reverse / --diff 模式不触发，避免误写文件。
# 用法：
#   dash -c "sh scripts/sync_examples.sh"             # 正向同步（shared → 示例）
#   dash -c "sh scripts/sync_examples.sh --reverse"    # 反向同步（示例 → shared）
#   dash -c "sh scripts/sync_examples.sh --diff"       # 差异报告（只比较不写入）
#
# 以 templates/shared/main.py 为唯一来源，为每个示例生成 main.py。
# --reverse 模式：将首个示例的差异反向同步回 shared/main.py
# --diff 模式：列出 shared/main.py 与各示例的差异

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SHARED="$SKILL_DIR/templates/shared/main.py"

if [ ! -f "$SHARED" ]; then
  echo "not found: $SHARED"
  exit 1
fi

# 仅模板化示例（main.py 含 __APP_TITLE__ 占位符）参与同步。
# 03-FastCRM / 04-FastERP / 05-FastHRM / 06-FastInsights 为扁平布局 + 自有 main.py
# （bespoke，非模板生成），不从此 shared 模板同步，故不在本列表。
EXAMPLES="01-announcement-downloader"

sync_example() {
  title="$1"
  target="$2"
  target_file="$target/src/main.py"
  if [ ! -d "$target/src" ]; then
    echo "  skip (no src/): $target"
    return
  fi
  # 仅同步由 shared/main.py 模板生成的示例（含 __APP_TITLE__ 占位符）。
  # 03–06 与 12–15 使用自有入口（desktop.py / 自有 main.py），不走模板，故 skip。
  if ! grep -q "__APP_TITLE__" "$target_file" 2>/dev/null; then
    echo "  skip (bespoke entry, not template-based): $target"
    return
  fi
  sed "s/__APP_TITLE__/$title/g" "$SHARED" > "$target_file"
  echo "  OK $target_file"
}

diff_example() {
  target="$2"
  target_file="$target/src/main.py"
  if [ ! -f "$target_file" ]; then
    echo "  skip (no file): $target_file"
    return
  fi
  # 用标题占位符做归一化后比较
  title="$1"
  normalized=$(echo "$title" | sed 's/ /_/g')
  diff_output=$(diff <(cat "$SHARED") <(sed "s/$title/__APP_TITLE__/g" "$target_file") 2>/dev/null)
  if [ -z "$diff_output" ]; then
    echo "  OK $target_file — 一致"
  else
    echo "  DIFF $target_file:"
    echo "$diff_output" | head -20
  fi
}

if [ "$1" = "--reverse" ]; then
  echo "=== reverse sync: first example -> shared/main.py ==="
  first_example="$SKILL_DIR/examples/01-announcement-downloader"
  first_file="$first_example/src/main.py"
  if [ ! -f "$first_file" ]; then
    echo "  error: $first_file not found"
    exit 1
  fi
  # 反向同步：将示例 main.py 中非标题部分的改动合并回 shared/main.py
  # 使用 diff 检测差异，手动确认后合并
  echo "  comparing $first_file vs $SHARED ..."
  diff -u "$SHARED" <(sed 's/公告下载器/__APP_TITLE__/g' "$first_file") > /tmp/sync_reverse.diff 2>/dev/null
  if [ -s /tmp/sync_reverse.diff ]; then
    echo "  发现差异，合并到 shared/main.py ..."
    patch -u "$SHARED" < /tmp/sync_reverse.diff 2>/dev/null
    echo "  OK shared/main.py 已更新"
    cat /tmp/sync_reverse.diff
  else
    echo "  OK 无差异"
  fi
  rm -f /tmp/sync_reverse.diff
  echo "=== done ==="
  exit 0
fi

if [ "$1" = "--diff" ]; then
  echo "=== diff report ==="
  for pair in $EXAMPLES; do
    case "$pair" in
      "01-announcement-downloader") diff_example "公告下载器" "$SKILL_DIR/examples/$pair";;
    esac
  done
  echo "=== done ==="
  exit 0
fi

echo "=== sync examples ==="
for pair in $EXAMPLES; do
  case "$pair" in
    "01-announcement-downloader") sync_example "公告下载器" "$SKILL_DIR/examples/$pair";;
  esac
done
echo "=== done ==="

# 启动器（launcher.py 决策层 + 启动.bat 派发壳）由 scripts/gen_launchers.py 统一分发，
# 与 main.py 同步正交。前向同步（无参数）时顺带跑一次，保持 examples 启动器与 templates/shared/launcher.py 一致。
if [ -z "$1" ] && command -v python >/dev/null 2>&1; then
  echo "=== sync launchers (launcher.py + launcher.json + 启动.bat) ==="
  python "$SCRIPT_DIR/gen_launchers.py" || echo "  [warn] gen_launchers.py 失败（不影响 main.py 同步）"
fi
