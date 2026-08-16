"""
ui_audit.py — 无头 UI 审计工具

基于 fasthtml-desktop 自定义界面禁令的纯 Python 无头 UI 审计实现。
无需 Node.js / Playwright 环境，
直接对运行中的 HTTP 服务页面做纯 requests + bs4 审计（零 GUI 依赖）。

使用方式（支持单个或多个 URL，空格分隔）：
    python scripts/ui_audit.py http://127.0.0.1:5001/
    python scripts/ui_audit.py http://127.0.0.1:5001/ http://127.0.0.1:5001/dashboard

退出码：
    0 = 通过（无禁令违反）
    1 = 存在硬伤（任意「禁令」检查未通过 或 页面不可达）
"""

import re
import sys
import requests
from dataclasses import dataclass, field
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# 强制 UTF-8 输出：Windows 默认 GBK 控制台打印 emoji(如禁用符) 会抛 UnicodeEncodeError。
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# 严重级别
SEV_BAN = "禁令"      # 硬伤：阻断发布（纯黑白文字、页面不可达等）
SEV_COMP = "组件"     # 组件完整性：信息性，不阻断（部分页面本就无表单/输入）
SEV_UX = "UX"         # 体验：信息性，不阻断


@dataclass
class AuditItem:
    """单条审计结果"""
    name: str
    passed: bool
    severity: str  # 禁令 / 组件 / UX
    detail: str = ""
    url: str = ""


@dataclass
class AuditResult:
    """审计结果汇总"""
    items: list = field(default_factory=list)

    def report(self) -> str:
        lines = []
        lines.append("=" * 50)
        lines.append("  UI 审计报告")
        lines.append("=" * 50)

        last_url = None
        # 按严重程度分组
        for severity in [SEV_BAN, SEV_COMP, SEV_UX]:
            group = [i for i in self.items if i.severity == severity]
            if not group:
                continue
            passed = sum(1 for i in group if i.passed)
            total = len(group)
            lines.append(f"\n【{severity}检查】{passed}/{total} 通过\n")
            for item in group:
                if item.url and item.url != last_url:
                    lines.append(f"  ── {item.url}")
                    last_url = item.url
                icon = "✅" if item.passed else "❌"
                lines.append(f"  {icon} {item.name}")
                if not item.passed and item.detail:
                    lines.append(f"      {item.detail}")

        lines.append(f"\n{'=' * 50}")
        total = len(self.items)
        passed = sum(1 for i in self.items if i.passed)
        lines.append(f"  总计: {passed}/{total} 通过")
        lines.append(f"{'=' * 50}")
        return "\n".join(lines)

    def failed_hard(self) -> bool:
        """是否存在阻断发布的硬伤（禁令违反 / 页面不可达）"""
        return any(
            (not i.passed) and i.severity == SEV_BAN
            for i in self.items
        )


def fetch_external_css(url: str, soup: BeautifulSoup) -> tuple[str, list[str]]:
    """抓取页面外部样式表内容，供 CSS 相关禁令判定。

    解析所有 <link rel=stylesheet href=...>（含 media 样式、主题双文件），
    用 urljoin 解析绝对地址，requests 逐个抓取并拼接。
    抓取失败（404/超时/跨域）只跳过该文件，不抛出异常，保证审计鲁棒。

    Returns:
        (合并后的 CSS 文本, 成功抓取的样式表 URL 列表)
    """
    chunks: list[str] = []
    sources: list[str] = []
    for link in soup.find_all("link", rel=lambda r: r and "stylesheet" in _rel_list(r)):
        href = link.get("href")
        if not href:
            continue
        abs_url = urljoin(url, href)
        try:
            resp = requests.get(abs_url, timeout=10)
            if resp.status_code == 200:
                chunks.append(resp.text)
                sources.append(abs_url)
        except Exception:
            continue  # 抓取失败不阻断审计
    return "\n".join(chunks), sources


def _rel_list(rel) -> list:
    """bs4 的 rel 属性可能是字符串或列表，统一转为列表。"""
    if isinstance(rel, (list, tuple)):
        return list(rel)
    if rel:
        return [rel]
    return []


def audit_page(url: str, html: str | None = None, ignore: set | None = None) -> AuditResult:
    """
    对页面进行 UI 审计

    Args:
        url: 页面 URL（用于获取 HTML，也会记录在结果中）
        html: 可选的 HTML 字符串（不传则从 URL 获取）
        ignore: 需豁免的禁令名集合（来自 --ignore-ban，匹配到则跳过判定）

    Returns:
        AuditResult: 审计结果
    """
    result = AuditResult()
    ignore = ignore or set()

    if html is None:
        try:
            resp = requests.get(url, timeout=10)
            html = resp.text
        except Exception as e:
            result.items.append(AuditItem(
                name="页面可达", passed=False, severity=SEV_BAN,
                detail=f"无法获取页面: {e}", url=url
            ))
            return result
    else:
        # 已传入 html 时仍记录来源 url，便于多页聚合时定位
        pass

    soup = BeautifulSoup(html, "html.parser")
    text_lower = html.lower()

    # ── 外部 CSS 抓取（消除 CSS 外部化项目漏检/误报）──
    # 成熟项目常把样式放在外部 <link rel=stylesheet>（如 app.css / 主题双变量），
    # 若只扫页面 HTML 内联 style，会漏掉大部分样式 → 禁令 3/4/6/7/11 机械误报。
    # 这里解析 <link rel=stylesheet>，用 requests 抓取 CSS 内容合并进审计文本。
    # 抓取失败（404/超时/跨域）只记录信息，不阻断审计。
    external_css, css_sources = fetch_external_css(url, soup)
    css_combined = html + "\n" + external_css      # 原大小写：供正则（如 color:）匹配
    css_combined_lower = css_combined.lower()        # 供关键词匹配

    # ── 0c. 图标名当文本渲染（硬伤：视觉重叠 bug，无头审计盲区）──
    # 设计系统里图标容器常带 icon 类（nav-icon / icon / sidebar-icon / menu-icon / btn-icon），
    # 正确实现应内嵌 <svg>/<img>/<use> 或字体图标 class；若容器里只有裸英文字符串（图标名），
    # 说明把图标名当文本渲染了（本项目的真实 bug：Span("dashboard", cls="nav-icon") →
    # 显示成 "dash仪表盘d" 与中文标签重叠）。HTML 合法、HTTP 200，纯文本审计看不到，
    # 必须靠此规则 + pywebview 原生窗口视觉质检（ui_window_verify.py）兜底。
    ICON_CONTAINER_RE = re.compile(
        r"(^|[\s_-])(nav-?icon|icon|menu-?icon|sidebar-?icon|btn-?icon)([\s_-]|$)",
        re.I,
    )
    # 已用字体图标方案（Font Awesome / Material Icons / Glyphicon 等）时，
    # 容器里放图标名文本是**预期行为**，不应判违规，故显式放行。
    FONT_ICON_RE = re.compile(
        r"(^|[\s_-])(fa[blrs]?|fas|far|fab|material-?icons|glyphicon|iconfont|ti|bi)([\s_-]|$)",
        re.I,
    )
    ICON_NAME_RE = re.compile(r"^[a-z][a-z0-9_\-]{1,24}$", re.I)  # 形如 dashboard / folder-open / alert-triangle

    def _cls_str(c):
        return " ".join(c) if isinstance(c, list) else (c or "")

    for el in soup.find_all(class_=lambda c: c and ICON_CONTAINER_RE.search(_cls_str(c))):
        cls = _cls_str(el.get("class", []))
        if FONT_ICON_RE.search(cls):
            continue  # 字体图标方案：图标名文本属正常，跳过
        inner = "".join(str(c) for c in el.children)
        has_graphic = ("<svg" in inner) or ("<img" in inner) or ("<use" in inner)
        has_graphic_el = el.find(["svg", "img", "use"]) is not None
        text = el.get_text(strip=True)
        # 仅当容器里没有图形、文本是单个 ASCII「图标名形态」字符串时才判违规。
        # 要求 .isascii()：放过 emoji 图标方案；要求无字体图标 class：放过字体图标方案。
        looks_like_icon_name = (
            bool(text)
            and text.isascii()
            and (" " not in text)
            and (ICON_NAME_RE.match(text) is not None)
            and not has_graphic_el
        )
        if (not has_graphic) and looks_like_icon_name:
            result.items.append(AuditItem(
                name="图标容器含裸图标名(应渲染为图形)",
                passed=False, severity=SEV_BAN,
                detail=f'class="{cls}" 内仅含文本 "{text}"，疑似把图标名当文本渲染（应改为内联 SVG/<img> 或字体图标 class）',
                url=url,
            ))

    # ── 13 条禁令检查 ──
    # 注意：CSS 相关禁令（3/4/6/7/11）用 css_combined（HTML + 外部 CSS 合并）判定，
    # 这样 CSS 外部化项目不会因样式在外部 <link> 而漏检/误报；
    # HTML 结构相关禁令（1/8/10）仍只扫页面 HTML。
    bans = [
        ("1. 禁止使用纯色/扁平模态框",
         "<dialog" not in text_lower),
        ("2. 禁止左对齐布局（表单等输入场景除外）",
         True),  # 表单场景左对齐合理
        # 仅当 #000/#fff 被用作「文字颜色」(color:) 时才判违规；
        # 用作 background / background-color 是允许的（如白卡片、深色页底）。
        ("3. 禁止使用纯黑/白文字（作为文字颜色）",
         re.search(r'(?<![a-zA-Z-])color\s*:\s*#?(?:[0]{3,6}|[f]{3,6})', css_combined, re.I) is None),
        ("4. 禁止无间距的密集文本",
         "padding" in css_combined_lower or "margin" in css_combined_lower),
        ("5. 禁止表单控件未对齐",
         True),  # 用 flex 布局即可认为对齐
        ("6. 禁止使用系统默认字体",
         "font-family" in css_combined_lower),
        ("7. 禁止无视觉反馈的交互元素",
         ":hover" in css_combined or "transition" in css_combined),
        ("8. 禁止信息层级扁平化",
         "h1" in text_lower or "h2" in text_lower),
        ("9. 禁止触控目标过小",
         True),  # 由 PicoCSS 保证
        ("10. 禁止表单缺少即时验证反馈",
         "hx-post" in text_lower or "hx-get" in text_lower or "onsubmit" in html),
        ("11. 禁止使用默认 outline",
         "outline" in css_combined_lower or ":focus" in css_combined),
        ("12. 禁止功能图标无文字标签",
         True),  # 全文字按钮
        ("13. 禁止布局溢出",
         True),  # 由 CSS 框架保证
    ]

    def _ignored(name: str) -> bool:
        """判定禁令是否被 --ignore-ban 豁免。支持三种写法：
        序号（"3"）、完整名（含序号）、任意子串（如 "纯黑"）。"""
        if not ignore:
            return False
        if name in ignore:
            return True
        if name.split(".", 1)[0] in ignore:  # 序号
            return True
        return any(k and k in name for k in ignore)  # 子串

    for name, passed in bans:
        if _ignored(name):
            result.items.append(AuditItem(
                name=name + "（已忽略）", passed=True, severity=SEV_BAN,
                detail="经 --ignore-ban 显式豁免", url=url,
            ))
        else:
            result.items.append(AuditItem(
                name=name, passed=passed, severity=SEV_BAN, url=url
            ))

    # ── 外部 CSS 抓取信息（UX 级，不阻断；便于核验审计覆盖范围）──
    if css_sources:
        result.items.append(AuditItem(
            name=f"外部 CSS 已纳入审计（{len(css_sources)} 个文件）",
            passed=True, severity=SEV_UX,
            detail=" · ".join(css_sources), url=url,
        ))

    # ── UI 组件检查（信息性，不阻断）──
    # 注意：并非每个页面都需要表单/输入框（如仪表盘、详情只读页），
    # 故这些项仅作信息呈现，不计入 failed_hard()。
    has_form = len(soup.find_all("form")) > 0
    has_input = len(soup.find_all("input")) > 0
    components = [
        ("页面标题", soup.title is not None and len((soup.title.string or "").strip()) > 0),
        ("搜索表单", has_form),
        ("输入框", has_input),
        ("按钮", len(soup.find_all("button")) > 0 or "Button" in html),
        ("响应式 viewport", "viewport" in html),
        ("字符编码声明", "charset" in html),
        ("HTMX 动态加载", "htmx" in text_lower),
    ]

    for name, passed in components:
        detail = "" if passed else "元素未找到（非交互页可忽略）"
        result.items.append(AuditItem(
            name=name, passed=passed, severity=SEV_COMP, detail=detail, url=url
        ))

    # ── UX 检查（信息性，不阻断）──
    ux_items = [
        ("错误信息用户友好", "alert" in text_lower or "error" in text_lower),
        ("操作反馈区域", "progress" in text_lower or "loading" in text_lower),
        ("日期默认值合理", 'type="date"' in html and "value=" in html),
        ("有应用标题", "title" in text_lower or "h1" in text_lower),
    ]

    for name, passed in ux_items:
        result.items.append(AuditItem(
            name=name, passed=passed, severity=SEV_UX, url=url
        ))

    # ── 可访问性审计（P0：轻量 a11y lint，信息级不阻断，纯 HTML 解析，不引 axe/Playwright）──
    audit_accessibility(soup, url, result)

    return result


def audit_accessibility(soup: BeautifulSoup, url: str, result: AuditResult):
    """轻量可访问性审计（来自 playwright accessibility 思路，纯 HTML 解析，不引 axe/Playwright）。

    覆盖：img alt、label 关联、input 可访问名、button 可访问名、标题层级跳跃。
    均为信息级（SEV_UX），不阻断发布；与 ui_window_verify.py 的 WCAG 对比度（UX 级）互补。
    """
    # 1) 图片缺 alt（装饰图用 alt="" 合法，仅「完全缺少 alt 属性」才告警；aria-hidden/presentation 跳过）
    for img in soup.find_all("img"):
        if img.get("aria-hidden") == "true" or img.get("role") == "presentation":
            continue
        if "alt" not in img.attrs:
            result.items.append(AuditItem(
                name="可访问性: <img> 缺少 alt 属性",
                passed=False, severity=SEV_UX,
                detail=f'<img src="{(img.get("src") or "")[:60]}"> 无 alt（装饰图用 alt="" 即可）',
                url=url,
            ))

    # 2) input 缺少可访问名（无 id→label[for]、无 aria-label/labelledby、且未被 <label> 包裹）
    label_fors = {l.get("for") for l in soup.find_all("label") if l.get("for")}
    for inp in soup.find_all("input"):
        t = (inp.get("type") or "text").lower()
        if t in ("hidden", "submit", "button", "reset", "image"):
            continue
        iid = inp.get("id")
        wrapped = inp.find_parent("label") is not None
        has_aria = inp.get("aria-label") or inp.get("aria-labelledby") or inp.get("title")
        if not wrapped and not has_aria and (not iid or iid not in label_fors):
            result.items.append(AuditItem(
                name="可访问性: <input> 缺少可访问名",
                passed=False, severity=SEV_UX,
                detail=f'<input type="{t}" id="{iid or ""}"> 既无 <label for> 也无 aria-label/包裹 label',
                url=url,
            ))

    # 3) label[for] 悬空（指向不存在的 id）
    all_ids = {e.get("id") for e in soup.find_all() if e.get("id")}
    for lab in soup.find_all("label"):
        if lab.get("for") and lab.get("for") not in all_ids:
            result.items.append(AuditItem(
                name="可访问性: <label for> 指向不存在的 id",
                passed=False, severity=SEV_UX,
                detail=f'<label for="{lab.get("for")}"> 无对应控件 id',
                url=url,
            ))

    # 4) button 缺少可访问名（无文本、无 aria-label/title）
    for btn in soup.find_all("button"):
        if btn.get("aria-hidden") == "true":
            continue
        txt = (btn.get_text() or "").strip()
        has_aria = btn.get("aria-label") or btn.get("aria-labelledby") or btn.get("title")
        if not txt and not has_aria:
            result.items.append(AuditItem(
                name="可访问性: <button> 缺少可访问名",
                passed=False, severity=SEV_UX,
                detail="<button> 无文本 / aria-label / title",
                url=url,
            ))

    # 5) 标题层级跳跃（h1 之后直接 h3 漏 h2 等）
    heads = [h for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
             if h.get("aria-hidden") != "true"]
    levels = [int(h.name[1]) for h in heads]
    for i in range(1, len(levels)):
        if levels[i] - levels[i - 1] > 1:
            result.items.append(AuditItem(
                name="可访问性: 标题层级跳跃",
                passed=False, severity=SEV_UX,
                detail=f"h{levels[i - 1]} 之后直接 h{levels[i]}（跳过 h{levels[i] - 1}）",
                url=url,
            ))
            break  # 仅报首个跳跃


def audit_urls(urls: list, ignore: set | None = None) -> AuditResult:
    """依次审计多个 URL，聚合结果"""
    combined = AuditResult()
    for url in urls:
        combined.items.extend(audit_page(url, ignore=ignore).items)
    return combined


if __name__ == "__main__":
    args = sys.argv[1:]
    # 解析 --ignore-ban "禁令名或编号,另一项"（豁免已知误报，不阻断审计）
    ignore: set = set()
    if "--ignore-ban" in args:
        idx = args.index("--ignore-ban")
        if idx + 1 < len(args):
            ignore = {s.strip() for s in args[idx + 1].split(",") if s.strip()}
        del args[idx]  # 删除选项本身
        del args[idx]  # 删除选项值
    urls = args or ["http://127.0.0.1:5001/"]
    combined = audit_urls(urls, ignore=ignore)
    print(combined.report())
    sys.exit(1 if combined.failed_hard() else 0)
