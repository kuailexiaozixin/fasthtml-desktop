# pywebview 桌面壳参考

> 本文档覆盖 pywebview 在 FastHTML 桌面应用中的全部核心 API，**跨平台适用**（Windows / macOS / Linux）。
> 后端按操作系统自动选择：Windows=WinForms+(WebView2/mshtml)、macOS=cocoa、Linux=gtk。
> 后端矩阵、各 OS 打包与 cefpython3 限制见 `references/11-cross-platform.md`。
> 所有 API 均经 pywebview 6.2.1 真实内省或双态（开发态+打包态）实证验证。

---

## 适用场景与常用组合

### 场景速查表

| 场景 | 需要的 API | 对应示例 |
|------|-----------|---------|
| 简单信息展示（查看器/阅读器） | `create_window` + `start` | 01-04 最小示例 |
| 查询/搜索工具（需要搜索框+结果列表） | `create_window` + 表单 HTMX | 05 公告下载器 |
| 数据处理工具（上传→处理→下载） | `create_window` + 文件对话框 + JS 桥接 | 02/05/06 |
| 多步骤/向导 | `create_window` + 多页面路由 + `window.evaluate_js()` | — |
| 系统托盘+后台任务 | `pystray` 库 + `minimized=True` + 定时器（见下方托盘章） | — |
| 跨平台发布 | 确认各平台 WebView 引擎差异 | — |

### 常用组合

```python
# 场景：搜索查询桌面工具（05/06 类）
webview.create_window(
    title='工具名称',
    url=f'http://127.0.0.1:{PORT}',
    width=1200, height=800,
    resizable=True,
    easy_drag=False,       # 禁用窗口拖动（默认启动方式）
)
webview.start(debug=True) # debug=True 开启 DevTools

# 场景：系统托盘常驻
# webview.start(debug=True, private_mode=False)
# 通过托盘菜单唤醒窗口
```

### 版本差异说明

适用 pywebview 版本：**>=5.0, <7.0**。

| API / 行为 | pywebview 5.x | pywebview 6.x |
|-----------|--------------|--------------|
| `create_window` 基础窗口 | ✅ | ✅ |
| `start(debug=True)` DevTools | ⚠️ 需要手动配置 | ✅ 默认支持 |
| 系统托盘 | ❌ 不支持 | ❌ 不支持（改用 `pystray` 第三方库） |
| Cookie 管理 | ❌ 不直接支持 | ✅ `window.get_cookies()`（返回 list，无参） |
| `minimized=True` | ✅ | ✅ |
| `easy_drag` (原生拖动) | ❌ | ✅ v6.3+ |
| JS 桥接 `evaluate_js()` | ✅ | ✅ |
| `window.load_html()` | ✅ | ✅ |
| `window.load_url()` | ✅ | ✅ |
| `start(gui='edgechromium')` | ⚠️ 需手动指定 | ✅ 自动检测 |
| 文件对话框 | ✅ | ✅ |
| 多窗口 | ⚠️ 不稳定 | ✅ |
| `start(private_mode=)` | ❌ | ✅ |
| `start(storage_path=)` | ❌ | ✅ v6.1+ |

> **建议**：新项目使用 pywebview 6.x，示例中依赖声明为 `pywebview>=5.0` 以保持兼容。

---

## 快速上手

> **适用场景**：新建项目的第一步，确认 pywebview 能正常打开窗口加载本地服务。
> 如果连这个都跑不通，说明环境配置有问题（WebView2 缺失、pythonnet 版本不兼容等）。

桌面 EXE 场景中，URL 指向本地 FastHTML 服务：

```python
webview.create_window('我的应用', 'http://127.0.0.1:5001')
webview.start()
```

---

## create_window 参数

> **适用场景**：创建主窗口。这是 pywebview 最常用的 API，每个应用至少调用一次。
> 参数配置决定了窗口的基本行为（大小、可调性、全屏、置顶、关闭确认等）。

```python
window = webview.create_window(
    title='窗口标题',           # 窗口标题
    url='http://127.0.0.1:5001', # URL 或 HTML 内容
    width=1024,                  # 窗口宽度
    height=768,                  # 窗口高度
    x=None, y=None,              # 窗口位置（None=居中）
    screen=None,                 # 指定显示器（Screen 实例，None=默认屏幕；多显示器场景用 webview.screens 选屏）
    resizable=True,              # 可否调整大小
    fullscreen=False,            # 是否全屏
    min_size=(800, 600),         # 最小尺寸
    hidden=False,                # 是否初始隐藏
    frameless=False,             # 无边框模式
    easy_drag=False,             # 拖拽区域（frameless=True 时可用）
    shadow=False,                # 窗口投影（bool，仅 Windows 有效；frameless=True 时可设 True 加投影）
    focus=True,                  # 窗口创建后是否自动获取焦点（bool，默认 True）
    minimized=False,             # 启动即最小化（bool，配合托盘常驻场景）
    maximized=False,             # 启动即最大化（bool）
    on_top=False,                # 窗口置顶
    confirm_close=False,         # 关闭前确认
    background_color='#FFF',     # 背景色
    transparent=False,           # 透明窗口（bool，需配合 frameless=True；详见下方「透明窗口」章节）
    js_api=None,                # JS↔Python 桥接对象
    text_select=False,           # 是否允许选择文字
    zoomable=False,              # 是否允许 Ctrl+/- 或 Ctrl+滚轮缩放页面（bool，默认 False，实证 6.2.1）
    draggable=False,             # 整窗可拖（bool；仅 frameless=True 时有意义，与 drag-region 二选一）
    vibrancy=False,              # ⚠ bool，且仅 macOS cocoa 后端实现（实证 6.2.1：edgechromium/winforms 源码 0 命中）。Windows 桌面 EXE 设 True 无任何效果，勿用
    localization=None,           # 本地化字符串（见下方说明）
)
```

---

## 窗口控制

> **适用场景**：运行时动态调整窗口状态——最小化、全屏、置顶、调整大小、关闭窗口。
> 常用于：退出时最小化到托盘、点击按钮切换全屏、多窗口布局调整。

```python
window = webview.create_window('测试', 'http://127.0.0.1:5001')
webview.start()

# 运行时控制（需通过全局变量或 window 对象）
window.title = '新标题'
window.on_top = True
window.resize(1280, 720)         # 可选 fix_point=FixPoint.NORTH|FixPoint.WEST（默认）控制缩放锚点
window.move(100, 100)

# resize 的 fix_point 参数（实证 6.2.1）
# 签名：window.resize(width, height, fix_point=FixPoint.NORTH | FixPoint.WEST)
# fix_point 控制窗口缩放时哪个角/边固定不动，可组合（位运算 |）：
#   FixPoint.NORTH  — 上边固定（向下扩展）
#   FixPoint.SOUTH  — 下边固定（向上扩展）
#   FixPoint.EAST   — 右边固定（向左扩展）
#   FixPoint.WEST   — 左边固定（向右扩展）
# 默认 NORTH|WEST = 左上角固定（窗口向右下生长），即常规行为。
# 场景：从右下角缩放时用 SOUTH|EAST 让右下角不动。
from webview.window import FixPoint
window.resize(800, 600, fix_point=FixPoint.SOUTH | FixPoint.EAST)
window.minimize()
window.restore()
window.hide()
window.show()
window.destroy()
window.toggle_fullscreen()
window.load_url('http://127.0.0.1:5001/new-page')   # 导航到新 URL
window.load_html('<h1>Hello</h1>')                   # 直接加载 HTML 内容（无需服务器）
```

### 原生窗口句柄 `window.native`（已实证 6.2.1）

> **适用场景**：需要访问平台原生窗口对象进行深度定制（如 Windows DPI 感知、macOS NSWindow 行为调整、Linux GTK 信号连接）。

`window.native` 返回当前平台的原生窗口对象。**仅在 `before_show` 事件后可用**（建窗早期无句柄）：

| 平台 | `window.native` 类型 | `window.native.webview` 类型 |
|------|---------------------|-----------------------------|
| Windows | `System.Windows.Forms.Form` | WebView2 COM 对象 |
| macOS | `AppKit.NSWindow` | `WebKit.WKWebView` |
| Linux (GTK) | `Gtk.ApplicationWindow` | `WebKit2.WebView` |
| Linux (QT) | `QMainWindow` | `QWebEngineView` |

```python
window = webview.create_window('App', url)

def on_before_show():
    # 此时 window.native 已可用
    native = window.native
    # Windows 示例：设置 DPI 感知
    # native 是 System.Windows.Forms.Form 实例
    # macOS 示例：native 是 NSWindow，可调 native.setStyleMask_()

window.events.before_show += on_before_show
webview.start()
```

> ⚠️ `window.native` 在 `before_show` **之前**访问会返回 `None` 或抛异常。始终在 `before_show` / `shown` / `loaded` 等事件回调中使用。
> `window.native.webview` 返回 WebView 引擎对象，可用于更深层的引擎级操作（如 WebView2 的 CoreWebView2 接口）。

---

## start() 参数

> **适用场景**：启动 GUI 事件循环。`webview.start()` 是阻塞调用，程序运行到此处后进入窗口消息循环。

```python
webview.start(
    debug=False,            # 启用 DevTools（F12），开发阶段设为 True
    gui=None,               # 强制指定渲染引擎：'edgechromium' / 'cef' / 'mshtml' / 'qt'
    private_mode=False,     # 是否启用私有模式（隔离 cookie/缓存）
    http_server=False,      # 是否启用内置 HTTP 服务器
    http_port=None,         # 内置 HTTP 服务器端口
    storage_path=None,      # 持久化存储路径（默认系统临时目录）
    ssl=False,              # 是否启用 SSL
)
```

> ⚠️ **窗口必须在 `webview.start()` 之前创建**：`webview.start(func)` 的第一个位置参 `func` 是「主线程并发逻辑」（典型如启动 FastHTML/uvicorn 服务），**不是**用来创建窗口的。`start()` 入口会先检查 `webview.windows` 是否非空，若为空直接抛 `WebViewException: You must create a window first before calling this function.`。正确顺序：先 `webview.create_window(...)`（可多个），再 `webview.start(func, arg)`；若无需并发逻辑则直接 `webview.start()`。

| 参数 | fasthtml-desktop 推荐值 | 说明 |
|------|------------------------|------|
| `debug` | 开发=True / 打包=False | 打包后必须设为 False，否则右键菜单暴露 DevTools |
| `gui` | `None`（**跨平台推荐**） | 传 `None` 信任官方默认链（Win=WinForms/WebView2、mac=cocoa、Linux=gtk），业务代码三端通用。**不要硬编码 `gui='edgechromium'`**（旧 Windows-only 写法会锁死多端）。确需指定时仅限对应平台：`'edgechromium'`/`'mshtml'`（Win）、`'cocoa'`/`'qt'`（mac）、`'gtk'`/`'qt'`（Linux）、`'cef'`（⚠ 仅 Python ≤3.9） |
| `private_mode` | `False` | 设为 True 会隔离 session，每次启动 cookie 丢失 |
| `storage_path` | `BASE_DIR / "webview_data"` | 持久化路径需指向 EXE 所在目录（非临时目录） |
| `ssl` | `False` | localhost 场景不需要 |

---

## JS ↔ Python 通信

> **适用场景**：前端（FastHTML 页面）需要调用 Python 后端能力——文件读写、系统命令、API 请求等。
> 这是桌面应用区别于纯 Web 应用的核心能力。所有数据下载、文件操作、系统调用都通过此通道。

### ⚠️ 桥接就绪时机：必须等待 `pywebviewready`

`pywebview.api` 在 `window.onload` 时**不保证已就绪**，页面加载后立即调用 `pywebview.api.xxx()` 会抛 `pywebview is not defined`。前端 JS 必须监听 `pywebviewready` 事件后再调用 Python：

```javascript
window.addEventListener('pywebviewready', function () {
  pywebview.api.get_data('Alice').then(result => { /* ... */ });
});
```

> 典型坑：FastHTML 首屏渲染 / HTMX 换页后立刻调 Python 拉初始数据，若未等 `pywebviewready` 会偶发失败。所有 `pywebview.api.*` 调用都应包在该事件回调内（或确保触发时机晚于该事件）。

### js_api 桥接

```python
class Api:
    def get_data(self, name: str) -> str:
        return f"Hello, {name}!"
    def process_files(self, paths: list[str]) -> dict:
        # 调用后端逻辑
        return {"status": "ok", "count": len(paths)}

window = webview.create_window('App', 'http://127.0.0.1:5001', js_api=Api())
webview.start()
```

前端 JS 中调用：

```javascript
// pywebview.api.get_data('Alice').then(result => ...)
// pywebview.api.process_files(['a.txt', 'b.txt']).then(result => ...)
```

### Python 调 JS

```python
# 同步
result = window.evaluate_js('document.title')

# 异步（带回调）
def on_result(result):
    print(result)

window.evaluate_js('document.title', callback=on_result)
```

### 其他 Window 实例方法（已实证 6.2.1）

```python
window.set_title('新标题')          # 运行时改窗口标题（等价于 window.title = '...'）
current = window.get_current_url()  # 读取当前窗口 URL（字符串）
rv = window.run_js("function t(){ return 420 } t()")  # 运行 JS 并取返回值（实证返回 420）

# 全局能力（webview 模块级，实证 6.2.1）
screens = webview.screens           # 屏幕列表（Proxy），s.width / s.height / s.x / s.y
# Screen 实例完整属性（实证 6.2.1，全部为实例属性，类级 hasattr 会假阴性——因 scale 等为 @property）：
#   s.width / s.height        — 逻辑分辨率（CSS 像素）
#   s.x / s.y                 — 屏幕原点坐标
#   s.scale                   — 缩放因子（float，如 1.0 / 1.25 / 1.5；高 DPI 屏 >1.0）
#   s.physical_width / s.physical_height  — 物理分辨率（像素，= width * scale）
#   s.physical_x / s.physical_y           — 物理原点坐标
#   s.dpi                     — DPI 值（int，如 96 / 120 / 144）
# 多显示器场景：screens = list(webview.screens)；create_window(screen=screens[1]) 指定第二块屏
webview.start(
    user_agent='Mozilla/5.0 MyApp/1.0',   # ⚠ user_agent 是 start() 参数，不是 create_window 参数
    localization={'windows.fileFilter.allFiles': '所有文件'},  # Windows 生效键：windows.* / global.*
)
```

> ⚠️ **`webview.token` 是内部密钥，禁止业务使用**：`webview.token` 是 pywebview 在 `util.guarded` 中用于校验 JS↔Python 桥接请求的随机令牌（模块级 `_TOKEN`，每次导入随机生成），**不是公开 API**，切勿在应用代码中读取或依赖它。

### 运行时暴露方法

```python
class Api:
    pass

api = Api()
window = webview.create_window('App', 'http://127.0.0.1:5001', js_api=api)
webview.start()

# 运行时动态暴露方法
window.expose(api.do_something)
```

### 内置双向共享状态 `window.state`（pywebview 6.0+）

无需自建共享对象，pywebview 提供跨语言自动同步状态：

```python
window.state.counter = 0        # Python 侧赋值
# JS 侧读取：pywebview.state.counter（需经 pywebviewready 后可用）
```

> ⚠️ **写入时序（已实证）**：Python 侧对 `window.state` 的赋值与 JS 侧 `pywebviewready` 回调内的首次读取存在竞态。若 JS 在 `pywebviewready` 回调里**立即**读取 Python 尚未写入的属性，会得到 `undefined`。对策：① Python 在 `window.events.loaded` 中尽早写入；② JS 用 `setInterval` 轮询 / 重试读取（实测约 200ms 内即可读到 Python 已写的值）。

```javascript
pywebview.state.counter = 1;    // JS → Python 自动同步
console.log(pywebview.state.counter);
```

> 多窗口共享状态推荐用 `window.state` 替代"自建 SharedState 类 + js_api"的变通写法（见下方多窗口章节）。仅顶层属性变更会同步，嵌套对象变更不会自动传播。

**state 变更事件订阅（已实证 6.2.1）**：`window.state` 支持 `+=` / `-=` 订阅变更事件，回调签名为 `(event_type, key, value)`，`event_type` 为 `webview.state.StateEventType.CHANGE / DELETE`。Python 侧与 JS 侧引起的变更都会触发（回调在独立线程执行）：

```python
from webview.state import StateEventType

def on_state(event_type, key, value):
    if event_type == StateEventType.CHANGE:
        print(f'{key} -> {value}')

window.state += on_state     # 订阅
window.state -= on_state     # 退订
```

---

## Python 侧 DOM 操作（`window.dom`，已实证 6.2.1）

> **适用场景**：无需写 JS，直接用 Python 查询/增删/修改页面元素。适合桌面壳侧的轻量 UI 干预（如注入提示条、动态改状态角标）；**大块 UI 仍应由 FastHTML SSR/HTMX 渲染**，`window.dom` 只做壳层补充。
> 全部 API 已在本机 pywebview 6.2.1 内省 + 真实应用断言通过（开发态与打包 EXE 双态 ALL_PASS）。

```python
from webview.dom import ManipulationMode

# DOM 查询（须在 events.loaded 之后）
el   = window.dom.get_element('#content')      # 单个，无匹配返回 None
els  = window.dom.get_elements('.item')        # 列表
body = window.dom.body                          # <body> 句柄
doc  = window.dom.document                      # document 句柄
win  = window.dom.window                        # JS window 句柄

# 创建元素：html 片段 + 父元素/选择器 + 插入模式
p = window.dom.create_element('<p id="p1">hi</p>', parent=el,
                              mode=ManipulationMode.LastChild)
# ManipulationMode: LastChild / FirstChild / Before / After / Replace

# Element 常用成员（实测全集节选）
p.text                          # 读文本
p.tag                           # 'p'
p.id                            # 'p1'
p.classes.append('marked')      # 类名操作（ClassList，支持 append/remove/toggle）
p.style['color'] = 'red'        # 样式读写（propsdict）
p.attributes['data-x'] = '1'    # 属性读写
p.hide(); p.show(); p.toggle()  # 显隐
p.append('<span>child</span>')  # 追加子元素
p.remove()                      # 删除自身
# 其余：blur/focus/focused/children/parent/next/previous/copy/move/empty/value/visible/node/on/off
```

**事件绑定**：`el.on('click', handler)` / `el.off('click', handler)`，或 `el.events.click += DOMEventHandler(handler, prevent_default=True)`（拖放章节同款机制）。

> ⚠️ `window.dom` 的所有调用都要求窗口 DOM 就绪（`window.events.loaded` 之后），过早调用会拿到 `None` 或抛异常。

---

## 无边框窗口拖拽区（frameless + drag region，已实证 6.2.1）

> **适用场景**：`frameless=True` 自绘标题栏时，让某块区域承担"按住拖动窗口"的原生标题栏行为。

做法：给充当标题栏的元素加类名 `pywebview-drag-region`（FastHTML 里即 `cls="pywebview-drag-region"`）：

```python
# FastHTML 侧
Div("My App", cls="pywebview-drag-region", style="height:32px;")

# pywebview 侧
window = webview.create_window('App', url, frameless=True, easy_drag=False)
```

- 选择器可通过 `webview.settings['DRAG_REGION_SELECTOR']` 定制（默认 `'.pywebview-drag-region'`）。
- **⚠️ 旧 API 已弃用（实证有 DeprecationWarning）**：`webview.DRAG_REGION_SELECTOR` 模块常量已 deprecated，**必须**改用 `webview.settings['DRAG_REGION_SELECTOR']`。
- 关联字段 `webview.settings['DRAG_REGION_DIRECT_TARGET_ONLY']`（默认 `False`）：为 `True` 时仅元素自身（不含子元素）响应拖动。
- `easy_drag=True` 是另一种方案（整窗可拖），与 drag-region 二选一；表单类应用整窗可拖会干扰文本选择，**推荐 drag-region**。

---

## `load_css` 注入与 `webview.settings` 全字段（已实证 6.2.1）

**运行时注入 CSS**：`window.load_css(stylesheet: str)`，适合壳层主题微调（如冻结版隐藏滚动条、调整选中样式），注入后立即生效（实测 `getComputedStyle` 可验证）：

```python
window.load_css('#content { background-color: #f5f5f5; }')
```

**`webview.settings` 全 11 字段（6.2.1 实测默认值）**，须在 `webview.start()` **之前**设置：

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `ALLOW_DOWNLOADS` | `False` | 允许文件下载（见"文件下载"节） |
| `ALLOW_FILE_URLS` | `True` | 允许 `file://` URL |
| `DRAG_REGION_SELECTOR` | `'.pywebview-drag-region'` | 无边框拖拽区选择器 |
| `DRAG_REGION_DIRECT_TARGET_ONLY` | `False` | 拖拽区是否仅元素自身生效 |
| `DEFAULT_HTTP_PORT` | `42001` | 内置 http server 默认端口（本栈自管 uvicorn，一般不用） |
| `OPEN_EXTERNAL_LINKS_IN_BROWSER` | `True` | 外链用系统浏览器打开 |
| `OPEN_DEVTOOLS_IN_DEBUG` | `True` | debug 模式自动开 DevTools |
| `REMOTE_DEBUGGING_PORT` | `None` | WebView2 远程调试端口（仅调试用途，界面质检不依赖此端口） |
| `IGNORE_SSL_ERRORS` | `False` | 忽略 SSL 证书错误（仅调试用） |
| `SHOW_DEFAULT_MENUS` | `True` | 显示默认右键菜单 |
| `WEBVIEW2_RUNTIME_PATH` | `None` | 指定 WebView2 固定版本运行时路径（离线/受控环境部署） |

### 外部链接行为（`OPEN_EXTERNAL_LINKS_IN_BROWSER`，实证 6.2.1）

当页面中的链接 `target='_blank'` 或指向外部域名的链接被点击时，pywebview 默认用**系统默认浏览器**打开，而不是在 WebView 内导航。此行为由 `webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER']` 控制（默认 `True`）：

```python
# 默认行为：外链 → 系统浏览器打开（推荐，符合桌面应用预期）
webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = True   # 默认值

# 若需外链在 WebView 内打开（不推荐，可能导致导航到不可控页面）：
# webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = False
```

> **FastHTML 桌面应用推荐保持默认 `True`**：应用内部路由通过 HTMX `hx-get` / `hx-post` 处理（不触发整页导航），外部链接走系统浏览器打开——这是桌面应用的标准行为。设为 `False` 会导致用户点击外部链接时 WebView 导航到外部页面且无法返回。
> 镜像示例：`pywebview-examples/links.py`。

### `webbrowser.open`：外链行为的内部实现（实证 6.2.1 源码）

`OPEN_EXTERNAL_LINKS_IN_BROWSER=True`（上方 G6）的底层实现正是 Python 标准库 `webbrowser.open()`。pywebview 在 **6 个平台后端**中内部调用它，将外链导航交给系统默认浏览器：

| 后端 | 源码调用位置 | 触发条件 |
|------|-------------|---------|
| `edgechromium.py` | `webbrowser.open(str(args.get_Uri()))` | `OPEN_EXTERNAL_LINKS_IN_BROWSER=True` 时拦截 `NewWindow` 事件 |
| `cef.py` | `webbrowser.open(url)` | 用户手势触发的外链导航 |
| `mshtml.py` | `webbrowser.open(args.Url)` | 新窗口请求 |
| `qt.py`（2 处） | `webbrowser.open(url.toString(), 2, True)` | `navigationIntercepted` 拦截外链 + `createWindow` 新窗口 |
| `cocoa.py` | `webbrowser.open(action.request().URL().absoluteString(), 2, True)` | `decidePolicyForNavigation` 外链检测 |
| `gtk.py` | `webbrowser.open(uri, 2, True)` | `_blank` 目标跳转 |

> **与 G6 的关系**：G6（`OPEN_EXTERNAL_LINKS_IN_BROWSER`）是 pywebview 暴露给用户的**行为开关**，`webbrowser.open` 是该开关的**内部实现机制**。二者构成"配置项 → 实现"的依赖链——没有 `webbrowser.open`，G6 的 `True` 分支无法生效。

**FastHTML 桌面应用中 `webbrowser.open` 的合法使用场景**：

```python
import webbrowser, threading

# 场景 1：备选启动入口（pywebview 窗口失败时的 fallback）
# 02-build-commands.md 已含此模板：
threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
# pywebview 壳已自带浏览器窗口，自动打开系统浏览器这一步不是必需的。
# 可以保留作为备选（当 pywebview 窗口无法打开时用户可通过浏览器访问）。

# 场景 2：非 pywebview 部署模式（纯 Web 服务 + 浏览器访问）
# 开发调试时不用 pywebview 壳，直接用浏览器打开本地服务

# 场景 3：从应用内主动打开外部 URL（如帮助文档、官方网站）
webbrowser.open("https://example.com/docs")
```

> ⚠️ **不要因为"pywebview 原生窗口已承载页面"就认定 `webbrowser.open` 在 f-d 架构下无意义**。上述 6 个后端的内部调用证明它是 pywebview 外链行为的核心依赖；f-d 自身的模板和示例（`packaging/02-build-commands.md` 浏览器自动打开模板、示例 `01-announcement-downloader`）也已使用它。

### 日志控制 `PYWEBVIEW_LOG`（实证 6.2.1）

pywebview 使用 Python `logging` 模块，日志器名为 `'pywebview'`。可通过环境变量 `PYWEBVIEW_LOG` 控制日志级别：

```python
import os
# 开发调试时开启 pywebview 内部日志
os.environ['PYWEBVIEW_LOG'] = 'DEBUG'     # 或 'INFO' / 'WARNING' / 'ERROR'

# 打包发布时静默（默认即 WARNING 级别，通常无需设置）
# os.environ['PYWEBVIEW_LOG'] = 'ERROR'
```

> 该环境变量在 `webview` 模块导入时读取，须在 `import webview` **之前**设置。打包后默认日志级别为 `WARNING`，控制台仅显示警告和错误。开发态设 `DEBUG` 可查看后端选择、窗口创建、JS 桥接等详细日志。

### 透明窗口（`transparent=True`，实证 6.2.1）

`transparent=True` 使窗口背景透明（与 `frameless=True` 配合使用），适合自绘异形窗口、 Splash 启动动画等场景：

```python
html = '''
<html><body style="background:rgba(0,0,0,0);margin:0;">
  <div style="width:300px;height:200px;border-radius:16px;
              background:rgba(50,50,50,0.9);color:#fff;padding:20px;">
    透明窗口内容
  </div>
</body></html>
'''

window = webview.create_window(
    '透明窗口', html=html,
    transparent=True,      # 透明背景
    frameless=True,        # 无边框（透明窗口通常需要）
    easy_drag=True,        # 整窗可拖（因无标题栏）
)
webview.start()
```

> **平台差异**：
> - **Windows**：基于 WebView2，`transparent=True` 使窗口背景透明但 WebView 内容区域仍渲染。需配合 CSS `background:rgba(0,0,0,0)` 才能看到透明效果。
> - **macOS**：cocoa 后端原生支持透明。
> - **Linux**：GTK 后端支持透明（需合成管理器如 compton/mutter）。
>
> ⚠️ `transparent=True` 与 `background_color` 互斥——设透明后 `background_color` 无效。
> `transparent` 与 `vibrancy`（仅 macOS 毛玻璃）是不同效果：前者完全透明，后者是系统级毛玻璃模糊。

> ⚠️ `evaluate_js` 的代码会被包进普通函数体执行，**不能用顶层 `await`**（实证抛 `SyntaxError: await is only valid in async functions`）。需要异步逻辑时用 `.then()` 链或由 Python 侧发起 HTTP 请求。

---

## 对话框

> **适用场景**：需要用户选择文件（打开/保存）、确认操作、输入文字。
> 比 HTML 原生对话框更可靠（HTML 的 `<input type="file">` 在打包后可能行为异常）。

```python
# 打开文件
file_path = window.create_file_dialog(
    dialog_type=webview.FileDialog.OPEN,      # FileDialog.OPEN / FileDialog.FOLDER / FileDialog.SAVE
    directory='',                           # 默认目录
    allow_multiple=True,                    # 多选
    file_types=('Excel文件 (*.xlsx;*.xls)', '所有文件 (*.*)')
)

# 保存文件
save_path = window.create_file_dialog(
    dialog_type=webview.FileDialog.SAVE,
    save_filename='output.xlsx'
)

# 确认对话框
result = window.create_confirmation_dialog('确认删除？')
# 返回 True/False
```

---

## 文件拖放（拖文件进窗口）

比"点按钮 → `create_file_dialog`"更自然的桌面交互：把文件拖入窗口即可拿到**完整路径**，走 `window.dom` 的 `drop` 事件（pywebview 增强该事件以返回真实路径）：

```python
from webview.dom import DOMEventHandler

def on_drop(e):
    path = e['dataTransfer']['files'][0]['pywebviewFullPath']   # 拖入文件的完整路径
    print('dropped:', path)

window.dom.document.events.drop += DOMEventHandler(on_drop, prevent_default=True, stop_propagation=True)
```

> ⚠️ **字段名已修正**：pywebview 拖放事件用的是 `e['dataTransfer']['files'][0]['pywebviewFullPath']`，**不是** `domTransfer`（全库无 `domTransfer` 字段）。`DOMEventHandler` 用于声明 `prevent_default` / `stop_propagation`，是推荐绑定方式。
> 与 `create_file_dialog` 互补：前者适合"拖入即处理"，后者适合"显式选择 / 多文件 / 保存路径"。
> `drop` 依赖 `window.dom`，须在窗口 / DOM 就绪后绑定。完整可用示例见 `pywebview-examples/drag_drop.py`。

---

## 菜单

> **适用场景**：应用有结构化功能需要组织——文件（打开/保存/退出）、编辑（撤销/重做）、帮助（关于/检查更新）。
> 菜单是最符合 Windows 桌面用户习惯的功能入口方式。

```python
from webview.menu import Menu, MenuAction, MenuSeparator

menu = [
    Menu('文件', [
        MenuAction('打开', lambda: on_open()),
        MenuAction('保存', lambda: on_save()),
        MenuSeparator(),
        MenuAction('退出', lambda: window.destroy()),
    ]),
    Menu('帮助', [
        MenuAction('关于', lambda: on_about()),
    ])
]

window = webview.create_window('App', url, menu=menu)
```

> **子菜单（submenu）**：pywebview **没有** `MenuSubMenu` 类。子菜单通过「在 `Menu` 的 `items` 里再放一个 `Menu`」实现——`Menu` 的签名是 `Menu(title, items: list[Menu | MenuAction | MenuSeparator])`，`items` 本身可含 `Menu`。下方 `「文件 ▸ 最近打开」` 即一个二级子菜单：

```python
from webview.menu import Menu, MenuAction, MenuSeparator

menu = [
    Menu('文件', [
        MenuAction('打开', lambda: on_open()),
        MenuSeparator(),
        Menu('最近打开', [                        # ← 嵌套 Menu = 子菜单（无 MenuSubMenu 类）
            MenuAction('report.txt', lambda: None),
            MenuAction('notes.txt', lambda: None),
        ]),
        MenuSeparator(),
        MenuAction('退出', lambda: window.destroy()),
    ]),
    Menu('帮助', [
        MenuAction('关于', lambda: on_about()),
    ]),
]
window = webview.create_window('App', url, menu=menu)
```
```

> **`title='__app__'` 语义（macOS 应用菜单）**：当 `Menu` 的 `title` 为特殊值 `'__app__'` 时，在 **macOS** 上该菜单会显示为系统标准应用菜单（菜单栏第一项，标题为应用名，含 About / Quit 等系统项）；在 **Windows / Linux** 上该菜单被**静默忽略**（不显示）。典型用法：在菜单列表最前面放一个 `Menu('__app__', [...])` 以兼容 macOS 应用菜单规范，Windows/Linux 自动跳过：
> ```python
> menu = [
>     Menu('__app__', [                    # macOS 应用菜单；Windows/Linux 忽略
>         MenuAction('关于', lambda: on_about()),
>     ]),
>     Menu('文件', [
>         MenuAction('打开', lambda: on_open()),
>     ]),
> ]
> ```

---

## 事件

> **适用场景**：需要监听窗口生命周期事件——加载完成、关闭前、窗口移动/调整大小时执行特定操作。
> 常用事件：`before_show`/`initialized`（建窗早期钩子）、`loaded`/`shown`（UI 就绪）、`closing`/`closed`（清理资源）、`minimized`（隐藏到托盘）。
>
> ⚠️ `before_show`、`initialized`、`before_load` 都是**真实存在**的 `window.events`（`window.py` 在 `Window.__init__` 里动态挂载：`self.events.initialized = Event(self, True)` 等）。**不能**用「类级 `hasattr` / `dir(EventContainer)`」去检查——它们在类上查不到（会得到"不存在"的假象），必须用**窗口实例**检查或读 `window.py` 源码。本技能所有事件断言均已在真实窗口实例上实证触发。

```python
window = webview.create_window('App', url)

window.events.before_load += lambda: print('页面即将加载（可拦截）')
window.events.loaded += lambda: print('页面加载完成')
window.events.before_show += lambda: print('窗口即将显示')
window.events.initialized += lambda gui: print('窗口已初始化, 后端=', gui)  # gui 为渲染后端；回调返回假值/抛异常可中止建窗
window.events.shown += lambda: print('窗口已显示')
window.events.closing += lambda: print('窗口正在关闭...')
window.events.closed += lambda: print('窗口已关闭')
window.events.resized += lambda: print('窗口大小已变')
window.events.moved += lambda: print('窗口位置已变')
window.events.minimized += lambda: print('窗口已最小化')
window.events.maximized += lambda: print('窗口已最大化')
window.events.restored += lambda: print('窗口已还原')

# 网络请求级事件（实证 6.2.1：window.py 以实例动态赋值创建，edgechromium 后端有完整实现）
# ⚠ 注意：这两个事件是 Window.__init__ 里动态挂载的实例属性（self.events.request_sent = Event(self)），
#   用「类级 hasattr / dir(EventContainer)」检查会得到不存在的假象——必须用实例检查或读 window.py 源码。
window.events.request_sent += lambda w, req: print('请求发出:', req.url)        # 可改 req.headers 注入自定义请求头
window.events.response_received += lambda w, resp: print('收到响应:', resp.url)
```

---

## 系统托盘

> **适用场景**：应用需要常驻后台、快速唤醒（如定时监控、消息提醒）。
> 关闭窗口时最小化到托盘而非退出，右键托盘图标显示菜单。
> **实现方式**：pywebview 无内置托盘，使用 `pystray` 第三方库（依赖 `Pillow` 提供图标），见下方代码与 `pywebview-examples/pystray_icon.py`。

> ⚠️ **已修正**：pywebview **没有**内置托盘 API（`webview.TrayIcon` 不存在，`create_window` 无 `tray` 参数）。系统托盘须用第三方库 **`pystray`**（配合 `Pillow` 提供图标）实现，并以独立进程运行避免阻塞 GUI 主线程。

```python
import pystray
from PIL import Image
import multiprocessing

_tray = None

def on_exit(w):
    w.destroy()
    if _tray:
        _tray.stop()

def run_tray(w):
    global _tray
    _tray = pystray.Icon(
        'myapp',
        Image.open('app.ico'),            # 托盘图标文件（需自备，建议 .ico/.png）
        '我的应用',
        pystray.Menu(
            pystray.MenuItem('显示', w.show),
            pystray.MenuItem('退出', lambda: on_exit(w)),
        ),
    )
    _tray.run()                            # 阻塞，直到 stop()

# 托盘在独立进程运行，避免阻塞 GUI 主线程
tray_proc = multiprocessing.Process(target=run_tray, args=(window,), daemon=True)
tray_proc.start()
```

> 依赖：`pip install pystray Pillow`。完整可用示例见 `pywebview-examples/pystray_icon.py`（已验证 Windows / Edge 可用）。

---

## Cookie 管理

```python
# 获取所有 cookie（无参数；返回 list[Cookie]）
cookies = window.get_cookies()
# 清除全部 cookie（含 HttpOnly；无参数）
window.clear_cookies()
```

> ⚠️ **已修正**：`get_cookies()` **不接受任何参数**（签名 `(self)`）。pywebview 不提供"按 URL 过滤 cookie"的接口，调用 `get_cookies('http://...')` 会抛 `TypeError`。`clear_cookies()` 同样无参数（实证 6.2.1 两方法均为 `Window` 实例方法，真实存在）。

---

## 文件下载

> ⚠️ **已修正**：pywebview **没有** `events.download` 事件（`window.events` 清单中无 `download`）。开启下载能力只需设置全局开关，由 WebView2 引擎原生处理保存对话框：

```python
# 启用下载（全局开关，应在 webview.start() 之前设置）
webview.settings['ALLOW_DOWNLOADS'] = True

# 触发下载：前端 JS 发起下载请求，或由后端返回带 Content-Disposition 的响应，
# WebView2 会弹出原生"另存为"对话框，无需额外事件监听。
```

> 如需自定义下载落盘路径，配合 `create_file_dialog(dialog_type=webview.FileDialog.SAVE, save_filename=...)` 让用户选择。完整可用示例见 `pywebview-examples/downloads.py`。

---

## 多窗口

```python
window1 = webview.create_window('窗口一', 'http://127.0.0.1:5001')
window2 = webview.create_window('窗口二', 'http://127.0.0.1:5001')
webview.start()
```

> 上例只演示"开两个窗口"，未涉及窗口间如何共享状态或互相通知。注意 `create_window()` **返回 `Window` 对象**（见上方 `window.title = ...` / `window.evaluate_js(...)` 等用法），这是实现窗口协作的关键。

### 多窗口状态共享 / 窗口间通信

pywebview 没有内置的"窗口间消息总线"，靠以下两种机制实现（均基于本文件已列出的 API）：

**方案 A：共享 Python 状态对象（推荐，最简单）**
把同一个 Python 对象通过 `js_api` 注入每个窗口；任意窗口的 JS 调用 `js_api` 方法时，操作的是同一份内存，从而自然共享状态。
```python
class SharedState:
    def __init__(self):
        self.windows = []            # 收集各窗口的 Window 句柄
    def push_to(self, target, msg): # 经 registry 向指定窗口发指令
        for w in self.windows:
            if w.title == target:
                w.evaluate_js(f"window.onMessage({msg!r})")

shared = SharedState()
w1 = webview.create_window('主窗口', url, js_api=shared)
w2 = webview.create_window('详情',  url, js_api=shared)
shared.windows = [w1, w2]            # create_window 返回后即可收集句柄
webview.start()
```

**方案 B：窗口句柄注册表 + `evaluate_js` 定向推送**
维护一个 `title → Window` 映射，需要联动时调用目标窗口的 `evaluate_js(...)` 注入 JS（刷新、跳转、弹提示等）。`evaluate_js` 的返回值 / 回调（见本文件 §js_api 桥接）可把结果回传 Python。

> 注意：多窗口在 `webview.start()` 下标记为"⚠️ 不稳定"（见上方能力矩阵）。跨窗口强一致状态建议收敛到后端（FastHTML 的共享 session / DB），前端只做展示与触发，避免多窗口各自持状态导致不一致。

### 活跃窗口查询与全局窗口列表

```python
# 获取当前活跃（聚焦）的窗口实例
active = webview.active_window()     # 返回 Window 实例或 None（无窗口时）

# 获取所有已创建的窗口列表
all_windows = webview.windows        # 返回 list[Window]，在 start() 前后均可用

# 场景：从托盘唤醒时找到已有窗口而非新建
def on_tray_show():
    if webview.windows:
        w = webview.active_window() or webview.windows[0]
        w.show()
        w.restore()
    else:
        # 所有窗口已关闭，新建
        webview.create_window('App', url)
```

> `webview.windows` 是模块级属性（不是函数），返回当前所有 `create_window()` 创建的窗口实例列表。`webview.active_window()` 返回当前聚焦的窗口（无聚焦窗口时返回 `None`）。两者均在 `webview.start()` 之前也可用（已创建但尚未启动时 `windows` 非空、`active_window()` 返回最后创建的窗口）。

---

## 调试模式

```python
# 开发阶段：启用调试工具（F12 打开 DevTools）
webview.create_window('App', url, debug=True)
webview.start()

# PyInstaller 打包时去掉 debug=True
```

---

## WebView2 检测与自动安装

> **适用场景**：Win7 或精简版 Win10 可能未安装 WebView2 Runtime，
> 导致 pywebview 窗口打开时崩溃。以下代码通过注册表检测，缺失时静默安装。

```python
import winreg, subprocess
from pathlib import Path

def ensure_webview2() -> bool:
    """检测 WebView2 Runtime 是否已安装，缺失则自动安装。"""
    # 注册表检测路径
    paths = [
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"),
        (winreg.HKEY_CURRENT_USER,
         r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"),
    ]
    for hive, subkey in paths:
        try:
            key = winreg.OpenKey(hive, subkey)
            version, _ = winreg.QueryValueEx(key, "pv")
            winreg.CloseKey(key)
            print(f"  WebView2: v{version}")
            return True
        except OSError:
            continue

    print("  WebView2 未安装，尝试自动安装...")

    # 从 EXE 同级目录查找安装包（打包前需 --add-data 打入）
    installer = Path(sys.executable if getattr(sys, 'frozen', False) else __file__).parent
    installer = installer / "MicrosoftEdgeWebview2Setup.exe"

    if not installer.exists():
        print("  [!] 未找到 WebView2 安装包，请手动安装")
        print("      下载：https://go.microsoft.com/fwlink/p/?LinkId=2124703")
        return False

    result = subprocess.run(
        [str(installer), "/silent", "/install"],
        capture_output=True, timeout=120
    )
    if result.returncode == 0:
        print("  WebView2 安装完成")
        return True
    else:
        print(f"  [!] 安装失败 (exit={result.returncode})")
        return False
```

> 安装包（Evergreen Bootstrapper，约 1.6 MB）需要预先下载并通过 `--add-data` 打包进 EXE：
> ```
> --add-data "MicrosoftEdgeWebview2Setup.exe;."
> ```
> 下载链接：https://go.microsoft.com/fwlink/p/?LinkId=2124703

---

## PyInstaller 打包参数（桌面壳专用，按目标平台后端矩阵）

> pywebview 6.2.1 **自带** PyInstaller hook（`webview/__pyinstaller/hook-webview.py`），自动收集
> `webview/lib`、`webview/js` 与动态库——**无需手动 `--hidden-import webview`**。
> 只需补"目标平台实际会用的后端平台子模块"（完整矩阵见 `references/11-cross-platform.md` §3）：

```bash
# Windows（WinForms 宿主 + WebView2/mshtml renderer）
--hidden-import clr
--hidden-import webview.platforms.winforms
--hidden-import webview.platforms.edgechromium
--hidden-import webview.platforms.mshtml

# macOS（cocoa 宿主 + pyobjc）
--hidden-import webview.platforms.cocoa
--hidden-import AppKit --hidden-import Foundation --hidden-import WebKit --hidden-import objc --hidden-import PyObjCTools.AppHelper

# Linux（gtk 宿主 + PyGObject）
--hidden-import webview.platforms.gtk
--hidden-import gi --hidden-import gi.repository.Gtk --hidden-import gi.repository.WebKit2

# 跨平台通用
--collect-submodules fasthtml
--add-data "src;src"          # Windows 分隔符；mac/Linux 用 "src:src"
```

完整打包参数与 macOS py2app / Linux AppImage 见 `packaging/02-build-commands.md` 与 `references/11-cross-platform.md`。

---

## 冻结包入口模板

> 启动 uvicorn + pywebview 的规范写法见 `07-integration-patterns.md` §1（推荐 `webview.start(run_server)` 替代手动 threading）。

```python
import webview, uvicorn, threading

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=5001, reload=False)

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    webview.create_window("我的应用", "http://127.0.0.1:5001")
    webview.start()
```

### 注意事项

| 原则 | 原因 |
|------|------|
| `console=True` | 用户需要看到启动日志和访问地址 |
| Edge Chromium 模式 | Windows 系统自带 WebView2，无需额外分发 |
| `webview.start()` 阻塞主线程 | 服务器必须在**另一个线程**启动（daemon=True） |
| 关闭窗口后应退出进程 | uvicorn 线程是 daemon，主线程结束即退出 |

---

## 外部子进程边车（sidecar）模式（可选）

上面的"冻结包入口模板"用**线程**在进程内启动 uvicorn。若希望 FastHTML 服务与桌面壳**进程隔离**（服务崩溃不连累窗口、可独立重启、便于调试端口），可改用子进程 sidecar：

```python
import subprocess, sys, webview, time, requests

def start_server_sidecar(port=5001, timeout=15):
    """以子进程拉起 FastHTML 服务，返回 Popen；内置健康检查。"""
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app",
         "--host", "127.0.0.1", "--port", str(port), "--reload", "False"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    # 健康检查：轮询直到 200 或超时
    for _ in range(timeout * 10):
        try:
            if requests.get(f"http://127.0.0.1:{port}/", timeout=0.5).status_code == 200:
                return proc
        except requests.ConnectionError:
            pass
        if proc.poll() is not None:
            raise RuntimeError("FastHTML 服务启动失败")
        time.sleep(0.1)
    proc.terminate()
    raise TimeoutError("FastHTML 服务健康检查超时")

if __name__ == "__main__":
    server = start_server_sidecar()
    try:
        webview.create_window("我的应用", "http://127.0.0.1:5001")
        webview.start()
    finally:
        server.terminate()
        server.wait()
```

**线程 vs 子进程取舍**：

| 维度 | 线程（默认） | 子进程 sidecar |
|------|------------|---------------|
| 复杂度 | 低（模板即开箱） | 中（需健康检查/清理） |
| 隔离性 | 弱（服务异常可能拖垮主进程） | 强（进程隔离） |
| 独立重启 | 需重启整个 EXE | 可只重启服务进程 |
| 调试 | 日志混在同一控制台 | 服务日志独立，端口可单独访问 |

> 注意：子进程模式打包时需确保 `uvicorn` 与 `app` 模块能被找到（或改用 `python -m uvicorn` 指向可导入的包），并在 `finally` 中**务必**清理子进程，否则窗口关闭后端口仍被占用。

---

## 已验证示例索引（`pywebview-examples/`）

本目录镜像了 pywebview 官方示例（v6.2.1）中**适用于 FastHTML + pywebview 跨平台技术栈**的脚本，作为 `06` 内联改写代码的权威上游参考。每个文件已加适配注释头。其中 5 个原「锁死栈外」的示例经跨平台适配后已解锁为**跨平台专属示例**（标注适用平台，仅在该平台有效），详见下方 **E 类**（此处不再重复列举，避免与 E 类重复）。

### A 类 · 高价值缺口（06 原缺失/写错，本次已修正）

| 脚本 | 用途 | 对应修正 |
|------|------|---------|
| `pystray_icon.py` | 系统托盘（正确实现） | 替代伪造的 `webview.TrayIcon` / `tray=True` |
| `drag_drop.py` | 文件拖放 | 修正 `domTransfer` → `dataTransfer['files'][0]['pywebviewFullPath']` |
| `downloads.py` | 文件下载 | 替代伪造的 `events.download`，用 `ALLOW_DOWNLOADS` |
| `loading_animation.py` | SSR 首屏 loading | 避免 uvicorn 启动期白屏 |
| `dom_state_dragregion_verified.py` | FastHTML+pywebview 端到端自验证（16 项断言） | 实证 `window.dom` 全 API / drag-region+settings / load_css / state 事件订阅；开发态与打包 EXE 双态 ALL_PASS（2026-07 实测） |

### B 类 · 已覆盖于 06（上游原版参考）

| 脚本 | 用途 |
|------|------|
| `change_url.py` | 运行时切换窗口 URL |
| `confirm_close.py` | 关闭前确认（`confirm_close=True`） |
| `confirmation_dialog.py` | 确认对话框 |
| `cookies.py` | 读取 cookie（`get_cookies()`） |
| `debug.py` | 调试模式（DevTools） |
| `destroy_window.py` | 销毁窗口 |
| `dom_events.py` | DOM 事件 |
| `evaluate_js.py` | Python 调 JS（同步） |
| `evaluate_js_async.py` | Python 调 JS（异步回调） |
| `events.py` | 窗口生命周期事件 |
| `expose.py` | 运行时暴露方法 |
| `focus.py` | 窗口聚焦 |
| `frameless.py` | 无边框窗口 |
| `fullscreen.py` | 全屏 |
| `hide_window.py` | 隐藏窗口 |
| `js_api.py` | JS↔Python 桥接 |
| `load_html.py` | 直接加载 HTML |
| `menu.py` | 菜单（`from webview.menu import ...`） |
| `min_size.py` | 最小尺寸 |
| `move_window.py` | 移动窗口 |
| `multiple_windows.py` | 多窗口 |
| `on_top.py` | 窗口置顶 |
| `open_file_dialog.py` | 打开文件对话框 |
| `resize.py` | 调整窗口大小 |
| `save_file_dialog.py` | 保存文件对话框 |
| `settings.py` | `webview.settings` 配置 |
| `state.py` | `window.state` 双向共享 |
| `toggle_fullscreen.py` | 切换全屏 |
| `window_state.py` | 窗口状态 |
| `window_title_change.py` | 动态改标题 |

### D 类 · 2026-07 增补镜像（gap-demo 打包态 22 项断言 ALL_PASS 实证）

| 脚本 | 用途 | 实证要点 |
|------|------|---------|
| `get_current_url.py` | 读取当前 URL | `window.get_current_url()` 实证存在（N2） |
| `get_elements.py` | 批量选择元素 | API 是 `window.dom.get_elements`，无 `window.get_elements` |
| `dom_manipulation.py` | DOM 增删改 | create_element/classes/style/remove 全实证（A 类） |
| `dom_traversal.py` | DOM 遍历 | `Element.parent/children/next/previous` 均为真实 property |
| `drag_region.py` | 无边框拖拽区 | settings['DRAG_REGION_SELECTOR'] 新 API（B 类） |
| `load_css.py` | 注入 CSS | getComputedStyle 断言生效（C2） |
| `transparent.py` | 透明无边框窗口 | Windows 可用；与 vibrancy（仅 macOS）无关 |
| `remote_debugging.py` | 远程调试端口 | settings['REMOTE_DEBUGGING_PORT'] |
| `multiprocess.py` | 多进程运行 | Windows 注意 freeze_support |
| `multiple_servers.py` | 多服务器多窗口 | 上游用 bottle；落地换多 uvicorn 端口 |
| `localhost_ssl.py` | 本地 SSL | `start(ssl=True)` 参数实证存在 |
| `user_agent.py` | 定制 UA | ⚠ `user_agent` 是 `start()` 参数而非 `create_window` 参数（N5） |
| `headers.py` | 请求头注入/监听 | `events.request_sent`/`response_received` 为**实例动态属性**，edgechromium 有实现（类级检查会误判不存在） |
| `screens.py` | 屏幕枚举 | `webview.screens` 返回列表，s.width/s.height（N4） |
| `http_server.py` | 内置 HTTP server | 相对路径入口自动起服务（常规路线仍是 uvicorn） |
| `links.py` | 外链行为 | target='_blank' 走外部浏览器 |
| `localization.py` | 本地化 | `start(localization=...)`；Windows 生效键为 `windows.*`/`global.*`（N6） |
| `run_js.py` | 运行 JS 取返回值 | `window.run_js(script)` 实证返回求值结果（N3） |
| `simple_browser.py` | 最小窗口闭环 | create_window + start 最小示例 |

> 说明：B 类脚本在 `06` 中已有**针对 FastHTML + Windows/Edge 的改写版**（部分上游示例用 flask / 内置 http server / `https://`），实际落地请以 `06` 内联代码为准；`pywebview-examples/` 用于比对上游原始实现。

### E 类 · 跨平台专属示例（多端适配解锁，标注适用平台）

| 脚本 | 适用平台 | 用途 | 关键约束 |
|------|----------|------|----------|
| `cef.py` | 跨平台（⚠ 仅 Python ≤3.9） | CEF 后端 `gui='cef'` | cefpython3 仅支持到 Py3.9；现代 Python 禁用（见 `11-cross-platform.md` §6） |
| `qt_test.py` | 跨平台 | Qt 后端 `gui='qt'` | 需 `pip install qtpy` + Qt 绑定 |
| `vibrancy.py` | **仅 macOS cocoa** | 窗口 vibrancy 毛玻璃 | Windows/Linux 源码 0 命中，设 True 无效 |
| `icon.py` | **仅 GTK / QT** | 运行时设置窗口图标 | Edge/cocoa 图标在打包阶段设置，运行时无效 |
| `py2app_setup.py` | **仅 macOS** | py2app setup 模板 | 经典 `python setup.py py2app`；可运行版见 `scripts/build_macos_py2app.py` |
