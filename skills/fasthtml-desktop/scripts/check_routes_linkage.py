#!/usr/bin/env python3
"""check_routes_linkage.py — 前后端路由链路校验（捕获 404 契约断裂）

fasthtml-desktop 的 `check_routes.py` 校验「服务端路由是否显式声明路径」，
但**不校验「页面前端引用的端点是否真有后端路由」**。两者方向互补，缺一不可：

- 组件里写 `hx_get="/close-{modal_id}"`（或手写 `href="/somewhere"`），
  但 `app.py` 从未注册对应 `@rt/@ar`，运行时点击即 404；
- 这类 404 在 HTTP 200 冒烟测试、纯 HTML 结构审计下**完全隐形**，除非真人逐个点击。

本脚本静态扫描源码，把「前端引用的端点集合」与「后端路由集合」做差集，
报告所有**前端引用但无后端路由**的端点（404 隐患，阻断级）。

用法：
    python scripts/check_routes_linkage.py src/
    python scripts/check_routes_linkage.py src/app.py src/routes_*.py

退出码：
    0 = 所有前端引用都能命中某个后端路由（通过）
    1 = 发现「前端引用无后端路由」的 404 隐患（阻断发布）
    2 = 用法/环境错误（未提供路径、未找到任何后端路由等）

设计取舍：
- 这是**纯静态文本扫描**，不执行代码、不依赖浏览器。因此无法解 f-string 的运行时值
  （如 `f"/projects/{p.id}"` 里的 `p.id`）。处理方式：把任意含 `{` 的段视为「通配值段」，
  与后端路由里含 `{` 的参数段（如 `{pid}`）互相匹配。语义正确： fasthtml 按完整路径匹配，
  不按前缀匹配；段数必须一致，每段字面相等或任一侧为通配段即视为匹配。
- 静态资源（/vendor、/static、*.js、*.css 等）与页内锚点（#...）、外部 URL 一律跳过。
- 仅扫描显式写在 Python 源码里的引用；JS 里动态拼接的 URL 不在本脚本范围（属运行时渲染范畴）。
"""

import sys
import re
from pathlib import Path

# 强制 UTF-8 输出：Windows 默认 GBK 控制台打印中文/emoji 会抛 UnicodeEncodeError。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# ── 服务端路由提取 ──
# 1) 先扫描文件里所有 APIRouter 赋值，建立 变量名 -> prefix 映射。
#    例如：router = APIRouter(prefix="/api")  ->  {"router": "/api"}
#           ar = APIRouter()                  ->  {"ar": ""}
# 2) 路由装饰器 = 内置（rt / ar / app）或上述变量名（含 .route 形式）。
APIROUTER_ASSIGN_RE = re.compile(
    r"([A-Za-z_]\w*)\s*=\s*APIRouter\s*\(([^)]*)\)"
)
# 装饰器：@rt / @ar / @app / @<router变量名> （可带 .route 后缀）
ROUTE_DECOR_RE = re.compile(r"@([A-Za-z_]\w*)(?:\.route)?\b")
# 哪些是“内置、无 prefix”的路由装饰器
BUILTIN_ROUTERS = {"rt", "ar", "app"}
# 装饰器内第一个以 / 开头的字符串即路径（兼容 @ar("/x")、@ar(f"/{pid}")、@ar('/x')）
PATH_STR_RE = re.compile(r"""["'](/[^"']*)["']""")


def _prefix_of(assignment_body: str) -> str:
    """从 APIRouter(...) 的参数体里提取 prefix= 的值（无则空串）。"""
    m = re.search(r"prefix\s*=\s*(?:f)?\s*[\"']([^\"']*)[\"']", assignment_body)
    return m.group(1) if m else ""

# ── 前端引用提取（客户端 → 服务端端点）──
# 仅关注这些属性值，且其值需以 / 或 f"/ 开头（排除页内锚点 # 与外部 URL）。
REF_ATTRS = ("href", "hx_get", "hx_post", "hx_put", "hx_delete", "action", "url")
# 形如 href=f"/x" 或 href="/x" 或 action="/x" 或 url="/x"
REF_RE = re.compile(
    r"""(?:href|hx_get|hx_post|hx_put|hx_delete|action|url)\s*=\s*(f?)\s*["']([^"']*)["']"""
)
# redirect / RedirectResponse(url="/x", ...)
REDIRECT_RE = re.compile(r"Redirect(?:Response)?\s*\([^)]*url\s*=\s*(f?)\s*[\"']([^\"']*)[\"']", re.S)

# 静态资源目录前缀与扩展名（不计为路由端点）
STATIC_PREFIXES = ("/vendor/", "/static/", "/assets/", "/css/", "/js/", "/img/",
                   "/images/", "/fonts/", "/favicon", "/htmx", "/_app/")
STATIC_EXT = (".js", ".mjs", ".css", ".map", ".png", ".jpg", ".jpeg", ".gif",
              ".svg", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".json")

SKIP_DIRS = ("site-packages", ".venv", "venv", "__pycache__", "node_modules",
             "dist", "build", ".git")


def _strip_query_fragment(path: str) -> str:
    """去掉查询串与片段，仅保留路径。"""
    path = path.split("#", 1)[0]
    path = path.split("?", 1)[0]
    return path


def _is_static_or_external(ref: str) -> bool:
    if not ref:
        return True
    low = ref.lower()
    if low.startswith(("http://", "https://", "//", "mailto:", "data:", "tel:",
                       "ws://", "wss://", "ftp://", "file://", "blob:", "javascript:")):
        return True
    if low.startswith("#"):
        return True  # 页内锚点，非路由端点
    if any(ref.startswith(p) for p in STATIC_PREFIXES):
        return True
    if any(ref.lower().endswith(e) for e in STATIC_EXT):
        return True
    # 正则模式字符串（含正则元字符 ( [ \ ）——非路由路径
    if any(c in ref for c in "([\\"):
        return True
    # 非路径形态：不以 / 开头，且不含 /（裸单词）或含 {（f-string 变量插值）→ 无法静态解析，跳过
    if not ref.startswith("/") and ("{" in ref or "/" not in ref):
        return True
    return False


def _segments(path: str) -> list[str]:
    p = path.strip("/")
    return p.split("/") if p else []


def _seg_match(client_seg: str, server_seg: str) -> bool:
    """单段匹配：字面相等，或任一侧含 {（通配值段 / 路由参数段）即视为匹配。"""
    if "{" in client_seg or "{" in server_seg:
        return True
    return client_seg == server_seg


def _path_matches(client_path: str, server_path: str) -> bool:
    """完整路径匹配（fasthtml 按完整路径、段数一致匹配，不按前缀）。"""
    c = _segments(client_path)
    s = _segments(server_path)
    if len(c) != len(s):
        return False
    return all(_seg_match(a, b) for a, b in zip(c, s))


def collect_server_routes(files: list[Path]) -> set[str]:
    """扫描所有文件，收集全局后端路由集合（含 APIRouter 前缀化）。

    正确处理：
      - 内置装饰器 @rt/@ar/@app.route（无 prefix）
      - 任意变量名 = APIRouter(prefix=...) 创建的子路由，如
            router = APIRouter(prefix="/api")
            @router("/items/{iid}")   ->  /api/items/{iid}
        （旧版只认 @rt/@ar/@router.route，会漏掉常规写法的 @router(...) 导致
          误判“未检测到任何后端路由”/ 误报 404）
    """
    routes: set[str] = set()
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        # 该文件内的 router 变量名 -> prefix
        router_prefix: dict[str, str] = {}
        for am in APIROUTER_ASSIGN_RE.finditer(text):
            router_prefix[am.group(1)] = _prefix_of(am.group(2))
        for dm in ROUTE_DECOR_RE.finditer(text):
            name = dm.group(1)
            # 判定前缀：内置无 prefix；否则查 router 变量映射；其余跳过
            if name in BUILTIN_ROUTERS:
                prefix = ""
            elif name in router_prefix:
                prefix = router_prefix[name]
            else:
                continue  # 非路由装饰器（@cached/@wraps/@dataclass/@pytest.fixture ...）
            # 向后取 3 行拼成装饰器片段
            line_idx = text[: dm.start()].count("\n")
            snippet = "\n".join(text.splitlines()[line_idx: line_idx + 3])
            sm = PATH_STR_RE.search(snippet)
            if not sm:
                continue
            p = sm.group(1)
            if not p.startswith("/"):
                continue
            full = (prefix.rstrip("/") + p) if prefix else p
            routes.add(full)
    return routes


def collect_client_refs(files: list[Path]) -> list[tuple[str, str, int, str]]:
    """返回 (文件, 引用路径, 行号, 来源属性) 列表。"""
    refs: list[tuple[str, str, int, str]] = []
    for f in files:
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        text = "\n".join(lines)
        # href=/hx_*/action= 引用
        for m in REF_RE.finditer(text):
            attr = m.group(0).split("=")[0].strip()
            raw = m.group(2)
            line_no = text[: m.start()].count("\n") + 1
            refs.append((str(f), raw, line_no, attr))
        # redirect(url=...) 引用
        for m in REDIRECT_RE.finditer(text):
            raw = m.group(2)
            line_no = text[: m.start()].count("\n") + 1
            refs.append((str(f), raw, line_no, "redirect.url"))
    return refs


def main(argv=None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("用法: python scripts/check_routes_linkage.py <src目录或文件> [...]", file=sys.stderr)
        return 2

    py_files: list[Path] = []
    for target in args:
        p = Path(target)
        if p.is_dir():
            py_files.extend(
                f for f in p.rglob("*.py") if all(s not in f.parts for s in SKIP_DIRS)
            )
        elif p.is_file() and p.suffix == ".py":
            py_files.append(p)
        else:
            print(f"[WARN] 跳过不存在的路径: {target}", file=sys.stderr)

    if not py_files:
        print("[FAIL] 未找到任何 .py 文件", file=sys.stderr)
        return 2

    server_routes = collect_server_routes(py_files)
    if not server_routes:
        print("[WARN] 未检测到任何后端路由（@rt/@ar）。无法做链路校验，请确认已传入含路由的文件。", file=sys.stderr)
        return 2

    client_refs = collect_client_refs(py_files)

    # 去重（同路径不同位置仍想看，但通常只看路径即可；这里按 (路径, 属性) 去重以聚焦）
    seen = set()
    uniq: list[tuple[str, str, int, str]] = []
    for fp, raw, ln, attr in client_refs:
        path = _strip_query_fragment(raw)
        if _is_static_or_external(path):
            continue
        key = (path, attr)
        if key in seen:
            continue
        seen.add(key)
        uniq.append((fp, path, ln, attr))

    # 计算缺失（前端引用但无后端路由命中）
    missing: list[tuple[str, str, str]] = []  # (引用路径, 属性, 示例文件:行)
    for fp, path, ln, attr in uniq:
        if any(_path_matches(path, s) for s in server_routes):
            continue
        missing.append((path, attr, f"{Path(fp).name}:{ln}"))

    print("=" * 60)
    print("  前后端路由链路校验（前端引用 ↔ 后端路由）")
    print("=" * 60)
    print(f"  后端路由数: {len(server_routes)}")
    print(f"  前端引用(去重, 非静态): {len(uniq)}")
    print(f"  404 隐患(前端引用无后端路由): {len(missing)}")
    print("-" * 60)

    if not missing:
        print("  ✅ 所有前端引用的端点都能命中某个后端路由")
        print("=" * 60)
        return 0

    for path, attr, loc in missing:
        print(f"  ❌ 阻断  {attr}=\"{path}\"")
        print(f"          未找到匹配的后端路由（疑似 404）。引用自 {loc}")
    print("-" * 60)
    print("  请将上述前端端点补上对应 @rt/@ar 路由，或修正端点拼写/路径前缀。")
    print("=" * 60)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
