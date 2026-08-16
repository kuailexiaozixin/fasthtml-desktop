# FastHTML Handler 签名与参数绑定

> 在 `fasthtml-desktop` 工作流的 ⑥ 编码步骤中使用。本文档系统化 FastHTML 的参数绑定规则，防止 AI 写出签名错误导致静默失效的处理函数。

**权威源**：`fasthtml-refs/fasthtml-llms-ctx.txt`（本文所有规则均以该文件为准，不含外部技能私货）。

---

## 一、绑定顺序（binding order）

FastHTML 在运行时按以下优先级从前到后查找参数来源：

```
path params → query params → cookies → headers → session keys → form/JSON body
```

直到命中第一个匹配项。若全部未命中且参数无默认值，返回 HTTP 400。

**要点**：
- 查询参数在 cookies/headers **之前**检索，不要误以为 cookie 覆盖 query
- `session` 特殊参数名会拦截 session 查找（见 §三），普通业务参数不受影响
- 表单字段名与参数名**严格匹配**（区分大小写）
- **路径参数与查询参数同名时，路径参数优先**：例如路由 `@rt("/item/{id}") def get(id: str, q: str)` 且请求 `/item/42?q=xyz&id=99`，`id` 取路径的 `42` 而非查询的 `99`（按绑定顺序 `path → query`）。如需同时拿到两者，应改名（如 `path_id` / `query_id`）或用 `req` 直接读 `request.query_params`。

---

## 二、方法选择（@rt 语义）

这是 AI 最常见的误用场景之一。`@rt` 的行为取决于是否传 path 参数：

| 写法 | 路由 | 允许的 HTTP 方法 |
|------|------|-----------------|
| `@rt`（无参数） | 函数名自动映射（下划线→连字符），`index` 映射到 `/` | GET + POST 均可用 |
| `@rt("/path") def get(...)` | `/path` | 仅 GET |
| `@rt("/path") def post(...)` | `/path` | 仅 POST |
| `@app.get("/path")` | `/path` | 仅 GET（最明确写法） |
| `@app.post("/path")` | `/path` | 仅 POST（最明确写法） |

**关键规则**：
- 不带 path 时，函数名 `get`/`post` **不等于**方法限定——它只是路由名 `/get` 或 `/post`
- 需要同一 path 的不同方法 → 显式传 path + 函数名或 `@app.get`/`@app.post`
- 默认新代码使用 GET + POST；旧代码中 `PUT`/`DELETE` 的保留遵循既有风格

---

## 三、特殊参数名（已标注参数除外）

以下参数名被 FastHTML 识别为**框架注入对象**，**不需要**（也不应该）加类型注解，FastHTML 不尝试对其做类型转换：

| 参数名 | 来源 | 类型 |
|--------|------|------|
| `req` / `request` | Starlette Request | `Request` |
| `sess` / `session` | Session dict | `dict` |
| `htmx` | HTMX 请求头 | `HtmxHeaders` |
| `app` | 当前 FastHTML app | `FastHTML` |
| `auth` | `scope['auth']` | 自定义 |
| `scope` | ASGI scope | `dict` |
| `data` | 解析后的请求体数据 | - |
| `state` | `scope['state']` | - |
| `body` | 原始请求体 | - |

**反例**（错误）：
```python
@rt
def save(req: Request, name: str): ...  # ❌ req 不应加 Request 注解
```

**正确**：
```python
@rt
def save(req, name: str): ...  # ✅ req 无注解，FastHTML 自动注入
```

---

## 四、结构化请求体类型

以下类型会被 FastHTML 识别为**结构体绑定**——自动从表单/JSON body 提取匹配字段并构造实例：

| 类型 | 行为 |
|------|------|
| `dataclass` | 从表单字段中匹配构造 |
| fastlite 生成的 flexiclass | 同 dataclass（flexiclass 是其子类） |
| `TypedDict` | 用字段注解做类型转换 |
| `namedtuple` | 从表单字段匹配 |
| 带类型注解的自定义类 | 尝试匹配字段构造 |
| 实现了 `__from_request__` 的类 | 调用该工厂方法 |

**反例**（错误）：
```python
@rt
def save(data: dict): ...  # ❌ dict 捕获全部 body 但值保留为字符串，不做类型转换
@rt
def save(ids: list): ...   # ❌ 裸 list 被忽略，应使用 list[int]
```

**正确**：
```python
from dataclasses import dataclass

@dataclass
class LoginForm:
    name: str
    pwd: str

@rt
def login(form: LoginForm): ...  # ✅ 自动从表单构造 LoginForm 实例

@rt
def toggle(ids: list[int]): ...  # ✅ list[int] 会收集同名多值并转换为 int
```

**注意**：表单字段名必须与 dataclass/TypedDict 的字段名**完全一致**。

---

## 五、route function 引用（避免手写字符串 URL）

被 `@rt` 装饰后的函数本身是一个**可调用的 route-function wrapper**，支持：
- `handler` — 作为 `href`/`action`/`hx_get`/`hx_post` 的值直接传入
- `handler.to(...)` — 构造带查询参数的 URL
- `index` 自动映射到 `/`

```python
@rt
def profile(email: str): ...

# ✅ 用 handler 引用
Form(action=profile)(...)
Button("Open", hx_get=profile.to(email="a@example.com"))

# ❌ 手写字符串
Form(action="/profile")(...)
```

---

## 六、常见签名错误与诊断

| 症状 | 可能原因 | 检查 |
|------|---------|------|
| handler 参数始终为 None | 缺少类型注解，FastHTML 忽略该参数 | 逐一检查所有未标注参数是否为 §三 的特殊名 |
| 表单数据收不到 | 字段名与 handler 参数名不匹配 | 确认 `Input(name=...)` 与 handler 参数名一致 |
| list 参数不工作 | 用了裸 `list` 而非 `list[T]` | 改为 `list[int]` 等带类型参数的形式 |
| 路由 404 | 函数名映射与手写 href 不匹配 | 优先用 handler 引用替代字符串 URL；多文件用显式 `@ar("/path")` |
| `@rt` 没限定方法 | 误以为 `def get()/post()` 是方法限定 | 见 §二——不带 path 时函数名只是路由名 |

---

## 七、async 处理函数：禁止在事件循环里做阻塞调用

FastHTML 处理函数可写成 `def`（同步）或 `async def`（异步）。二者在 ASGI 运行时的调度完全不同，用错会**卡死整个应用**：

| 处理函数写法 | 运行位置 | 阻塞操作（`time.sleep`/同步 `requests`/`subprocess.wait`）的后果 |
|------------|---------|--------------------------------------------------|
| `def foo(...)`（同步） | Starlette 自动丢**线程池**执行 | 只占用一个工作线程，不影响其它请求 |
| `async def foo(...)`（异步） | 直接在**事件循环**上执行 | 阻塞期间**整个进程**无法处理任何其它请求，所有并发请求全部挂起 |

**真实事故（本技能实战复盘）**：一个 `async def` 保存处理函数里直接调用了内部的 `restart_gateway()`，而该函数内部有 `time.sleep()` 轮询（最长约 46s）。结果：本次 POST 迟迟不返回，且**期间前端发出的所有 GET 全部空响应/超时**——表现为「保存后页面卡死、数据读不出来」，极易误判为业务 bug。

**规则**：
- 在 `async def` 处理函数里，凡是**同步阻塞**调用（`time.sleep`、同步 HTTP 客户端、`subprocess` 等待、重 CPU 循环），必须丢线程池：
  ```python
  from starlette.concurrency import run_in_threadpool

  @rt("/save", methods=["POST"])
  async def save(req):
      body = await req.json()          # 异步 IO 用 await
      ok = await run_in_threadpool(blocking_fn)   # ✅ 阻塞调用丢线程池，不卡事件循环
      return JSONResponse({"ok": ok})
  ```
- 若处理函数**没有**任何 `await` 需求（不读异步 body、不调异步库），直接写成同步 `def`：Starlette 会自动把它放线程池，反而更省心。
- 判据：**能同步就同步；一旦 `async def`，函数体内不得出现裸的阻塞调用。**

**并发拉取的正确姿势（同步处理函数内）**：同步 `def` 处理函数已在线程池中，若需并发多个阻塞请求（如同时拉多个后端发现接口），可在其内部再开 `ThreadPoolExecutor` 并发，把「串行求和」降为「取最大」：
```python
from concurrent.futures import ThreadPoolExecutor

@ar("/api/hub/data", methods=["GET"])
def hub_data():                       # 同步 def：本身已在线程池
    with ThreadPoolExecutor(max_workers=4) as ex:
        fs = [ex.submit(blocking_get, p) for p in paths]
        results = [f.result() for f in fs]
    ...
```

> 注意：若某个后端接口**自身**就慢且无缓存（例如每次实时探测），并发也只能降到「单接口耗时」。此时应在**应用侧**加短 TTL 缓存（在写操作后显式失效），避免每次打开页面都付一次慢接口的钱——这属于应用逻辑，不在本表范围。

---

## 八、与 fasthtml-desktop 工作流的衔接

- ⑥ 编码：写完处理函数后，对照 §三 检查未注解参数、§四 检查结构体类型是否正确、§五 检查是否用 handler 引用替代了字符串 URL、§七 检查 `async def` 里有无裸阻塞调用
- ⑦ 运行验证：`uv run pytest` 会捕获签名错导致的 400 错误
- quality-check/02-ui-audit.md §4.5：多文件路由的 APIRouter 相关陷阱（函数名→路由映射 + get/post 命名陷阱）
