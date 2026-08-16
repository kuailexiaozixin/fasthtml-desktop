# 七、场景驱动的架构类型选择

> 本文档由 `02-architecture.md` 自动拆分生成。
> 源文件：[../02-architecture.md](../02-architecture.md)

## 七、场景驱动的架构类型选择

### 场景与架构类型对照表

| 场景 | 架构类型 | 项目结构骨架 | 典型触发条件 |
|------|---------|------------|------------|
| **Pure FastHTML（UI Only）** | Monolith-first | `routes/` + `components/` + `services/` + `models/` | 纯表单/列表/操作界面，无外部接口 |
| **FastHTML + FastAPI** | Layered | 增加 `api/` 层（与 `routes/` 同级） | 需要对外提供 REST API |
| **FastHTML + Pydantic AI** | Layered + Agent | 增加 `agents/` 层（独立，不导入 fasthtml） | LLM 对话、Agent 推理 |
| **FastHTML + Playwright** | Plugin-based | 增加 `browser/` 独立模块 | 网页自动化、数据采集 |
| **FastHTML + 数据分析** | Layered | 增加 `analytics/` 层 | 大量 pandas/numpy 计算 |
| **多框架组合** | Plugin-based | 按需叠加多个扩展模块 | 同时需要 API + Agent + 数据 |

---

### 场景 1：Pure FastHTML（UI Only）

```
src/
├── main.py            ← 入口
├── app.py             ← 路由注册
├── routes/            ← 路由处理器
├── components/        ← FastTags 组件
├── services/          ← 业务逻辑
├── models/            ← Fastlite schema
└── utils/
```

这是**默认场景**。不需要任何额外框架，架构类型锁定为 Monolith-first。

---

### 场景 2：FastHTML + FastAPI

需要通过 REST API 对外暴露能力时，在同一进程内挂载两个 ASGI 应用：

```
src/
├── main.py          ← 统一入口
├── fasthtml_app.py  ← FastHTML 应用（UI）
├── fastapi_app.py   ← FastAPI 应用（REST API）
├── routes/          ← FastHTML 路由
├── api/             ← FastAPI 路由（/api/v1/*）
├── services/        ← 共享业务逻辑
└── models/
```

```python
from starlette.routes import Mount
from starlette.applications import Starlette

app = Starlette(routes=[
    Mount("/api", app=fastapi_app),
    Mount("/", app=fasthtml_app),
])
```

**架构类型**：Layered。API 层和 UI 层共享 services/ 和 models/。

---

### 场景 3：FastHTML + Pydantic AI

Agent 层必须与 UI 层彻底解耦——Agent 不导入 fasthtml，不返回 HTML 组件：

```
src/
├── routes/chat.py    ← 接收用户输入，渲染 Agent 响应
├── agents/           ← Agent 逻辑（纯 Python，不导入 fasthtml）
│   ├── chat_agent.py
│   └── tools.py
├── services/         ← Agent 调用的业务逻辑
└── models/
```

```
通信契约：
  routes/chat.py  →  agents/chat_agent.run(message) → str/dict
  routes/chat.py  ←  agents/chat_agent 返回结果
  routes/chat.py  →  渲染为 HTML 片段
```

**架构类型**：Layered + Agent 模块。Agent 层作为独立模块，与 routes/services/models 同层级。

---

### 场景 4：FastHTML + Playwright

Playwright 管理独立的浏览器进程，与 FastHTML 页面完全解耦：

```
src/
├── routes/crawl.py     ← 用户操作的 UI 层
├── browser/             ← 浏览器自动化（独立进程管理）
│   ├── crawler.py       ── 封装 Playwright 操作
│   └── automator.py     ── 自动化流程编排
├── services/
└── models/
```

```python
# browser/crawler.py — 纯自动化逻辑，不感知 FastHTML
class Crawler:
    def __init__(self):
        self.browser = None

    def start(self):
        p = sync_playwright().start()
        self.browser = p.chromium.launch(headless=True)

    def scrape(self, url: str) -> dict:
        page = self.browser.new_page()
        page.goto(url)
        return {"title": page.title(), "content": page.content()[:1000]}
```

**架构类型**：Plugin-based。browser/ 是独立插件，与主应用通过数据接口通信。

---

### 场景 5：FastHTML + 数据分析

大量 pandas/numpy 计算需要独立于 UI 层：

```
src/
├── routes/analytics.py  ← 用户操作的 UI 层
├── analytics/            ← 数据分析（纯计算，不感知 FastHTML）
│   ├── processors.py     ── 数据处理管道
│   └── visualizations.py ── 图表生成
├── services/
└── models/
```

**架构类型**：Layered。analytics/ 层与 services/ 同级，专注于数据处理。

---

### 场景 6：多框架组合

同时需要 API + Agent + 数据 + 自动化的高度复杂场景：

```
src/
├── fasthtml_app.py    ← FastHTML 应用
├── fastapi_app.py     ← FastAPI 应用
├── routes/            ← FastHTML 路由
├── api/               ← FastAPI 路由
├── agents/             ← Pydantic AI Agent
├── browser/            ← Playwright 自动化
├── analytics/          ← 数据分析
├── services/           ← 共享业务逻辑
├── models/             ← 数据模型
├── components/         ← UI 组件
└── utils/
```

**架构类型**：Plugin-based。每个扩展模块（agents/、browser/、analytics/）是独立插件，
通过 services/ 和 models/ 共享数据，模块之间不直接依赖。

**核心约束**：
1. agents/、browser/、analytics/ **不能导入 fasthtml 或 fastapi**
2. 模块之间不直接调用，通过 services/ 协调
3. 每个插件模块有独立的生命周期（init → process → cleanup）

---
