"""无头 UI 验证脚本 — 通过 HTTP + HTML 解析验证 UI 完整性

无头 UI 验证（HTML 结构验证），适用于无 GUI 环境的 UI 完整性检查。
与 ui_audit.py（设计质量审计）互补——此脚本关注功能结构，ui_audit.py 关注设计质量。

用法：
    python scripts/ui_headless_verify.py http://127.0.0.1:PORT

依赖：requests, beautifulsoup4（标准技能依赖，无需额外安装）
"""
import re, sys, argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# 强制 UTF-8 输出：Windows 默认 GBK 控制台打印中文/emoji 会抛 UnicodeEncodeError。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# ── 验证项模板 ═══════════════════════════════════════

def make_checks(app_type: str = "generic") -> list[dict]:
    """根据应用类型返回验证项列表"""
    base = [
        {"type": "status", "desc": "HTTP 状态码为 200"},
        {"type": "element", "selector": "body", "desc": "页面包含 <body>"},
        {"type": "no_text", "pattern": "错误|500|Internal Server Error|Traceback|Exception",
         "desc": "页面无服务端错误信息"},
    ]
    templates = {
        "search": [
            {"type": "element", "selector": "form", "desc": "存在搜索表单"},
            {"type": "element", "selector": "input[type=text], input[type=search]",
             "desc": "存在文本输入框"},
            {"type": "element", "selector": "button[type=submit], button",
             "desc": "存在提交按钮"},
        ],
        "table": [
            {"type": "element", "selector": "table", "desc": "存在数据表格"},
            {"type": "element", "selector": "table thead, table th", "desc": "表格包含表头"},
        ],
        "form": [
            {"type": "element", "selector": "input, select, textarea",
             "desc": "存在表单输入控件"},
            {"type": "element", "selector": "form", "desc": "表单已包裹在 <form> 中"},
        ],
        "download": [
            {"type": "element", "selector": "a[download], a[href$='.zip'], a[href$='.pdf'], button:contains(下载)",
             "desc": "存在下载触发器"},
        ],
    }
    if app_type in templates:
        base.extend(templates[app_type])
    return base


# ── 验证引擎 ═════════════════════════════════════════

def verify_ui(url: str, checks: list[dict]) -> list[dict]:
    """执行 UI 验证，返回逐项检查结果"""
    results = []
    try:
        resp = requests.get(url, timeout=10)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')

        for check in checks:
            ctype = check.get("type")
            desc = check.get("desc", "")
            invert = check.get("invert", False)
            passed = False
            detail = ""

            if ctype == "status":
                code = check.get("code", 200)
                passed = resp.status_code == code
                detail = f"HTTP {resp.status_code}" if passed else f"期望 {code}，实际 {resp.status_code}"

            elif ctype == "element":
                sel = check.get("selector", "")
                elem = soup.select(sel)
                count = len(elem)
                passed = count > 0
                if invert:
                    passed = not passed
                detail = f"找到 {count} 个" if not invert else f"找到 {count} 个（期望 0）"

            elif ctype == "text":
                pattern = check.get("pattern", "")
                passed = bool(re.search(pattern, resp.text))
                if invert:
                    passed = not passed
                detail = f"模式: {pattern}" if passed else "未匹配"

            elif ctype == "no_text":
                pattern = check.get("pattern", "")
                found = re.search(pattern, resp.text)
                passed = not found
                detail = f"未出现错误" if passed else f"发现错误模式: {found.group(0) if found else ''}"

            elif ctype == "count":
                sel = check.get("selector", "")
                matches = soup.select(sel)
                count = len(matches)
                min_count = check.get("min", 1)
                max_count = check.get("max")
                passed = count >= min_count
                if max_count is not None:
                    passed = passed and count <= max_count
                detail = f"找到 {count} 个，期望 [{min_count}, {max_count or '∞'})"

            results.append({
                "desc": desc,
                "passed": passed,
                "detail": detail,
            })
            status = "✅" if passed else "❌"
            print(f"  {status} {desc}: {detail}")

    except Exception as e:
        results.append({"desc": "HTTP 请求", "passed": False, "detail": str(e)})
        print(f"  ❌ HTTP 请求失败: {e}")

    return results


def verify_links(soup: BeautifulSoup, expected_prefixes: list[str] | None = None) -> list[str]:
    """验证页面链接引用完整性"""
    if expected_prefixes is None:
        expected_prefixes = ["/", "./", "data:", "#", "http://127.0.0.1", "http://localhost"]
    issues = []
    for tag, attr in [("link", "href"), ("script", "src"), ("img", "src")]:
        for elem in soup.find_all(tag):
            url = elem.get(attr, "")
            if not url:
                continue
            if url.startswith("data:") or url.startswith("#"):
                continue
            if not any(url.startswith(p) for p in expected_prefixes):
                issues.append(f"意外的引用路径: <{tag} {attr}=\"{url}\">")
    return issues


# ── 主入口 ═══════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="无头 UI 验证脚本")
    parser.add_argument("url", help="目标 URL（如 http://127.0.0.1:5001）")
    parser.add_argument("--app-type", default="generic", choices=["generic", "search", "table", "form", "download"],
                        help="应用类型，决定验证项模板")
    parser.add_argument("--check-links", action="store_true",
                        help="额外执行链接引用完整性检查")
    args = parser.parse_args()

    print(f"=== 无头 UI 验证 === 目标: {args.url}")
    print(f"应用类型: {args.app_type}")
    print()

    checks = make_checks(args.app_type)
    results = verify_ui(args.url, checks)

    # 链接完整性检查
    if args.check_links:
        try:
            resp = requests.get(args.url, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            issues = verify_links(soup)
            if issues:
                print(f"\n  链接引用问题 ({len(issues)} 项):")
                for issue in issues:
                    print(f"    ⚠️  {issue}")
            else:
                print("\n  ✅ 链接引用完整性检查通过")
        except Exception as e:
            print(f"\n  ⚠️  链接检查失败: {e}")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\n结果: {passed}/{total} 通过", end="")
    if passed == total:
        print(" ✅")
        return 0
    else:
        print(f" ❌ ({total - passed} 项未通过)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
