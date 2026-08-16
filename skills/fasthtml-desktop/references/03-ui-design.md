# 界面设计（原型驱动）

> 本文档在架构设计之后、编码之前使用。
> **用 FastHTML 写出可运行的纯界面原型，预览后迭代，确认无误后再接入业务逻辑。**
>
> 不出纸笔或文字草图——直接写代码、直接看效果。

---

## 二、设计上下文（可选）

在设计原型之前，先建立产品设计上下文，明确"谁用/做什么/为什么/不要做成什么样"与"颜色/字体/间距/圆角怎么定"。推荐在项目根目录创建两个文件：

**PRODUCT.md** — 产品上下文，回答"谁用/做什么/为什么/不要做成什么样"
**DESIGN.md** — 视觉规范，回答"颜色/字体/间距/圆角怎么定"

这两个文件中的设计令牌可以直接映射为 FastHTML 的 CSS 变量：

```css
:root {
  --color-surface: oklch(0.97 0.005 75);
  --color-accent: oklch(0.55 0.12 45);
  --font-family: -apple-system, sans-serif;
}
```


---

### 为什么用代码出原型

纸笔草图或 Figma 原型的问题在于：
- 画的布局和实际渲染效果有差距
- 无法验证交互手感（点击、跳转、反馈）
- 做原型的时间成本不比写代码低

**fasthtml-desktop 的界面设计直接用 FastHTML 写原型**：

```
写一个 main.py + app.py → uv run → 浏览器中看到界面 → 修改 → 再预览
```

当界面确认无误后，再接入后端逻辑。原型阶段的代码不会被浪费——它直接变成最终代码的一部分。

### 原型 vs 最终代码

```
原型阶段（纯界面）                    编码阶段（接入功能）
─────────────────────────────        ─────────────────────────────
Div(H1("标题"),                       Div(H1("标题"),
  Form(                                 Form(
    Input(name="url"),                    Input(name="url"),
    Button("提交"),                        Button("提交"),
  ),                                    hx_post="/process",
  id="prototype"                         hx_target="#result"
)                                      ),
                                       Div(id="result")
                                      )
```

原型中的组件大部分可以保留，只需要在编码阶段添加 `hx_*` 属性和 `Div(id="result")` 等交互元素。

---

### 原型深度按场景分级（避免无谓投入）

不是所有应用都需要一套像素级完整原型。按界面性质分级，把精力花在刀刃上：

| 场景类型 | 原型投入 | 说明 |
|---------|---------|------|
| **视觉密集型**（营销页、品牌站、强视觉表达） | 完整 `prototype_app.py` + 浏览器逐页预览迭代 | 视觉即产品，必须先把观感打磨到位再接逻辑 |
| **数据管理型**（仪表盘、CRUD 后台、表单工具、表格密集） | 骨架预览 + `ui_audit.py` 审计即可 | 布局以列表/表单/表格为主，PicoCSS 默认样式已足够；**不必做像素级原型**，确认结构后用 ui_audit 守住反模式门禁即可 |
| **工具型 / API 查询型**（单页表单 + 结果展示） | 轻量原型（表单 + 结果区占位） | 参考 `examples/01-announcement-downloader` |

> 无论哪种分级，**禁止跳过 `ui_audit.py` 反模式审计**（纯 headless，零 GUI 依赖）。视觉密集型额外建议结合 pywebview 原生窗口质检做机器视觉复检（见 quality-check/04-smoke-and-delivery.md 的 pywebview 原生视觉质检 `ui_window_verify.py`）。

---

## 二、三步原型法

### Step 1：确定页面结构（信息架构）

列出应用有哪些页面、每个页面有什么元素：

```
以文件批量重命名工具为例：

首页 = 标题 + 参数表单（文件夹路径、操作类型、参数输入）+ 预览区 + 结果区
```

不画图、不写文字稿，直接用 FastHTML 把页面结构写出来：

```python
# prototype_app.py — 纯界面原型（不带功能）
from fasthtml.common import *

app, rt = fast_app(default_hdrs=False, hdrs=(Style("""
    body { font-family: sans-serif; padding: 20px; max-width: 800px; margin: auto; }
    .card { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin: 16px 0; }
    .btn { background: #0078d4; color: #fff; padding: 10px 20px; border: none; border-radius: 4px; }
"""),))

@rt
def index():
    return Titled("文件批量重命名",
        Div(
            H2("参数配置"),
            Form(
                Div(Label("文件夹路径"), Input(placeholder="D:\\测试文件")),
                Div(Label("操作类型"), Select(
                    Option("添加前缀"), Option("添加后缀"), Option("替换文字"))),
                Div(Label("参数"), Input(placeholder="输入内容")),
                Button("预览", cls="btn"),
                style="display:flex; flex-direction:column; gap:12px;"
            ),
            cls="card"
        ),
        Div(
            H2("预览结果"),
            P("选择文件夹后显示预览...", style="color:#999;"),
            cls="card"
        ),
        Div(
            H2("执行结果"),
            P("执行后显示结果...", style="color:#999;"),
            cls="card"
        ),
    )
```

运行 `uv run python prototype_app.py`，浏览器打开 `http://127.0.0.1:5001`，直接看效果。

### Step 2：选 CSS 框架（可选）

fasthtml-desktop 内联样式可以满足大部分场景。如果追求更精致的视觉效果，可以使用以下 CSS 框架：

| CSS 框架 | 风格 | 离线策略 | 何时使用 | 位置 |
|---------|------|---------|---------|------|
| **PicoCSS** | 极简、语义化、自适应主题 | ✅ `Style()` 纯内联 | 默认推荐，最轻量 | `./fasthtml-refs/picocss-reference.md` |
| **MonsterUI** | 鲜艳、丰富组件库（70K+ 上下文） | ⚠️ CSS 内联 + JS `--add-data` 本地打包 | 需要复杂组件（按钮组、导航栏、模态框） | `./fasthtml-refs/monsterui-llms-ctx.txt` |
| **FastStrap** | Bootstrap 5.3 风格，93 个 UI 组件 | ⚠️ CSS 内联 + JS/字体 `--add-data` 本地打包 | 熟悉 Bootstrap、需要快速搭建 | `./fasthtml-refs/faststrap-llms.txt` |

快速启用 PicoCSS 原型：

```python
# 使用 PicoCSS 的原型（开发阶段用 pico=True 快速启动）
from fasthtml.common import *

app, rt = fast_app()  # fast_app 默认加载 PicoCSS，且会注入 htmx/fasthtml-js/surreal/css-scope-inline 共 5 个资源头（CDN 或本地均可，本技能不限制）
```

### 图标处理（禁止把图标名当文本渲染）

> **⚠️ 高频真实 bug**：菜单/按钮的图标字段常存成字符串名（如 `"dashboard"`、`"folder"`、`"alert"`），
> 若直接 `Span(icon_name, cls="nav-icon")` 渲染，浏览器会把图标名当**纯文本**显示，再被 `.nav-icon { width: 20px }` 截断，
> 与相邻标签重叠成 `dash仪表盘d`、`fold研发项目`。**这在 HTML 层完全合法（无报错、状态 200），需 pywebview 原生视觉质检（渲染后 DOM 检查，见 quality-check/04-smoke-and-delivery 测试项五）才能发现**，
> 是纯 HTML 无头审计（ui_audit.py / ui_headless_verify.py）的盲区。

图标三种正确做法：

| 方案 | 说明 | 推荐度 |
|------|------|--------|
| **内联 SVG（首选）** | 图标名 → SVG 字符串字典，用 `NotStr(SVG)` 注入；无外部依赖、可 `currentColor` 跟随主题 | ★★★ |
| Emoji | 直接用 `"📊"` 等 Unicode 字符；零依赖但风格不统一、跨系统字形不一 | ★★ |
| 本地字体图标 | 把 iconfont 的 `.woff2` 用 `@font-face` 本地引用 | ★ |

**禁止**：把图标名字符串当文本直接渲染。

内联 SVG 标准写法（fasthtml）：

```python
ICON_SVGS = {
    "dashboard": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" '
                 'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
                 'stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/>...</svg>',
    # ... 其余图标
}

# 渲染：必须用 NotStr，否则 SVG 标签会被转义成 &lt;svg&gt; 文本
Span(NotStr(ICON_SVGS.get(icon, "")), cls="nav-icon")
```

配套 CSS（让 SVG 居中且不被截断）：

```css
.nav-icon { display: inline-flex; align-items: center; justify-content: center;
            width: 20px; height: 20px; flex-shrink: 0; }
.nav-icon svg { width: 20px; height: 20px; }
```

> **验收**：渲染 HTML 里应出现 `<svg`，且**不应出现**任何图标名裸文本（`dashboard`/`folder`/`alert` 等）。
> 纯 HTML 断言可查这两条，但视觉对齐需经 pywebview 原生视觉质检确认（见 quality-check/04-smoke-and-delivery 测试项五）。

### Step 3：定义交互位置（为编码做准备）

在原型中标出哪些区域将来会用 HTMX 动态更新：

```python
@rt
def index():
    return Titled("文件批量重命名",
        Div(Form(...), cls="card"),
        Div(
            H2("预览结果"),
            Div(id="preview",        # ★ 将来用 hx_target 更新
                P("选择文件夹后显示预览...", style="color:#999;")),
            cls="card"
        ),
        Div(
            H2("执行结果"),
            Div(id="result",         # ★ 将来用 hx_target 更新
                P("执行后显示结果...", style="color:#999;")),
            cls="card"
        ),
    )
```

原型阶段标好 `id`，编码时直接加 `hx_*` 属性即可。

---

## 三、原型迭代流程

```
写 prototype_app.py → uv run → 浏览器预览
  ↓ 不满意
修改 → 保存 → 浏览器自动刷新（live=True）
  ↓ 满意
确认原型 → 重命名为 app.py → 开始接业务逻辑
```

开启自动刷新：

```python
# 原型阶段用 live=True，改代码后浏览器自动刷新
app, rt = fast_app(live=True)
```

### 迭代日志

每次原型迭代只改一个变量，保存一个版本：

```
版本 1：页面结构（标题 + 表单 + 预览区 + 结果区）
版本 2：加上 CSS（内联样式，调整间距和颜色）
版本 3：加上布局（单栏→上下分栏→侧边栏，选最合适的）
版本 4：拆分组件的边界
```

---

## 四、常用布局模板

### 单栏布局（最常用）

```python
def layout(title, *body):
    return Div(H1(title), *body, cls="container")
```

### 侧边栏布局

```python
def sidebar(*items):
    return Div(*[Div(item, cls="nav-item") for item in items], cls="sidebar")

def main_content(*children):
    return Div(*children, cls="main-content")

# 使用
@rt
def index():
    return Div(
        sidebar("仪表盘", "数据管理", "设置"),
        main_content(H2("仪表盘"), P("欢迎使用")),
        style="display:flex; gap:20px;"
    )
```

### 表单布局

```python
def form_group(label, input_element):
    return Div(Label(label), input_element, style="margin-bottom:12px;")

@rt
def settings():
    return Form(
        form_group("API Key", Input(type="password", placeholder="sk-...")),
        form_group("模型", Select(Option("gpt-4"), Option("gpt-3.5"))),
        Button("保存", cls="btn"),
        style="max-width:400px;"
    )
```

### 铺满式 AI 助手面板（chatbot 风格）

右侧主内容区要**占满「视口宽 − 侧边栏」**，而对话框输入框保持居中悬浮（参考 WorkBuddy 式 chatbot）。常见错误是给主内容区设 `flex:none`（或不保留拉伸），导致宽度被内部 `max-width:720px` 的输入框卡片「收缩」，窗口越大右侧空白越大。

```css
/* 容器层：在 .app-layout(flex 横向) 里保持拉伸，占满可用宽度 */
.main-content:has(.agent-wrap) {
  flex: 1 1 auto;   /* 必须保留拉伸，不可设 none */
  min-width: 0;     /* 允许在 flex 容器内收缩，避免溢出 */
  height: 100vh;
  overflow: hidden;
}
.agent-wrap { width: 100%; height: 100%; display: flex; flex-direction: column; }

/* 仅输入框卡片限宽居中悬浮，容器仍铺满 */
.agent-input-card { max-width: min(720px, 100%); width: 100%; }
.agent-compose { margin-bottom: 48px; }  /* 输入框与页面下边沿留悬空间隙 */
```

> 要点：`:has()` 覆盖默认 `flex` 时**务必保留拉伸**（`flex:1 1 auto` + `min-width:0`），否则容器会被内部限宽卡片「拉窄」，右侧出现大面积空白。

---

## 五、原型参考

`examples/` 下的示例可按界面形态挑选原型参考：

| 示例 | 布局 | 交互 | 参考价值 |
|------|------|------|---------|
| `01-announcement-downloader/app.py` | 单栏 | 表单 + 搜索 + 分页 + 批量下载 | API 查询型标准界面（轻量范式） |
| `03-FastCRM/web_app.py` | 侧栏 + 主区 | 列表 / 看板 / 详情 + 登录弹窗 | 带认证的管理后台标准骨架 |
| `06-FastInsights/web_app.py` | 多页面 | 仪表盘 + Plotly 图表 + SQL 实验室 | 数据分析型界面 |
| `15-FastMail/web_app.py` | 三栏 | 文件夹/标签筛选 + 列表 + 详情 | 资源浏览型界面（列表-详情-侧栏筛选） |

---

## 六、设计检查清单

- [ ] 页面结构已用 FastHTML 原型确认（不是纸笔或文字）
- [ ] 每个页面的布局模式已确定（单栏 / 上下分栏 / 侧边栏）
- [ ] 交互位置（`id`）已在原型中标出
- [ ] CSS 框架已选择（内联 / PicoCSS / MonsterUI / FastStrap）
- [ ] 离线策略已确定：PicoCSS 用 `Style()` 内联，MonsterUI/FastStrap 用 `--add-data` 本地化 JS
- [ ] 打包前检查清单中确认资源引用方式符合预期（CDN / 本地均可，由项目决定）
- [ ] 原型可在浏览器中正常运行预览
- [ ] 原型已保存（prototype_app.py），以备编码时参考
