# 实测要点

> 架构约束与质量检查相关的实测要点汇总。

---

## 一、pywebview 导入与启动

- **库导入名是 `webview`**（不是 `pywebview`）：`import webview`。
- `webview.start(func, args)` 的 `args` 必须是**可迭代对象（元组）**：正确写法是 `webview.start(run_checks, (window, args))`。若写成 `webview.start(run_checks, window, args)`，第三个位置参数会被误绑到 `localization` 形参，报 `'Namespace' object is not iterable`。

## 二、质检脚本用法

### 有窗口环境（推荐）

| 脚本 | 用途 |
|------|------|
| `scripts/ui_window_verify.py` | DOM 断言 + 可选截图，驱动 WebView2/系统 webview，零额外浏览器、零浏览器授权 |
| `scripts/ui_automate.py` | UI 交互自动化：点击/输入/导航/断言，验证按钮/表单/状态切换等交互行为 |

### 无 GUI 环境（headless）

| 脚本 | 用途 |
|------|------|
| `scripts/ui_audit.py` | 纯 HTTP + bs4 结构审计，零 GUI 依赖 |
| `scripts/ui_headless_verify.py` | headless HTML 结构验证 |

## 三、DOM 断言检查能力

DOM 断言式检查（图标名当文本 / 几何重叠 / WCAG 对比度 / 横向溢出 / 空白页）是可靠且独立于显示器的核心能力。只要环境能创建窗口（含隐藏窗口），即可在真实渲染的 DOM 上读计算样式并断言。

### 重叠检测

可滚动容器（`overflow:auto/hidden`）内被滚出可视区的子元素，其 `getBoundingClientRect` 仍落在容器坐标内，会与底部固定元素算出假重叠。须用 `isClipped()` 守卫沿祖先链检查是否越出任一 `overflow` 非 `visible` 祖先的可视边界，裁剪元素不参与计算。

### 对比度

浅色主题的文字颜色须确保与背景比值 ≥ 4.5:1（WCAG 2.1 AA）。`ui_window_verify.py` 的 DOM 断言可自动检出此类缺陷。

### 溢出

可滚动容器必须设为 `overflow:auto` 或 `overflow-y:auto`，禁止 `overflow:visible`（否则底部元素可能被裁切不可达）。

## 四、像素截图

- **像素截图是「可选增强」，必须依赖真实显示器**：WebView2 的 `CoreWebView2` 只能在 UI 线程访问（须用 `form.Invoke` 调度），`CapturePreviewAsync` 需要窗口有真实渲染表面——隐藏窗口 / 无显示器的 headless 环境会截出 0 字节。截图前须先 `Show` 窗口；无显示器时自动降级为 DOM 法判空白，**不影响主体检查**。图像格式须用 `CoreWebView2CapturePreviewImageFormat.Png`（**不是** `System.Drawing.Imaging.ImageFormat`）。
- **适用边界**：需在**有窗口会话**的环境运行（本地 Windows 桌面天然满足）；纯无界面 CI 服务器应改用 `ui_audit.py`。无头截图可用 html2canvas（evaluate_js 注入页面内渲染 canvas 导出 PNG）。
---

## 五、四个 UI 工具的分工与边界（防误用）

| 工具 | 是否启动浏览器/渲染 | 职责 | 何时用 |
|------|-------------------|------|--------|
| `ui_audit.py` | 否（纯 headless，`requests.get` 抓 HTML） | **设计反模式审计**（13 条禁令） | 无 GUI / 全量页面扫描 / 快速风格检查；**自动抓取外部 CSS**，可用 `--ignore-ban` 豁免误报 |
| `ui_headless_verify.py` | 否（headless 结构验证） | HTML 结构完整性 | 无 GUI 环境 |
| `ui_window_verify.py` | 是（pywebview 原生窗口） | **机器视觉质检**：DOM 断言 + 截图 | 有窗口会话，界面交付的**唯一机器手段** |
| `ui_automate.py` | 是（pywebview 原生窗口） | **交互自动化**：点击/输入/导航/断言 | 有窗口会话，验证按钮/表单/状态切换 |

**关键边界**：

- `ui_audit.py` 是 headless 设计审计，**不渲染、不启动浏览器**；`ui_window_verify.py` 是真实渲染质检。两者**功能不重合**、职责不同、**使用流程上不构成先后步骤**（可并列执行），且 headless 审计不能替代真实窗口质检（HTML 结构验证通过 ≠ 界面没问题）。
- 有 GUI 环境时，**UI 交付门禁以 `ui_window_verify.py`（+`ui_automate.py`）为唯一机器手段**；`ui_audit.py` 用于设计反模式的快速全量扫描。
- 无 GUI 环境（纯 CI）时，用 `ui_audit.py`（headless 设计审计）+ `ui_headless_verify.py`（headless 结构验证）作为降级替代。

**`ui_audit.py` 的边界（重要）**：它只抓页面 HTML 与 `<link rel=stylesheet>` 外部 CSS，**不执行 JS、不渲染**。因此凡依赖运行时渲染/脚本注入的样式或交互（如 JS 动态写入的 `<style>`、CSS-in-JS 运行时生成）不在其审计范围——此类项目须以 `ui_window_verify.py` 的真实渲染质检为准。
