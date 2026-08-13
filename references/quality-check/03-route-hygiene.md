# products.py
from fasthtml.common import APIRouter
ar = APIRouter()

@ar("/products")              # GET  /products
def list_products(): ...

@ar("/products/{pid}")        # GET  /products/123
def product_detail(pid: int): ...

# app.py
from products import ar
ar.to_app(app)                # 把 products.py 的路由挂回主 app
# 生成指向某路由的 URL（避免手写字符串与路由定义脱节）：
A("详情", href=ar.rt_funcs['product_detail'])   # → /products/{pid} 形式
```

**路由前缀（统一前缀用 `APIRouter(prefix=...)`）**：

```python
ar = APIRouter(prefix="/api/users")

@ar("/list")   # GET /api/users/list
def list(): ...

@ar("/{uid}")  # GET /api/users/123
def get(uid: int): ...
```

**APIRouter 处理程序命名陷阱**：`APIRouter` 将其包装的处理程序函数存储在 `rt_funcs` 字典中以供发现，但字面上命名为 `get`、`post`、`put` 等的处理程序**不会暴露在该字典中**。如果需要通过 `ar.rt_funcs['handler_name']` 生成 URL：

```python
# ❌ 以下处理程序不会出现在 ar.rt_funcs 中
@ar("/users")
def get(): ...       # 字面名 get → rt_funcs 中不可见
@ar("/users")
def post(name: str): ...  # 字面名 post → rt_funcs 中不可见

# ✅ 使用语义化名称代替
@ar("/users")
def list_users(): ...     # 可被 ar.rt_funcs['list_users'] 引用
@ar("/users")
def create_user(name: str): ...  # 可被 ar.rt_funcs['create_user'] 引用
```

此陷阱与上述「函数名自动映射路由」不同——此处是**同一 path 上不同方法**的处理程序命名问题，影响的是 URL 生成而非路由匹配。

提供静态扫描脚本（不依赖运行时/浏览器），打包前运行：

```bash
python scripts/check_routes.py src/
```

分级与处置：

| 形态 | 判定 | 处置 |
|------|------|------|
| `@ar("/explicit/path")` / `@ar(f"/{pid}")` | ✅ 显式路径 | 通过 |
| `@rt` / `@ar`（无括号，如 `@rt def index()`） | ⚠️ 告警（函数名派生 `/index`，约定俗成） | 非阻断；建议显式化 `@ar("/")` |
| `@ar(prefix="/api")` 无路径 | ⚠️ 告警（路由 = prefix + 函数名） | 非阻断；建议补全路径 |
| `@ar(methods=["POST"])` 等带括号却无路径 | ❌ **阻断**（典型漏写路径） | 必须改为 `@ar("/explicit/path", methods=["POST"])` 后才能发布 |

退出码：`0` = 无阻断项（通过）；`1` = 存在阻断项（禁止发布）。

#### 4.6 前端→后端路由链路校验（运行期 404 隐患，静态门禁，P1）

`check_routes.py`（§4.5）排查的是「服务端路由未显式声明路径」；但还有一类缺陷它**看不见**：**前端组件引用了某个端点，后端却从未注册对应路由**——典型如把关闭动作挂在 `hx_get=f"/close-{modal_id}"` 上，却忘记了在 `app.py` 注册 `@rt(f"/close/{modal_id}")`。HTTP 200 冒烟只验证已知页面，UI 结构审计只看静态 HTML，都发现不了这条「死链」，直到用户真去点 × 才 404。

提供反向校验脚本（与 `check_routes.py` 方向相反、互为补充）：把「前端引用的端点集合」与「后端路由集合」做差集，命中差集即阻断。

```bash
python scripts/check_routes_linkage.py src/
```

扫描逻辑（不依赖运行时/浏览器）：
- **前端引用**：正则抽取 `hx_get=` / `hx_post=` / `href=` / `fetch(` / `requests.` 等处的 URL 字面量，模板 f-string 自动 `{{var}}`→`{}` 通配；`href="/"`、`#anchor`、外链 `http`、静态资源 `.css/.js/.svg/.ico` 跳过。
- **后端路由**：复用 `check_routes` 的路由提取器，收集显式 `@rt/@ar` 路径、`APIRouter(prefix=...)` 前缀、以及含 `Form/`/`Query()` 参数但**无显式路径**的函数（记入「自动派生」，不判缺失）。
- **判定**：前端引用 ∩ 后端路由 = 空集的端点 → 阻断（报告文件:行号）。

分级与处置：

| 形态 | 判定 | 处置 |
|------|------|------|
| 前端 `hx_get="/close-{modal_id}"` 且后端有 `@rt("/close/{id}")` | ✅ 命中 | 通过 |
| 前端 `hx_get="/close-{modal_id}"` 但后端无 `/close/...` 路由 | ❌ **阻断** | 在 `app.py` 补 `@rt(f"/close/{modal_id}")` 后才能发布 |
| `href="/"`、`#anchor`、外链、静态资源 | ⏭️ 跳过 | 不计入 |
| 模板变量 `{{modal_id}}` | 🔁 通配为 `{}` | 与后端 `{id}` 形态对齐 |

退出码：`0` = 无阻断项（通过）；`1` = 存在阻断项（禁止发布）。**打包前必跑，与 pytest 门禁同级。**

---

