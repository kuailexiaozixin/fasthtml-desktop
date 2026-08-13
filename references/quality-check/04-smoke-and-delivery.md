## 冒烟测试门禁（不可跳过）

> 本技能对打包产物的冒烟测试门禁规范如下。

打包完成后，AI **必须自行启动 EXE 进行冒烟测试**，确认以下所有测试项通过：

### 测试项一：HTTP 服务可用

启动 EXE，等待服务就绪后发送 HTTP 请求，确认返回 200：

### 测试项二：关键业务路径验证

仅验证主页 200 不够，必须验证至少一条关键业务路径：

```python
# 示例：对搜索型应用验证搜索功能
resp = requests.post(f"http://127.0.0.1:{PORT}/search", data={
    "market": "SZSE", "keyword": "000001",
    "start_date": "2026-01-01", "end_date": "2026-07-17", "page": 1,
}, timeout=10)
assert resp.status_code == 200
# 验证返回了结果而非错误提示
assert "error" not in resp.text.lower() or "未找到" not in resp.text
```

### 测试项三：启动 EXE 与窗口存在检查

启动 EXE 后，用 pywebview 窗口存在检查确认桌面窗口已创建：

```python
import requests, time

# 启动 EXE（子进程）
proc = subprocess.Popen([str(exe_path)])

# 轮询等待 HTTP 200
for i in range(20):
    time.sleep(1)
    try:
        resp = requests.get(f"http://127.0.0.1:{PORT}", timeout=3)
        if resp.status_code == 200:
            break
    except requests.ConnectionError:
        continue
else:
    raise RuntimeError("HTTP 服务未能在 20 秒内就绪")
```

#### pywebview 窗口存在检查（本技能新增）

```python
import win32gui

def find_window(timeout=15):
    """确认 pywebview 窗口已创建"""
    for _ in range(timeout):
        hwnd = win32gui.FindWindow(None, "我的应用")  # 窗口标题
        if hwnd:
            return hwnd
        time.sleep(1)
    return None

hwnd = find_window()
assert hwnd, "冒烟测试失败：未检测到 pywebview 窗口句柄"
```

### HTML 结构验证（无 GUI 环境首选，禁止跳过门禁）

当无 GUI 环境（无显示器 / CI / 远程服务器）时，使用纯 HTTP + HTML 解析验证 UI 完整性。这是结构级门禁，**必须执行**；但它只解析 HTML 结构，对「HTML 合法但视觉坏」天然不可见（见下方 测试项五 的盲区说明），不能替代 pywebview 原生窗口视觉质检。

```python
"""无头 UI 验证：通过 HTTP 获取 HTML 页面，解析验证 UI 元素"""
import requests
from bs4 import BeautifulSoup

def verify_ui(url: str, checks: list[dict]) -> list[dict]:
    """无头 UI 验证函数
    
    checks 格式示例：
    [
        {"type": "element", "selector": "form", "desc": "存在搜索表单"},
        {"type": "text", "pattern": "公告下载", "desc": "页面标题包含'公告下载'"},
        {"type": "count", "selector": "table tr", "min": 1, "desc": "表格至少有一行数据"},
        {"type": "no_text", "pattern": "错误|500|Internal Server Error", "desc": "页面无错误信息"},
    ]
    """
    results = []
    try:
        resp = requests.get(url, timeout=10)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        for check in checks:
            ctype = check.get("type")
            desc = check.get("desc", "")
            passed = False
            detail = ""
            
            if ctype == "element":
                sel = check.get("selector", "")
                elem = soup.select_one(sel)
                passed = elem is not None
                detail = f"找到 {len(soup.select(sel))} 个匹配" if passed else "未找到"
                
            elif ctype == "text":
                pattern = check.get("pattern", "")
                import re
                passed = bool(re.search(pattern, resp.text))
                detail = f"匹配到模式: {pattern}" if passed else "未匹配"
                
            elif ctype == "count":
                sel = check.get("selector", "")
                matches = soup.select(sel)
                count = len(matches)
                min_count = check.get("min", 1)
                passed = count >= min_count
                detail = f"找到 {count} 个，要求 ≥ {min_count}"
                
            elif ctype == "no_text":
                pattern = check.get("pattern", "")
                import re
                found = re.search(pattern, resp.text)
                passed = not found
                detail = f"错误模式未出现" if passed else f"发现错误: {found.group(0) if found else ''}"
            
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


# ── 使用示例 ──
if __name__ == "__main__":
    PORT = 5001  # 替换为实际端口
    checks = [
        {"type": "element", "selector": "form", "desc": "存在搜索表单"},
        {"type": "element", "selector": "input[type=text], input[type=search]", "desc": "存在输入框"},
        {"type": "element", "selector": "button[type=submit]", "desc": "存在提交按钮"},
        {"type": "text", "pattern": "公告|搜索|下载|工具", "desc": "页面包含核心功能关键词"},
        {"type": "no_text", "pattern": "错误|500|Internal Server Error|Traceback", "desc": "页面无服务端错误信息"},
    ]
    
    results = verify_ui(f"http://127.0.0.1:{PORT}", checks)
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\n结果: {passed}/{total} 通过")
    assert passed == total, f"❌ {total - passed} 项未通过"
    print("✅ UI 验证全部通过")
```

**使用场景**：
- CI/CD 无 GUI 环境
- 远程服务器部署验证
- 自动化回归测试
- 打包前快速检查（无需浏览器 GUI / 截图依赖）

> **⚠️ HTML 结构验证的盲区**：纯 HTML 结构解析对「HTML 合法但视觉坏」天然看不见，典型如：图标名当文本被截断重叠、元素重叠 / 溢出、对比度不足、flex 塌陷错位。因此**HTML 结构验证 通过 ≠ 界面没问题**。这类视觉缺陷由 **测试项五（pywebview 原生窗口视觉质检）** 全覆盖，无需人眼。

### 测试项五：pywebview 原生窗口视觉质检（机器替代人眼，推荐）

直接驱动应用所在的 PyWebView 原生窗口（Windows=WebView2，与 Edge 同引擎），通过 `evaluate_js` 在真实渲染的 DOM 上执行检查。**零额外浏览器、零 websockets、零浏览器授权**。

**前置依赖**：

- Python 包 `pywebview`（PyWebView 本身，通常已随应用安装）；
- 待检页面可由 `--url` 指定（手动启动 EXE 或 dev server 后传入）。
- 可选：`Pillow`（仅像素级空白判读与视觉回归用；缺失时自动降级，不影响 DOM 检查）。
- 可选：`html2canvas.min.js`（无头截图用；缺失时仅在有显示器的环境下可用 `CapturePreviewAsync` 截图）。

运行：

```bash
# 应用已在运行（推荐）
python scripts/ui_window_verify.py --url http://127.0.0.1:5001

# 指定截图输出 / 关闭截图
python scripts/ui_window_verify.py --url http://127.0.0.1:5001 --out shot.png
python scripts/ui_window_verify.py --url http://127.0.0.1:5001 --no-shot

# 调试时显示窗口（默认隐藏）
python scripts/ui_window_verify.py --url http://127.0.0.1:5001 --show
```

脚本自动化断言：

| 检查项 | 级别 | 检测方式 | 覆盖的 bug 类型 |
|--------|------|----------|-----------------|
| 图标名当文本 | ❌ BAN | 渲染后 DOM 检查 `.nav-icon` 内是否有 `<svg` / `<img>` | `dash仪表盘d` 式截断重叠 |
| 元素重叠 | ⚠️ UX | `getBoundingClientRect` 两两交叠（含 `isClipped()` 裁剪守卫） | 菜单/按钮互相覆盖 |
| 横向溢出 | ⚠️ UX | `scrollWidth - innerWidth` | 内容被裁切 / 出现横向滚动条 |
| 低对比度 | ⚠️ UX | `getComputedStyle` 计算 WCAG 对比度 | 灰底灰字、看不清链接 |
| 空白页 | ⚠️ UX | DOM 检查 + 可选截图灰度方差 | 路由白屏或渲染失败 |
| 视觉回归（像素级） | ⚠️ UX | 可选截图 + aHash 汉明距离 / PIL 灰度 MAD 比对基线 | 布局 / 样式意外变更（UX 级告警，不阻断） |

#### 5.0 断言前的渲染稳定等待

htmx / surreal 是 SPA 式更新：**断言 DOM / 截图前必须等渲染稳定**，否则会误报「元素缺失 / 空白页」。本脚本在 `run()` 中已内置等待：页面加载后 sleep 缓冲 + HTMX 渲染周期。

**纪律**：任何自定义视觉质检脚本都必须先等 DOM 稳定再 `evaluate_js`，绝不能「导航完立刻查」。这是降低 flaky 的第一原则（与 `09-test-driven-development.md` §9.1 重复跑纪律互补）。

退出码：
- `0` = 通过（或仅有 UX 提示）
- `1` = 存在 BAN 级缺陷（禁止发布）
- `2` = 环境/参数错误（未装 pywebview、URL 不可达、无法创建窗口）

> **机器已覆盖的缺陷**：图标真实图形、元素重叠、横向溢出、WCAG 对比度、空白页——全部由本脚本自动断言，无需人眼。仅「纯主观审美」（好不好看、配色风格偏好）不在机器断言范围内，按需人工判断，但**不将人工截图作为验收手段**。

#### 5.2 无头截图方案（html2canvas）

Windows 无显示器时，WebView2 的 `CapturePreviewAsync` 返回 0 字节（平台限制，非代码 bug）。此时可用 **html2canvas** 纯 JS 方案在页面内将 DOM 渲染到 `<canvas>` 再导出 PNG：

```python
# 核心逻辑（详见 .qa/test_native_canvas_shot.py 示例）
window.evaluate_js(html2canvas_lib_source)          # 注入库
window.evaluate_js(
    "window.__shot = null;"
    "html2canvas(document.body, {backgroundColor:null, scale:1})"
    ".then(c => { window.__shot = c.toDataURL('image/png'); })")
# 轮询 window.__shot 直到非 null → base64 解码写 PNG
```

此方案完全在 PyWebView 原生 JS 引擎内执行，不依赖显示器、不依赖额外浏览器。已在 01-hermes-desktop 上验证：输出 130KB 有效 PNG（787×565 RGBA）。

#### 5.3 侦察-行动方法论（Recon-Action，来自 webapp-testing）

pywebview 原生视觉验证遵循「侦察 → 行动」：

1. **侦察**：`evaluate_js` 在**真实渲染的 DOM** 上取图标 / 几何 / 对比度 / 溢出数据；可选 html2canvas 截图；
2. **定选择器**：从渲染状态确定断言用的选择器（优先 role / 文字 / 语义 class，禁止脆弱 `:nth-child` / XPath / 索引定位）；
3. **行动 / 断言**：用上一步确定的选择器做机器断言（重叠 / 图标真实图形 / 对比度 / 空白页）。

这与 webapp-testing 的 recon-action 同构，但落地为「可重复、可门禁（exit code）的机器断言」，不依赖人工截图。

---

### 测试项六：进程可正常退出

```python
proc.terminate()
proc.wait(timeout=5)
assert proc.returncode is not None, "进程未能正常退出"
# 确认端口已释放
```

---

### 测试项七：CI 无头验证编排（来自 playwright ci-cd 思路）

三层验证在 CI 中分工明确，**无 GUI 也能跑全量门禁**：

| 层 | 工具 | 无 GUI 可跑 | CI 行为 |
|----|------|------------|---------|
| 逻辑 | `pytest`（单元 / 集成 / 数据驱动） | ✅ | 非零退出阻断 |
| HTML 结构 | `ui_audit.py`（headless） | ✅ | 非零退出阻断（页面不可达） |
| 视觉 / 运行时 | `ui_window_verify.py`（pywebview 原生） | ⚠️ 需能创建窗口 | `exit 2` 视为「环境不可用」，**跳过不阻断** |

```bash
# CI 无头编排示例（无窗口时视觉质检自动跳过）
uv run pytest                                       # 逻辑门禁（必跑）
python scripts/ui_audit.py http://127.0.0.1:$PORT  # HTML 结构门禁（必跑）
python scripts/ui_window_verify.py --url http://127.0.0.1:$PORT --out shot.png \
  && echo "UI 通过" || { code=$?; [ $code -eq 2 ] && echo "UI 跳过（无窗口）"; }
```

- **关键**：`ui_window_verify.py` 退出 `2`（环境错误：未装 pywebview、URL 不可达、无法创建窗口）必须被 CI 当作 skip 而非 fail，否则无 GUI 的 CI 会误阻断逻辑套件。
- 无头截图可用 html2canvas（evaluate_js 注入页面内渲染 canvas 导出 PNG，无需显示器），详见 §5.2。
- 与本文「HTML 结构验证（无 GUI 首选）」衔接，形成「逻辑 + 结构 + （可选）视觉」的完整收口。

---

## 打包前检查清单

> 每个检查项标注执行频次：**[每次写入]** = 每次代码变更后执行 / **[编码完成]** = 模块开发结束时执行 / **[打包前]** = 仅打包前执行

| 频次 | 检查项 | 命令/方法 |
|------|--------|---------|
| [每次写入] | 语法检查 | `py_compile.compile()` |
| [编码完成] | Ruff 代码质量 | `ruff check src/` |
| [打包前] | 依赖清单审计（仅含必要包） | `uv pip list` 检查无关大包 |
| [每次写入] | `main.py` 中 `reload=False` | 检查 `uvicorn.run()` 参数 |
| [打包前] | 所有 CSS/JS 已正确打包（无意外缺失） | 启动服务后 `python scripts/ui_audit.py http://127.0.0.1:PORT` |
| [每次写入] | 路径代码使用 `sys.frozen` 检测 | 检查 `BASE_DIR` 计算方式 |
| [每次写入] | 无 `print()` 输出 emoji（GBK 编码） | 全局搜索 emoji 字符 |
| [编码完成] | UI 反模式检查通过 | 4.1 绝对禁令 + 4.3 AI Slop 测试 |
| [编码完成] | 产品 UI 专用检查（如适用） | 4.2 所有 13 项 |
| [编码完成] | 通用设计规则自检清单 | 4.4 颜色/排版/布局/动效/交互 |
| [打包前] | **后端路由显式化（APIRouter 陷阱）** | `python scripts/check_routes.py src/` → exit 0 |
| [打包前] | **前端→后端路由链路校验（死链 404）** | `python scripts/check_routes_linkage.py src/` → exit 0 |
| [打包前] | **技能引用/依赖完整性** | `bash scripts/check_refs.sh`（模板一致）+ `bash scripts/scan_deps.sh <proj>`（依赖漂移） |
| [打包前] | **全量测试门禁** | `uv run pytest` → 全绿，非零退出禁止发布 |

#### 发布前自检（统一 release_gate，P6）

以下门禁**任一非零退出即禁止发布**。按依赖顺序串行执行（前一关不过不进下一关），避免把问题拖到打包/交付阶段才爆：

```bash
# 0. 导入完整性（精确替换断裂引用，秒级）
bash scripts/verify_imports.sh <proj_dir>          # exit 0

# 1. 逻辑门禁（单元/集成）
uv run pytest <proj_dir>/tests -q                   # 全绿 exit 0

# 2. 服务端路由显式化（APIRouter 默认路径陷阱，§4.5）
python scripts/check_routes.py <proj_dir>/src       # exit 0

# 3. 前端→后端链路校验（死链 404 隐患，§4.6）
python scripts/check_routes_linkage.py <proj_dir>/src   # exit 0

# 4. 界面交付质检（pywebview 原生窗口视觉质检，无 GUI 强制 HTML 结构验证）
python scripts/ui_window_verify.py --url http://127.0.0.1:PORT   # 或 ui_headless_verify.py / ui_audit.py（无 GUI 时）

# 5. 技能自身引用/依赖漂移检查
bash scripts/check_refs.sh && bash scripts/scan_deps.sh <proj_dir>

# 6. 打包（build_windows_exe.sh 内含清理前杀残留进程硬化，§P2）
./scripts/build_windows_exe.sh <proj_dir> <AppName>     # 末尾冒烟测试 HTTP 200
```

> 该顺序由多轮实战归并：原本散落在 SKILL.md ⑦⑧⑨ 各步骤的门禁，统一为**单一可复现的发布流水线**。新增门禁（如 §4.6 链路校验）只往此处追加一行，不改变既有顺序。

## 发布前自检

- [ ] 打包产物存在且大小合理
- [ ] 冒烟测试全部通过
- [ ] 日志文件可正常写入
- [ ] 退出方式已说明（Ctrl+C 或关闭窗口）
