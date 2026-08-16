# FastHTML 搭配 FastAPI 构建 RESTful API

## 背景与问题

fasthtml 是**HTML 优先**的框架——它的 `FastHTML` 类继承自 `Starlette`，专为服务端渲染的
超媒体应用设计。官方明确指出：

> **不兼容 FastAPI 语法**；FastHTML 不是用来创建 API 服务的。

但桌面应用（fasthtml-desktop 场景）有时需要同时提供：
- **HTML 页面**（由 fasthtml 渲染，pywebview 展示）
- **RESTful API**（供外部系统/插件/前后端分离调用）
- **自动生成 OpenAPI 文档**（便于 API 消费者接入）

解决方案：**在同一个 uvicorn 进程中，将 FastAPI 应用作为子应用挂载到 fasthtml 下**。

---

## 方案：挂载 FastAPI 子应用（推荐）

利用底层 Starlette 的 `mount()` 机制，将 FastAPI 应用挂载到指定路径前缀（如 `/api`），
与 fasthtml 页面路由共存于同一个进程和端口。fasthtml 负责页面，FastAPI 负责 API + OpenAPI。

### 项目结构

```
my_app/
├── src/
│   ├── __init__.py
│   ├── main.py              # 入口：启动 fasthtml + fastapi 集成
│   ├── web/
│   │   ├── __init__.py
│   │   └── routes.py        # fasthtml 页面路由
│   └── api/
│       ├── __init__.py
│       ├── router.py        # FastAPI APIRouter（RESTful 端点）
│       └── schemas.py       # Pydantic 模型（自动生成 OpenAPI schema）
├── launcher.json
├── requirements.txt
└── pyproject.toml
```

### 代码实现

```python
# main.py
from fasthtml.common import *
from src.api.router import api_router
from src.web.routes import setup_page_routes

# 1. 创建 fasthtml 应用（页面层）
app, rt = fast_app()

# 2. 创建 FastAPI 子应用（API 层）
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

api_app = FastAPI(
    title="My App API",
    version="1.0.0",
    docs_url="/docs",           # OpenAPI Swagger UI（挂载后为 /api/docs）
    redoc_url="/redoc",         # ReDoc（挂载后为 /api/redoc）
    openapi_url="/openapi.json" # OpenAPI schema（挂载后为 /api/openapi.json）
)

# 3. 注册 API 路由
api_app.include_router(api_router)

# 4. 在 FastAPI 子应用上添加 CORS 中间件（API 需要对外暴露，故加在 api_app 上而非 fasthtml app）
api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "HEAD", "OPTIONS", "POST", "PUT", "DELETE"],
    allow_headers=["Accept", "Content-Type", "Authorization"],
)

# 5. 将 FastAPI 子应用挂载到 /api 路径
#    FastHTML 继承自 Starlette，.mount() 来自 Starlette 的 ASGI 子应用挂载机制
app.mount("/api", api_app)

# 6. 注册 fasthtml 页面路由
setup_page_routes(app, rt)
```

```python
# api/schemas.py
from pydantic import BaseModel, Field

class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)  # 无默认值即为必填，不用 Ellipsis
    description: str | None = None
    price: float = Field(gt=0)

class ItemResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    price: float
```

```python
# api/router.py
from fastapi import APIRouter, HTTPException
from .schemas import ItemCreate, ItemResponse

# prefix/tags 声明在 APIRouter 上，不在 include_router 中传递
api_router = APIRouter(prefix="/v1", tags=["items"])

# 模拟数据存储
_items: dict[int, dict] = {}
_next_id = 1

@api_router.get("/items")
def list_items() -> list[ItemResponse]:
    """获取所有条目（自动生成 OpenAPI 文档）"""
    return [ItemResponse(id=k, **v) for k, v in _items.items()]

@api_router.get("/items/{item_id}")
def get_item(item_id: int) -> ItemResponse:
    """获取单个条目"""
    if item_id not in _items:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemResponse(id=item_id, **_items[item_id])

@api_router.post("/items", status_code=201)
def create_item(item: ItemCreate) -> ItemResponse:
    """创建条目"""
    global _next_id
    _items[_next_id] = item.model_dump()
    _next_id += 1
    return ItemResponse(id=_next_id - 1, **item.model_dump())
```

```python
# web/routes.py
from fasthtml.common import *

def setup_page_routes(app, rt):
    @rt("/")
    def index():
        return Titled("Home", H1("My App"), P("fasthtml 页面与 FastAPI 共存"))

    @rt("/items")
    def items_page():
        # 页面可通过 hx-get 调用 /api/v1/items 获取数据
        return Titled("Items", Div(id="items-list", hx_get="/api/v1/items"))
```

### 启动

```bash
# 启动后：
# - http://localhost:5001/          → fasthtml 页面
# - http://localhost:5001/api/v1/items → FastAPI RESTful API
# - http://localhost:5001/api/docs   → Swagger UI（OpenAPI 文档）
# - http://localhost:5001/api/redoc  → ReDoc
# - http://localhost:5001/api/openapi.json → OpenAPI schema
# 双击启动.bat（或终端执行 python src/main.py）
```

> **启动链**：`启动.bat` → `launcher.py` → `src/main.py`（`serve()` 启动 uvicorn，
> 同时提供页面和 API）。`launcher.resolve_entry()` 自动扫描 `src/main.py` → `main.py`。
> 开发调试阶段也可直接 `python src/main.py`。

---

## OpenAPI 文档自动生成

FastAPI 子应用**自动生成** OpenAPI 文档，无需额外配置：

- `docs_url="/docs"` → Swagger UI（交互式 API 浏览）
- `redoc_url="/redoc"` → ReDoc（替代文档风格）
- `openapi_url="/openapi.json"` → OpenAPI 3.1 schema（JSON）

所有在 `api_router` 中注册的端点（含 Pydantic 请求/响应模型、参数校验、描述文档）
**自动出现在 OpenAPI 文档中**。fasthtml 页面路由不会出现在 API 文档中（两者互不干扰）。

---

## 在桌面应用中的使用

在 fasthtml-desktop 场景下，此模式适用于：

| 场景 | 说明 |
|---|---|
| **本地 HTTP API** | 桌面应用需对外暴露 RESTful 接口（如被其他工具调用） |
| **前后端分离** | 前端用 pywebview 加载 HTML，后端用 FastAPI 提供数据接口 |
| **插件系统** | 第三方插件通过 API 与桌面应用交互 |
| **调试/运维** | 通过 Swagger UI 直接在浏览器中调试接口 |

### 桌面应用启动

fasthtml-desktop 的标准启动链：

```
用户双击 启动.bat  →  launcher.py（依赖预检/环境决策）  →  src/main.py（serve() 启动 uvicorn）
```

`src/main.py` 内部调用 `serve()` 启动 uvicorn，同时提供 fasthtml 页面和 FastAPI 接口。
pywebview 在 `launcher.py` 中启动，加载 `http://localhost:5001/` 页面。

开发调试阶段也可直接运行 `python src/main.py`（跳过 launcher 的依赖预检）。

---

## 注意事项

### 1. 路由冲突
- fasthtml 页面路由与 FastAPI 路由**不会冲突**（`/api` 路径前缀被 mount 隔离）。
- 避免在 fasthtml 中定义与 `/api` 开头的同名路由（会被 mount 覆盖）。

### 2. Session 隔离
- fasthtml 的 `session`（基于 Starlette 中间件）**对 FastAPI 子应用不可见**。
- FastAPI 端需独立管理身份认证（如 JWT Token、API Key）。

### 3. Static 文件
- fasthtml 的 `StaticFiles` 和 FastAPI 的 `StaticFiles` 互不干扰。
- fasthtml 静态资源（如 `static/`）通过 `app.mount("/static", StaticFiles(...))` 提供。

### 4. 数据库共享
- fasthtml 和 FastAPI 可以共享同一个数据库连接（如 `fastlite` 或 `SQLModel`）。
- 建议在 `app.state` 或全局单例中管理连接，避免重复创建。

### 5. 错误处理
- fasthtml 的异常处理（`@app.exception_handler`）与 FastAPI 的异常处理独立。
- 各自注册各自的异常处理器。

### 6. CORS
- 如果 API 被外部（非 pywebview 内）调用，需在 FastAPI 端添加 CORS 中间件。
- 在 `api_app` 上添加 `CORSMiddleware`，而非 fasthtml 的 `app`。

---

## 打包注意事项

使用 FastAPI 的项目在 PyInstaller 打包时，需要额外声明以下懒加载模块的
`--hidden-import`（否则 EXE 在导入 fastapi 时崩溃）：

- `fastapi`
- `uvicorn`
- `pydantic`
- `starlette`
- `yaml`（FastAPI 依赖）
- `multipart`（FastAPI 表单解析依赖）

这些模块应写入 `src/pyinstaller_hidden_imports.txt`（每行一个模块名），
由 `build_windows_exe.py` 自动读取并追加到 PyInstaller 命令。

```
# src/pyinstaller_hidden_imports.txt
fastapi
uvicorn
pydantic
starlette
```

> 若手动传递 `--hidden-import`，标准打包命令参考：
> ```
> python -m PyInstaller --onefile --console --noupx --name MyApp ^
>   --collect-submodules fasthtml ^
>   --hidden-import clr ^
>   --hidden-import webview.platforms.winforms ^
>   --hidden-import webview.platforms.edgechromium ^
>   --hidden-import fastapi ^
>   --hidden-import uvicorn ^
>   --hidden-import pydantic ^
>   --hidden-import starlette ^
>   --add-data "src;src" ^
>   --exclude-module unittest
> ```

---

## API 设计原则

遵循 RESTful API 设计规范，构建一致、可维护、开发者友好的接口。

### 资源命名

```
# 资源名用复数名词、小写、kebab-case
GET    /api/v1/users
GET    /api/v1/users/:id
POST   /api/v1/users
PUT    /api/v1/users/:id
PATCH  /api/v1/users/:id
DELETE /api/v1/users/:id

# 子资源表达从属关系
GET    /api/v1/users/:id/orders
POST   /api/v1/users/:id/orders

# 非 CRUD 操作（谨慎使用动词）
POST   /api/v1/orders/:id/cancel
```

**命名规则**：
- 多词资源用 kebab-case（`/team-members`）
- 复数（`/users` 而非 `/user`）
- 不用动词（`/users` 而非 `/getUsers`）
- 不用 snake_case（`/team-members` 而非 `/team_members`）

### HTTP 方法与状态码

| 方法 | 幂等 | 安全 | 用途 |
|------|------|------|------|
| GET | 是 | 是 | 获取资源 |
| POST | 否 | 否 | 创建资源、触发动作 |
| PUT | 是 | 否 | 全量替换 |
| PATCH | 否* | 否 | 部分更新 |
| DELETE | 是 | 否 | 删除资源 |

*PATCH 可通过正确实现变成幂等

**状态码**：
```
# 成功
200 OK          — GET, PUT, PATCH（有响应体）
201 Created     — POST（含 Location 头）
204 No Content  — DELETE, PUT（无响应体）

# 客户端错误
400 Bad Request           — 校验失败、无效 JSON
401 Unauthorized          — 缺少/无效认证
403 Forbidden             — 已认证但无权限
404 Not Found             — 资源不存在
409 Conflict              — 重复条目、状态冲突
422 Unprocessable Entity  — 语义无效（JSON 合法，数据不合法）
429 Too Many Requests     — 限流触发

# 服务端错误
500 Internal Server Error — 意外失败（绝不暴露细节）
502 Bad Gateway           — 上游服务失败
503 Service Unavailable   — 临时过载（含 Retry-After）
```

### 响应格式

**成功响应**：
```json
{
  "data": { "id": "abc-123", "email": "alice@example.com", "name": "Alice" }
}
```

**集合响应（含分页）**：
```json
{
  "data": [{ "id": "abc-123", "name": "Alice" }],
  "meta": { "total": 142, "page": 1, "per_page": 20, "total_pages": 8 },
  "links": { "self": "/api/v1/users?page=1", "next": "/api/v1/users?page=2", "last": "/api/v1/users?page=8" }
}
```

**错误响应**：
```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": [
      { "field": "email", "message": "Must be a valid email address", "code": "invalid_format" }
    ]
  }
}
```

### 分页

| 类型 | 适用场景 | 优缺点 |
|------|----------|--------|
| **Offset 分页** | 管理后台、小数据集（<10K）、搜索（用户期望页码） | 实现简单，支持跳页；大偏移量性能差 |
| **Cursor 分页** | 无限滚动、Feed、大数据集、公开 API | 性能稳定，与并发插入一致；不支持跳页 |

**Offset 分页**：`GET /api/v1/users?page=2&per_page=20`

**Cursor 分页**：
```
GET /api/v1/users?cursor=eyJpZCI6MTIzfQ&limit=20
# 响应：
{ "data": [...], "meta": { "has_next": true, "next_cursor": "eyJpZCI6MTQzfQ" } }
```

### 过滤、排序与搜索

```
# 过滤：括号表示法表示比较条件
GET /api/v1/orders?status=active&customer_id=abc-123
GET /api/v1/products?price[gte]=10&price[lte]=100
GET /api/v1/orders?created_at[after]=2025-01-01

# 多值（逗号分隔）
GET /api/v1/products?category=electronics,clothing

# 排序（- 前缀为降序）
GET /api/v1/products?sort=-created_at
GET /api/v1/products?sort=-featured,price

# 全文搜索
GET /api/v1/products?q=wireless+headphones

# 稀疏字段（减少 payload）
GET /api/v1/users?fields=id,name,email
```

### 认证与授权

```
# Bearer Token（标准方式）
GET /api/v1/users
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

# API Key（服务间调用）
GET /api/v1/data
X-API-Key: sk_live_abc123
```

授权模式：资源级（检查所有权）、角色级（检查权限）。

### 限流

```
# 响应头
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000

# 超限时
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

| 分级 | 限频 | 窗口 | 适用 |
|------|------|------|------|
| 匿名 | 30/min | 按 IP | 公开端点 |
| 已认证 | 100/min | 按用户 | 标准 API |
| 付费 | 1000/min | 按 API Key | 付费计划 |
| 内部 | 10000/min | 按服务 | 服务间 |

### 版本策略

- **URL 路径版本化**（推荐）：`/api/v1/users`，显式、易路由、可缓存
- 最多同时维护 2 个活跃版本（当前 + 上一个）
- 弃用通知：公开 API 提前 6 个月，加 `Sunset` 头
- 非破坏性变更**不**需要新版本（新增字段、可选参数、新增端点）
- 破坏性变更需要新版本（删除/重命名字段、修改类型、修改 URL 结构）

### API 设计检查清单

- [ ] 资源 URL 符合命名规范（复数、kebab-case、无动词）
- [ ] 使用正确的 HTTP 方法（GET 读、POST 建、DELETE 删等）
- [ ] 意义明确的状态码（不是 200 通吃）
- [ ] 输入用 Pydantic/Zod 校验
- [ ] 错误响应格式统一（含 code 和 message）
- [ ] 列表接口有分页
- [ ] 需要认证（或明确标记为公开）
- [ ] 有权限检查（用户只能访问自己的资源）
- [ ] 配置了限流
- [ ] 响应不暴露内部细节（堆栈、SQL 错误）
- [ ] 命名与现有端点一致（camelCase / snake_case 统一）
- [ ] 已更新 OpenAPI 文档

---

## 参考

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [fasthtml 官方上下文](https://github.com/AnswerDotAI/fasthtml)
- [Starlette mount 子应用](https://www.starlette.io/applications/#mounting-sub-applications)
- 本技能 `references/` 下 FastAPI 参考（`fastapi` 技能 / 外部依赖）