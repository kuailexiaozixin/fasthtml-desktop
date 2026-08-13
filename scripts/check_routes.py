#!/usr/bin/env python3
"""check_routes.py — 路由卫生静态检查（捕获 APIRouter 默认路由陷阱）

fasthtml 的 @rt / @ar 在**未显式给出路径字符串**时，会用「函数名」自动生成路由
（下划线转连字符），并把类型注解参数当作查询参数。手写 RESTful href（如 /expenses/new）
会与自动生成的 /expenses_new 对不上 → 全站 404。本陷阱极隐蔽，运行时除非逐个点，否则发现不了。

本脚本静态扫描源码，标记所有「缺少显式路径字符串」的路由装饰器，作为打包前门禁。
不依赖运行时、不依赖浏览器，纯静态文本扫描。

用法：
    python scripts/check_routes.py src/
    python scripts/check_routes.py src/app.py

退出码：
    0 = 全部显式声明（通过）
    1 = 发现自动派生风险（阻断发布，需改为 @ar("/explicit/path")）
"""

import sys
import re
from pathlib import Path

# 强制 UTF-8 输出：Windows 默认 GBK 控制台打印 emoji(如 ⚠️) 会抛 UnicodeEncodeError
# 见实测：GBK 下 'gbk' codec can't encode character '\u26a0'。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# 路由装饰器名（fasthtml 的 @rt / @ar，以及 starlette 风格 @app.route / @router.route）
ROUTE_DECOR_RE = re.compile(r"@(rt|ar|app\.route|router\.route)\b")
# 提取引号内的字符串内容，用于判断是否为「路径」（而非 methods=["POST"] 这类参数）
QUOTED_CONTENT_RE = re.compile(r"""["']([^"']*)["']""")
# APIRouter(prefix=...) 是前缀声明，单独出现且无路径时仍属风险，但单独标记以便区分
PREFIX_RE = re.compile(r"\bprefix\s*=")


def has_explicit_path(snippet: str) -> bool:
    """片段中是否存在『以 / 开头的显式路径字符串』。

    仅当路径字符串以 / 开头才算显式路径（如 "/expenses"、f"/{pid}"）。
    这样可以避免把 methods=["POST"]、status="200" 等带引号的参数误判为路径。
    """
    for content in QUOTED_CONTENT_RE.findall(snippet):
        if content.startswith("/"):
            return True
    return False

# 跳过这些目录，避免误扫依赖
SKIP_DIRS = ("site-packages", ".venv", "venv", "__pycache__", "node_modules", "dist", "build")


def scan_file(path: Path) -> list[tuple[str, int, str, bool]]:
    """返回 (文件, 行号, 说明, 是否阻断) 列表

    分级：
    - 阻断(ERROR)：装饰器带了括号却没写显式路径（如 @ar(methods=["POST"]) 漏写路径），
      几乎总是「忘记写路径」的错误 → 阻断发布。
    - 告警(WARN)：bare @rt/@ar（无括号，约定俗成的函数名派生，如 index）、或 prefix= 派生，
      可能正常工作，但应被显式化 → 仅告警，不阻断。
    - 通过：含以 / 开头的显式路径字符串。
    """
    issues = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return issues
    text = "\n".join(lines)
    for m in ROUTE_DECOR_RE.finditer(text):
        name = m.group(1)
        line_idx = text[: m.start()].count("\n")
        # 向后取最多 3 行拼成装饰器片段（绝大多数装饰器在一行内闭合）
        snippet = "\n".join(lines[line_idx : line_idx + 3])
        has_paren = "(" in lines[line_idx]  # 只检查装饰器行本身，避免被下一行 def index(): 的括号误导
        if not has_paren:
            # @rt 无括号 → 约定俗成的函数名自动派生（如 def index → /index），仅告警
            issues.append((str(path), line_idx + 1,
                           f"@{name} 无括号：路由将由函数名自动派生（如 /index）；若手写 href 与之不一致会 404，建议显式 @ar(\"/\")", False))
            continue
        if PREFIX_RE.search(snippet):
            # prefix= 即使带了 / 串也是「前缀」而非完整路径，路由仍 = prefix + 函数名
            issues.append((str(path), line_idx + 1,
                           f"@{name}(prefix=...) 无显式路径：路由 = prefix + 函数名（如 /api/list_users），手写 href 易对不上，建议补全路径", False))
            continue
        if has_explicit_path(snippet):
            continue  # 含显式路径字符串（以 / 开头，含 f-string）→ 通过
        # 有括号、无 / 开头路径、无 prefix → 典型漏写路径错误 → 阻断
        issues.append((str(path), line_idx + 1,
                       f"@{name}(...) 无显式路径字符串：路由将由函数名派生（404 陷阱），请改为 @ar(\"/explicit/path\")", True))
    return issues


def main(argv=None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("用法: python scripts/check_routes.py <src目录或文件> [...]", file=sys.stderr)
        return 2
    all_issues: list[tuple[str, int, str, bool]] = []
    for target in args:
        p = Path(target)
        if p.is_dir():
            # 跳过依赖/构建产物目录，避免误扫第三方包
            files = [f for f in p.rglob("*.py") if all(s not in f.parts for s in SKIP_DIRS)]
        elif p.is_file():
            files = [p]
        else:
            print(f"[WARN] 跳过不存在的路径: {target}", file=sys.stderr)
            continue
        for f in files:
            all_issues.extend(scan_file(f))

    errors = [i for i in all_issues if i[3]]
    warns = [i for i in all_issues if not i[3]]

    print("=" * 56)
    print("  路由卫生检查（APIRouter 默认路由陷阱）")
    print("=" * 56)
    if not all_issues:
        print("  ✅ 未发现自动派生风险：所有路由均显式声明了路径")
        print(f"{'=' * 56}")
        return 0
    for fp, ln, msg, blocking in all_issues:
        tag = "❌ 阻断" if blocking else "⚠️ 告警"
        print(f"  {tag} {fp}:{ln}")
        print(f"      {msg}")
    print(f"\n  阻断 {len(errors)} 处 / 告警 {len(warns)} 处")
    print(f"  阻断项须改为 @ar(\"/explicit/path\") 显式声明路径后才能发布")
    print(f"{'=' * 56}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
