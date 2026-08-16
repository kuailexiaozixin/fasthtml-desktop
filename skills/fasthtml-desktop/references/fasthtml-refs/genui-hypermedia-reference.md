# AI is the new UI: Generative UI with FastHTML

> **来源**: [kafkasl.github.io/genUI/](https://kafkasl.github.io/genUI/) — 作者：pol_avec (Fewsats / L402)
>
> **核心主题**: 使用 FastHTML + HTMX 构建生成式用户界面 (Generative UI)，将 AI 输出从纯文本聊天进化为富交互式 UI 组件。
>
> **适用场景**: 本文件作为 FastHTML 技能的补充参考，展示 FastHTML 在 GenUI 领域的实际应用模式与最佳实践。

---

## 目录

- [GenUI 的核心思想](#genui-的核心思想)
- [三种 GenUI 演进层次](#三种-genui-演进层次)
- [为什么 FastHTML 适合 GenUI？](#为什么-fasthtml-适合-genui)
- [基本文本聊天机器人](#基本文本聊天机器人)
- [静态 GenUI：天气卡片组件](#静态-genui天气卡片组件)
- [交互式 GenUI：反馈循环模式](#交互式-genui反馈循环模式)
- [终极 GenUI：文本 + 按钮的融合](#终极-genui文本--按钮的融合)
- [实战 Demo 完整源码](#实战-demo-完整源码)
  - [Demo 1：weather（展示型 GenUI）](#demo-1weather展示型-genui)
  - [Demo 2：your_color（交互式 GenUI）](#demo-2your_color交互式-genui)
  - [Demo 3：hal9000（融合式 GenUI）](#demo-3hal9000融合式-genui)
- [如何运行 GenUI（实操指南）](#如何运行-genui实操指南)
- [在 fasthtml-desktop 中落地 GenUI](#在-fasthtml-desktop-中落地-genui)
- [架构总结](#架构总结)
- [已知限制与注意事项](#已知限制与注意事项)
- [参考链接](#参考链接)

---

## GenUI 的核心思想

**Generative UI (genUI)** 将生成式 AI 的能力从文本/图像扩展到动态用户界面。核心演进路径：

| 阶段 | 描述 | 用户体验 |
|------|------|----------|
| **1. 纯文本聊天** | 传统 LLM 接口，纯文本交互 | 需手打所有命令 |
| **2. 展示型 GenUI** | LLM 生成可视化组件（卡片、图表等），但不可交互 | 可视化浏览，仍需文字操作 |
| **3. 交互式 GenUI** | LLM 生成的组件包含可点击按钮、表单等交互元素 | 直观点击操作，无需打字 |

## 三种 GenUI 演进层次

### 1. 纯文本聊天界面

传统方法：用户输入 "I want to buy a book about AI"，AI 返回文字推荐，每一步都需打字回复。

### 2. 展示型 GenUI

LLM 生成带封面和描述的书籍卡片——视觉上更好看，但仍需打字进行选择或购买。ChatGPT 和 Claude 已实现部分类似功能（生成图表、HTML 预览），但交互非常有限。

### 3. 交互式 GenUI

用户可直接与生成的 UI 组件交互——书籍卡片包含可点击的 "Buy Now" 按钮，用点击代替文字命令完成购买。

## 为什么 FastHTML 适合 GenUI？

### 问题：契约耦合 (Contract Coupling)

传统 SPA 架构中，前端和后端通过数据契约耦合——前端只能渲染它预先知道的 JSON 结构。当 LLM 动态生成新的 UI 模式时：

- LLM 生成新的数据结构，前端不知如何渲染
- LLM 想创建新的交互模式，前端代码需更新
- 任何新 UI 组件都需要预定义的前端渲染逻辑

### 解决方案：超媒体架构 (Hypermedia)

FastHTML + HTMX 采用超媒体方法——一切发生在后端。LLM 服务器动态生成新内容和 UI 组件，发送完整 HTML 而非 JSON 数据。客户端只需处理标准 HTML 和 HTMX 属性，无需特定应用数据结构。

> **核心洞察**: "AI is the new UI"——所有传统数字交互将越来越多地通过 AI 介导系统进行。随着 MCP (Model Context Protocol) 等标准普及，工具将通过 AI 接口被调用。如果这些工具仍停留于纯文本界面，用户体验将远不如传统 GUI。GenUI 通过让 LLM 生成富交互界面，弥合了这一鸿沟。

## 基本文本聊天机器人

### 代码示例

```python
from claudette import Client

# 设置聊天模型 (https://claudette.answer.ai/)
cli = Client(models[-1])

# 用户消息输入框——同时利用 OOB 交换实现发送后清空
def ChatInput():
    return Input(name='msg', id='msg-input', placeholder="Type a message",
                 hx_swap_oob='true')

# 主界面
@app.get
def index():
    page = Form(hx_post=send, hx_target="#chatlist", hx_swap="beforeend")(
        Div(id="chatlist"),
        Div()(
            Group(ChatInput(), Button("Send"))
        )
    )
    return Titled('Chatbot Demo', page)

# 处理表单提交
@app.post
def send(msg: str, messages: list[str] = None):
    if not messages:
        messages = []
    messages.append(msg.rstrip())
    r = contents(cli(messages, sp=sp))  # 从聊天模型获取回复
    return (
        ChatMessage(msg, user=True),      # 用户消息
        ChatMessage(r.rstrip(), user=False),  # 聊天机器人回复
        ChatInput()  # 通过 OOB 交换清空输入框
    )
```

### 关键概念

| 概念 | 说明 |
|------|------|
| `hx_post=send` | 表单提交到 `send` 端点 |
| `hx_target="#chatlist"` | 响应放入 `id="chatlist"` 的元素 |
| `hx_swap="beforeend"` | 在目标元素末尾追加响应 |
| `hx_swap_oob='true'` | Out-of-Band 交换——用返回的空输入替换当前输入（即清空效果） |
| Python 生成 HTML | 所有 UI 元素通过 Python 函数创建，LLM 易于生成 |

## 静态 GenUI：天气卡片组件

### WeatherComponent 工具函数

```python
def WeatherComponent(location: str, temperature: str, description: str):
    """生成类似 iPhone 天气应用的简洁天气卡片"""
    return Div(
        H2(location, cls="text-xl font-semibold mb-1"),
        # 天气内容
        # ...
    )
```

这个组件是纯 Python 函数，可直接作为 LLM 的工具（tool）使用。

### 修改后的消息处理

```python
@app.post
def send(msg: str, messages: list[str] = None):
    if not messages:
        messages = []
    messages.append(msg.rstrip())

    cli = Client(model)
    sp = """You are a helpful assistant that invents weather for a specific location.
            Use the tool weather_component to generate a card for the given location."""
    r = cli.structured([sp, msg], tools=[WeatherComponent])
    return (
        ChatMessage(msg, True),
        r[0],
        ChatInput()
    )
```

> **模式要点**: LLM 通过 tool calling 调用预定义的 Python 组件函数。组件返回 FastHTML FT 对象，直接作为 HTTP 响应返回给浏览器渲染。无需额外前端代码。

## 交互式 GenUI：反馈循环模式

### 核心机制：反馈循环

```
[浏览器] 用户点击按钮
    │ 通过 HTMX 发送数据到 /send 端点
    ▼
[FastHTML 端点] 接收数据
    │ 传递给 LLM（含工具）
    ▼
[LLM] 调用工具生成新 UI 组件
    │ 工具生成包含 HTMX 属性的 HTML 组件
    ▼
[FastHTML 端点] 将组件直接返回给浏览器
    │ 无需前端代码解释——纯 HTML 渲染
    ▼
[浏览器] 渲染新组件 → 用户可再次点击 → 重启循环
```

### 单端点模式

```python
@app.post('/send')
async def send(data):
    html_component = chat(data, tools=[generate_response])
    return html_component  # 直接将组件返回给浏览器
```

### 动态按钮生成工具

```python
def generate_response(options: list[str]):
    """为每个选项生成一个带 HTMX 属性的 Button()"""
    return [
        Button(option,
               name=option,      # LLM 在按钮点击时收到的值
               hx_post="/send")  # 指向我们的端点
        for option in options
    ]
```

调用示例：
```python
generate_response(["Option A", "Option B", "Option C"])
```

### 交互式 GenUI 的威力

- **消除契约耦合**: 前后端之间无需预定义数据契约
- **浏览器 = 渲染引擎**: 浏览器仅负责渲染 HTML，无需理解应用逻辑
- **LLM 完全控制 UI**: LLM 通过生成 HTML 组件动态控制整个用户体验
- **端到端闭环**: 按钮点击 → 发送到端点 → LLM 处理 → 生成新组件 → 渲染 → 再次点击

## 终极 GenUI：文本 + 按钮的融合

### 统一端点处理所有交互

以下示例是 HAL 9000 模拟器，同时支持文字聊天和按钮点击两种交互方式：

```python
@app.post
async def send(request):
    form_data = await request.form()
    usr_choice = first(form_data.keys())       # 按钮点击结果
    usr_msg = form_data.get('user_message', '')  # 输入框文字

    # 统一处理两种输入来源
    msg = usr_msg if usr_msg else usr_choice
    if msg:
        messages.append(msg)

    # 获取 LLM 响应
    r = cli.structured(messages, tools=[generate_hal_response])

    # LLM 的 generate_hal_response 工具返回包含 4 个元素的元组：
    # 1. HAL 的回复文本
    # 2. 环境描述
    # 3. 颜色组件（表示 HAL 的情绪）
    # 4. 新的导航按钮
    response_text, environment_description, color_component, new_buttons = r[0]

    # 返回更新的 UI 组件
    return (
        UserReply(msg),
        HalMessage(response_text),
        EnvironmentMessage(environment_description),
        new_buttons,
        color_component,
        InputArea()
    )
```

### 输入区域组件（支持文字输入）

```python
def InputArea():
    return Div(id="input-container", cls="input-container", hx_swap_oob="true")(
        Textarea(
            placeholder="Use the input to talk to HAL...",
            name="user_message",
            id="user-input",
            hx_post=send,
            hx_target="#chatlist",
            hx_swap="beforeend",
            hx_trigger="keydown[key=='Enter']"
        ),
        Button("Send", cls="hal-button send-button", hx_post=send)
    )
```

### OOB 交换详解

| 属性 | 作用 |
|------|------|
| `hx_swap_oob='true'` | 使 HTMX 用响应中相同 ID 的元素替换页面上的元素——用于清空输入框 |
| `hx_post=send` | 提交到 `send` 端点 |
| `hx_target="#chatlist"` | 响应放入 `chatlist` 元素 |
| `hx_swap="beforeend"` | 在末尾追加（不替换已有内容） |
| `hx_trigger="keydown[key=='Enter']"` | 按 Enter 键触发提交 |

## 实战 Demo 完整源码

> 来源仓库：[github.com/kafkasl/genUI](https://github.com/kafkasl/genUI)。三个 demo 的核心逻辑都集中在各自的 `main.py`（组件 + 路由 + LLM 工具调用），外加 `requirements.txt`；部分 demo 还带 `style.css` 与图片素材——`your_color` 有 `moon.jpg` / `hiroshige.webp`，`hal9000` 有 `hal-9000.svg` / `discovery-background.jpg`，而 weather 仅 `main.py` + `requirements.txt`。
>
> 这正是 GenUI 的核心卖点——**一个文件就能跑通完整的生成式 UI 闭环**，没有前端构建链、没有 JSON schema、没有状态管理。

### Demo 1：weather（展示型 GenUI）

**依赖**（`requirements.txt`）：

```
python-fasthtml
monsterUI
fastcore
claudette
```

**完整 `main.py`**（已加中文注释）：

```python
from fasthtml.common import *
from monsterUI.all import *          # 提供 Theme / Titled / ContainerT 等
from claudette import *              # Anthropic 客户端封装
from datetime import datetime

hdrs = Theme.blue.headers()          # MonsterUI 主题 → 注入 DaisyUI/Tailwind CDN
app, rt = fast_app(hdrs=hdrs)
model = 'claude-3-5-haiku-20241022'

# ── ① 组件即工具：这个纯 Python 函数会被当成 LLM 的 tool ────────────
def WeatherComponent(location: str, temperature: str, description: str):
    """生成类似 iPhone 天气应用的简洁天气卡片"""
    weather_icons = {
        "sunny":  "https://openweathermap.org/img/wn/01d@2x.png",
        "cloudy": "https://openweathermap.org/img/wn/03d@2x.png",
        "rainy":  "https://openweathermap.org/img/wn/10d@2x.png",
    }
    icon = weather_icons.get(description.lower(), weather_icons["sunny"])
    return Div(cls="p-4 bg-sky-500 text-white rounded-xl shadow-lg w-64")(
        H2(location, cls="text-xl font-semibold mb-1"),
        Div(cls="text-sm opacity-80")(
            datetime.now().strftime("%A, %H:%M"), " · ", description.title()
        ),
        Div(cls="flex items-center justify-between mt-2")(
            Span(f"{temperature}°", cls="text-5xl font-light"),
            Img(src=icon, cls="w-16 h-16"),
        ),
    )

# ── ② 聊天气泡 + 隐藏字段回传历史消息 ─────────────────────────────
def ChatMessage(msg, user):
    bubble_class = "chat-bubble-primary" if user else "chat-bubble-secondary"
    chat_class   = "chat-end"            if user else "chat-start"
    return Div(cls=f"chat {chat_class}")(
        Div("user" if user else "assistant", cls="chat-header"),
        Div(msg, cls=f"chat-bubble {bubble_class}"),
        Hidden(msg, name="messages"),    # 关键：把历史塞回表单，实现无状态多轮
    )

# ── ③ OOB 输入框：返回同 id 元素即可自动清空 ──────────────────────
def ChatInput():
    return Input(name='msg', id='msg-input', placeholder="Type a message",
                 cls="input input-bordered w-full", hx_swap_oob='true')

@app.get
def index():
    page = Form(hx_post=send, hx_target="#chatlist", hx_swap="beforeend")(
        Div(id="chatlist", cls="chat-box h-[73vh] overflow-y-auto"),
        Div(cls="flex space-x-2 w-full")(
            ChatInput(), Button("Send", cls="btn btn-primary")
        ),
    )
    return Titled('Weather Component', page, cls=ContainerT.sm)

# ── ④ 单端点：LLM structured 调用 → 直接返回 FT 组件 ───────────────
@app.post
def send(msg: str, messages: list[str] = None):
    if not messages:
        messages = []
    messages.append(msg.rstrip())
    cli = Client(model)
    sp = """You are a helpful assistant that invents weather for a specific location.
            Use the tool WeatherComponent to generate a card for the given location."""
    r = cli.structured([sp, msg], tools=[WeatherComponent])
    if not r:
        # DeepSeek 等 Anthropic 兼容端点偶尔不调用工具、直接返回文本，r 为空
        return (ChatMessage(msg, True),
                ChatMessage("模型这次没有生成天气卡片（端点未稳定调用工具），请再点一次 Send。", False),
                ChatInput())
    return (ChatMessage(msg, True), r[0], ChatInput())

serve()
```

**四个必须理解的点**：

| 编号 | 机制 | 为什么重要 |
|------|------|-----------|
| ① | 组件函数直接进 `tools=[...]` | claudette 读取函数签名+docstring 自动生成 tool schema；**函数返回值就是 UI**，不是 JSON |
| ② | `Hidden(msg, name="messages")` | FastHTML 无状态多轮的惯用法：历史藏在表单里随下次提交回传，服务端不存 session |
| ③ | `hx_swap_oob='true'` | 返回一个同 `id="msg-input"` 的空输入框 → HTMX 自动替换 → 输入框清空 |
| ④ | `r[0]` 直接放进返回元组 | `cli.structured()` 返回的是**工具函数的真实返回值列表**，即 FT 对象，可直接混进 HTTP 响应 |

### Demo 2：your_color（交互式 GenUI）

正念冥想应用。LLM 每轮返回「一个颜色 + 一段反思文字 + 三个可点按钮」，用户全程只需点击。

关键差异（相对 weather）：

```python
# 工具签名带 options，LLM 自行决定下一轮给哪几个选项
def generate_response(color: str, reflection: str, options: list[str]):
    """Generate the color card, the reflection text and the next choices."""
    return (
        ColorCard(color, reflection),
        generate_buttons(options),
    )

def generate_buttons(options):
    return Div(cls="options-container", id="options", hx_swap_oob="true")(
        *[Button(o, name=o, value="1",
                 hx_post=send, hx_target="#chatlist", hx_swap="beforeend",
                 hx_indicator="#loading",          # 点击时显示 loading
                 cls="option-button")
          for o in options]
    )

# ColorCircle：把 LLM 给出的颜色叠加到 moon.jpg 之上（SVG 蒙版）
def ColorCircle(color):
    return Div(cls="color-circle-wrap")(
        Img(src="/moon.jpg", cls="moon"),
        NotStr(f'<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="48" '
               f'fill="{color}" fill-opacity="0.55"/></svg>'),
    )

@app.post
async def send(request):
    form = await request.form()
    # 按钮点击 → key 是按钮名；输入框 → key 是 'msg'
    ...
    r = cli.structured(messages, tools=[generate_response, generate_finish_response])
    return (*r[0], InputArea())

serve(reload=True)
```

**要点**：`hx_swap_oob="true"` 用在**按钮容器**上——每轮 LLM 返回新按钮组，整块替换旧按钮组，天然实现「导航状态由 LLM 掌控」。

### Demo 3：hal9000（融合式 GenUI）

《2001 太空漫游》HAL 9000 模拟器，**同一个 `/send` 端点同时接受文字输入和按钮点击**，这是本文档 [终极 GenUI](#终极-genui文本--按钮的融合) 一节的完整实现。

```python
def generate_hal_response(color: str, mood_description: str, response_text: str,
                          environment_description: str, options: list[str]):
    """HAL 的一轮完整输出：情绪色 + 心情描述 + 台词 + 环境 + 下一步选项"""
    return (response_text, environment_description,
            ColorCard(color, mood_description), generate_buttons(options))

def ColorCard(color, mood):
    # 读取 hal-9000.svg，把里面的 <stop stop-color="..."> 按情绪替换
    svg = Path('hal-9000.svg').read_text()
    svg = svg.replace('#FF0000', color)
    return Div(cls="hal-eye", id="hal-eye", hx_swap_oob="true")(NotStr(svg), P(mood))

@app.post
async def send(request):
    form_data  = await request.form()
    usr_choice = first(form_data.keys())            # 按钮点击
    usr_msg    = form_data.get('user_message', '')  # 文本输入
    msg = usr_msg if usr_msg else usr_choice        # 统一成一条消息
    ...

serve(reload=True, port=5001)
```

**要点**：`first(form_data.keys())` 是 fastcore 的工具函数。按钮点击时表单只带按钮自己的 `name`，因此取第一个 key 即可拿到用户选了什么——**不需要为按钮和输入框各写一个端点**。

---

## 如何运行 GenUI（实操指南）

### 步骤 1：拿到源码

```bash
git clone https://github.com/kafkasl/genUI.git
cd genUI/weather        # 或 your_color / hal9000
```

### 步骤 2：安装依赖

```bash
pip install -r requirements.txt
```

> Windows 下若使用 WorkBuddy 内置 Python，请用绝对路径调用，例如：
> `"C:\Users\<你>\.workbuddy\binaries\python\versions\<ver>\python.exe" -m pip install -r requirements.txt`

### 步骤 3：配置 LLM 凭证（这是唯一的硬前提）

三个 demo 都用 `claudette`（Anthropic SDK 封装），读取标准 Anthropic 变量。两种接法：

**A. 官方 Anthropic（原始要求）**——读取 `ANTHROPIC_API_KEY`：

```bash
# PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
# cmd
set ANTHROPIC_API_KEY=sk-ant-...
# bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**B. DeepSeek 兼容端点（本技能 07 示例默认采用）**——把 Anthropic SDK 指向 DeepSeek 的 Anthropic 兼容地址，模型名自动映射（如 `claude-3-5-haiku-*` → `deepseek-v4-flash`、`claude-3-5-sonnet-*` → `deepseek-v4-flash`、`claude-opus-*` → `deepseek-v4-pro`）：

```bash
# PowerShell（用户级永久）
setx ANTHROPIC_BASE_URL "https://api.deepseek.com/anthropic"
setx ANTHROPIC_AUTH_TOKEN "sk-..."        # 即 DeepSeek API Key
# 也可在示例目录放 .env（ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN），壳会优先读环境变量、其次 .env
```

> 注意：`ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` 是 Anthropic SDK 通用变量，**设为全局后会劫持本机所有调用 Anthropic SDK 的程序**。仅想单目录生效时，用示例目录的 `.env` 即可，无需改全局。

**没有 LLM Key 怎么办？** 两条改造思路（注意：本技能的 `examples/07-genui-weather` **并未**实现离线兜底——没配 Key 时页面能打开，但发起对话会报 401 / 工具未调用，属上游行为）：

1. **换客户端**：把 `from claudette import *` + `Client(model)` 换成任意 OpenAI 兼容客户端，只要能做 tool calling 即可。工具函数（即组件）本身完全不用改。
2. **本地兜底**：自己写一个不依赖网络的「假 LLM」，按关键词决定调用哪个组件函数，让无 Key 也能演示 UI 闭环。

### 步骤 4：启动

```bash
python main.py
```

`serve()` 内部即 `uvicorn.run(...)`，默认监听 `http://localhost:5001`（weather 用 `serve()` 默认端口 5001，hal9000 显式写了 `port=5001`）。

### 步骤 5（可选）：部署到 Plash

```bash
pip install plash-cli
# 在 demo 目录创建 plash.env，填入 ANTHROPIC_API_KEY 等
plash_deploy
```

Plash 是 Answer.ai 的 FastHTML 托管服务（测试阶段），会把整个目录连同 `requirements.txt` 一起部署。

### 常见坑

| 现象 | 原因 | 处理 |
|------|------|------|
| `AuthenticationError` | 未设 `ANTHROPIC_API_KEY` | 见步骤 3 |
| 页面无样式 | MonsterUI 走 CDN，断网即裸奔 | 桌面/离线场景改为本地 CSS（见下节） |
| 按钮点击无反应 | 按钮不在 `<form>` 内且未写 `hx_post` | 每个 Button 都要显式 `hx_post=send` |
| 多轮对话「失忆」 | 忘了 `Hidden(msg, name="messages")` | 历史必须随表单回传 |
| `r[0]` 报 IndexError | LLM 没调工具而是直接回文本 | system prompt 里强制 "Use the tool ..."，并对 `r` 做类型兜底（07 的 weather/main.py 已内置 `if not r:` 兜底，返回提示而非崩溃） |

---

## 在 fasthtml-desktop 中落地 GenUI

### 抽取决策：三个 demo 全部完整克隆进 07

| Demo | 是否纳入 `examples/07-genui-weather` | 说明 |
|------|--------------------------------------|------|
| **weather** | ✅ 完整克隆上游 | 展示型：结构最干净，最能讲清「组件即工具」 |
| **your_color** | ✅ 完整克隆上游 | 交互式：单端点 + 工具返回 FT + 按钮循环，依赖 `moon.jpg` / `hiroshige.webp` |
| **hal9000** | ✅ 完整克隆上游 | 融合式：文字输入 + 按钮点击同一端点，依赖 `hal-9000.svg` / `discovery-background.jpg` |

> **现状（2026-08 修正）**：早期方案是「只抽 weather、其余仅在文档解析」，但本技能后期将 `07-genui-weather` 改为 **kafkasl/genUI 的完整克隆**——三个 demo 上游代码原样放入 `weather/` `your_color/` `hal9000/` 子目录，**不改动任何上游业务代码**，仅在外层追加桌面壳（`main.py` / `claudette_compat.py` / `启动-*.bat` / `requirements.txt` / `dev_check.py`）。这样 07 既是可运行示例，也是「重型 GenUI 应用」的完整参考语料。
>
> 三个 demo 通过环境变量 `GENUI_DEMO=weather|your_color|hal9000` 切换（默认 `weather`）；桌面壳 `main.py` 用 `claudette_compat.py` 启动包装修复 claudette 的 `mk_ns` 多工具 bug 并接管 uvicorn 参数，**不修改全局 site-packages、也不改上游代码**。

### 桌面化改造清单（kafkasl/genUI → 07-genui-weather）

从原版 demo 到符合本技能规范的桌面示例，07 实际做了这些事：

1. **加桌面壳、不拆上游**：上游每个 demo 的 `main.py` **原样保留**在 `weather/` `your_color/` `hal9000/` 子目录；外层新增 `main.py`（pywebview 外壳，含 `find_free_port()` / `wait_for_server()` / `SERVER_ONLY=1` 无头模式）与 `claudette_compat.py`（启动包装）。
2. **去 CDN 依赖**：MonsterUI 的 `Theme.blue.headers()` 会注入 CDN 链接，桌面应用断网即失去样式。示例中仍走 CDN（需联网渲染），离线场景可改为内联 `Style(...)` 或本地 `static/style.css`。
3. **LLM 接入（非离线兜底）**：桌面壳以极简 `.env` 加载（不引入第三方依赖）读取 `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN`（默认 DeepSeek 端点）或系统环境变量；不设 Key 时**页面可打开、对话会报错**——07 没有离线 mock 生成器，这不是缺陷。
4. **三件套 `启动-*.bat`（GBK + CRLF）**：`启动-weather.bat` / `启动-your_color.bat` / `启动-hal9000.bat`，分别 `set GENUI_DEMO=...` 后复用 `templates/shared/launcher.py`（自动定位 Python、装依赖、探测 WebView2 Runtime）。bat 名由 `gen_launchers.py` 的 `BAT_NAME` 配置驱动，改名不会被同步工具覆盖。
5. **双用途 README**：`README.md` 给人看、`README.genui.md` 保留上游原文，既是使用说明，也是给 Agent 看的复刻蓝图（问题→架构→关键代码→坑）。

### GenUI 与本技能其它章节的关系

| 你要做的事 | 去看 |
|-----------|------|
| 理解「组件即工具」的写法 | 本文档 [静态 GenUI](#静态-genui天气卡片组件) + [Demo 1](#demo-1weather展示型-genui) |
| 让组件在桌面窗口里跑起来 | `references/06-pywebview-shell.md` |
| 处理端点的类型标注与表单解析 | `references/10-ft-handlers-typing.md` |
| 打包成单文件 EXE | `references/08-packaging.md` + `references/packaging/01-core-workflow.md` |
| 界面质检（pywebview 原生视觉） | `references/quality-check/INDEX.md` |

## 架构总结

```
传统 SPA 架构:
  [前端: React/Vue] ←JSON 契约→ [后端 API] ←→ [LLM]
  问题: 契约耦合——前端需预知所有数据结构和UI模式

FastHTML GenUI 架构:
  [浏览器: 纯渲染HTML] ←HTML组件→ [FastHTML端点 + LLM]
  优势: 无契约耦合——LLM动态生成HTML，浏览器原生渲染
```

### 关键优势对比

| 维度 | 传统 SPA | FastHTML + HTMX |
|------|----------|-----------------|
| 前后端耦合 | 强（JSON 数据契约） | 无（HTML 超媒体） |
| 新 UI 模式 | 需更新前端代码 | LLM 动态生成 |
| 渲染方式 | 客户端渲染 (CSR) | 服务端渲染 (SSR) |
| 前端代码量 | 大量（路由、状态管理、组件库） | 极少（仅 HTML 模板） |
| 学习曲线 | 高（框架、工具链） | 低（Python + HTML） |
| LLM 友好度 | 需生成特定 JSON 格式 | 可直接生成 Python 组件 |

## 已知限制与注意事项

1. **当前实践**: 文中示例使用 LLM 进行 tool calling（调用预定义 Python 组件函数），而非让 LLM 直接生成 FastHTML 组件代码。更高级的做法是让 LLM 直接生成 FastHTML 组件作为 Python 代码，实现完全灵活的 UI 创作。

2. **模型能力**: 作者认为当前模型够好，通过清晰的提示词说明 FastHTML/HTMX 工作原理、单端点模式及示例，即可让 LLM 生成 GenUI 组件。

3. **库知名度**: FastHTML/HTMX 不如 React/Vue 流行，LLM 在生成某些 HTMX 特性（如 `hx-confirm`、`scroll` 行为）时可能出错。建议阅读 [Hypermedia Systems](https://hypermedia.systems/) 以深入理解。

4. **部署**: 可使用 [Plash](https://github.com/AnswerDotAI/plash_cli)（Answer.ai 的部署服务，测试阶段）一键部署。创建 `plash.env` 后运行 `plash_deploy` 即可。

## 参考链接

- [FastHTML 官网](https://fastht.ml)
- [HTMX](https://htmx.org)
- [Claudette (Answer.ai)](https://claudette.answer.ai/)
- [Hypermedia Systems](https://hypermedia.systems/)
- [L402 Protocol](https://github.com/l402-protocol/l402)
- [Plash CLI 部署工具](https://github.com/AnswerDotAI/plash_cli)

### 示例源码

- [基本聊天机器人](https://github.com/AnswerDotAI/fasthtml-example/blob/main/02_chatbot/basic.py)
- [天气组件 Demo](https://github.com/kafkasl/genUI/tree/main/weather)
- [情绪色彩正念 Demo](https://github.com/kafkasl/genUI/tree/main/your_color)
- [HAL 9000 Demo](https://github.com/kafkasl/genUI/tree/main/hal9000)
- [phact/code-assistant](https://github.com/phact/code-assistant) — 用 FastHTML 写的「造 FastHTML 应用的 AI 工具」，内含 13 个 LLM 生成的小应用

### 本技能内的可运行示例

| 目录 | 说明 |
|------|------|
| `examples/07-genui-weather/` | kafkasl/genUI 的**完整克隆**（weather / your_color / hal9000 三 demo 原样 + 桌面壳），DeepSeek 兼容端点接入，三件套 bat；需配 LLM Key 才能对话 |
| `examples/08-code-assistant/` | code-assistant 桌面外壳 + 13 个生成应用的清单与拆解 |

### 在线 Demo

- [天气 Demo](https://fasthtml-app-cbd32e55.pla.sh/)
- [情绪色彩正念](https://fasthtml-app-68e1764d.pla.sh/)
- [HAL 9000 Demo](https://fasthtml-app-6e583cfc.pla.sh/)

---

*本文档基于 [AI is the new UI: Generative UI with FastHTML](https://kafkasl.github.io/genUI/) 整理，作为 FastHTML 技能的补充参考文件。*

