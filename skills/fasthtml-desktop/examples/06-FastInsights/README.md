# FastInsights（桌面版 / Desktop）

**FastInsights** 是一个基于 [FastHTML](https://fastht.ml) 的开源商业智能（BI）工具，是 [Frappe Insights](https://github.com/frappe/insights) 核心的「服务器端 + HTMX」移植版。纯 Python、无 JS 框架：一个合成数据仓库、渲染 **Plotly** 图表的已存查询、仪表盘、SQL 实验室，以及一个 **AI 文本转 SQL** 助手。

*Ask your data anything.* 默认端口 **5008**。

> ⚠️ **仅含合成数据。** 全部数据由 `seed.py` 生成确定性合成零售销售数仓（星型模型）。

本 README 有**两个用途**：
- **用途一（给最终用户）**：怎么启动、怎么登录、数据在哪、AI 怎么配。
- **用途二（给 LLM / 开发者）**：怎么从零克隆出一模一样的桌面应用，含目录结构、入口约定、`_bootstrap_db()` 导入顺序（**FastInsights 尤为关键**）、PyInstaller 打包要点。

---

## 用途一：给最终用户（使用说明书）

### 快速开始（一键启动）

**最终用户（双击即用）**：直接**双击 `启动.bat`**，脚本会自动定位 Python、首次运行创建 `.venv` 并安装依赖、随后弹出桌面窗口。无需打开终端。

```bat
启动.bat              # 双击：自动建 .venv → 装依赖 → 生成种子数据 → 弹出桌面窗口
启动.bat server       # 可选：仅启动 HTTP 服务（无头模式，便于浏览器访问 / 调试）
```

> ⚠️ 注意：`start.py` 是**开发者命令行工具**，不是供最终用户双击的启动器——`.py` 双击默认会用编辑器打开，不会运行。用户入口统一是 **`启动.bat`**。



首次运行：① 若没有 `.venv` 则创建并 `pip install -r requirements.txt pywebview`；② 若本地无数据库自动 `seed.build()`；③ 启动服务（默认 `http://127.0.0.1:5008`）并打开桌面窗口。

### 登录凭据（默认）

- 邮箱：`admin@fastinsights.example`
- 密码：`FastInsights2026$`

可在 `.env` 中用 `FASTINSIGHTS_ADMIN_EMAIL` / `FASTINSIGHTS_ADMIN_PASSWORD` 覆盖。

### 开发者命令行（`start.py`）

> 供开发者在终端使用：质量门禁、依赖安装、无头调试。普通用户请用 `启动.bat`。



| 命令 | 说明 |
|---|---|
| `python start.py` | 桌面窗口模式（默认） |
| `python start.py --server` | 仅启动 HTTP 服务，不弹窗 |
| `python start.py --check` | 运行一键质量门禁 `dev_check.py`（进程内验证），全过退出 0 |
| `python start.py --reseed` | 删除本地数据库后重新生成种子数据 |
| `python start.py --port 8080` | 指定端口 |

### 功能模块

| 路由 | 模块 |
|---|---|
| `/` | 首页：KPI 卡片（收入、毛利、客单价、客户数）+ 两张旗舰 Plotly 图 + 仪表盘链接 |
| `/dashboards` | 仪表盘：响应式网格中的图表看板 |
| `/queries` | 查询与图表：已存 SQL 查询，各自绑定图表类型 |
| `/build` | 可视化构建器 |
| `/sql` | SQL 实验室 + Ask AI：对数仓跑**只读** SQL，或用自然语言让 AI 写 SQL |
| `/sources` | 数据源：浏览数仓表（行数 + 样本） |
| `/ai` | AI 助手（右侧栏） |
| `/guide` | 使用指引 |

**AI 文本转 SQL（亮点）**：SQL 实验室的 *Ask the data* 把你的问题 + 实时数仓 schema 发给配置的 LLM，返回一条 SQL，经 `db.run_sql()`（强制**单条只读 SELECT**，禁止 INSERT/UPDATE/DELETE/DDL）执行后渲染为图表 + 表格。模型**从不直接碰数据库**。

**AI 助手**：slash 命令 `/metrics /tables /top` **无需 API Key**；自由聊天 / 文本转 SQL 需厂商 Key。

### 数据落点

桌面运行时 SQLite 通过 `FASTINSIGHTS_DB` 重定向到 **可执行文件所在目录的 `data/fastinsights.sqlite`**（可写）。开发态默认 `fastinsights.sqlite`。重置：`python start.py --reseed`。

### AI（自由聊天 / 文本转 SQL）配置

```ini
MODEL_PROVIDER=xai          # xai | openai | anthropic | google
MODEL_NAME=grok-4-1-fast-reasoning
XAI_API_KEY=...             # 或 OPENAI_API_KEY / ANTHROPIC_API_KEY / GOOGLE_API_KEY
```

无 Key 时，仪表盘、已存查询、SQL 实验室、slash 命令均可用，仅 AI 生成（文本转 SQL、自由聊天）禁用。

---

## 用途二：给 LLM / 开发者（克隆说明书）

### 目录树

```
06-FastInsights/
├── web_app.py        # 路由、鉴权、SQL 执行 + AI-SQL 端点、SSE 聊天、boot（serve(port=PORT)）
├── db.py             # 数仓 + 应用 schema，只读 run_sql() 守卫；DB_PATH = getenv("FASTINSIGHTS_DB")
├── seed.py           # 确定性合成零售星型模型 + 已存查询/图表/仪表盘
├── main.py           # 桌面入口（pywebview + uvicorn）
├── start.py          # 一键脚本：建 venv / 装依赖 / 启动 / --check / --reseed
├── dev_check.py      # 进程内 TestClient 质量门禁
├── requirements.txt  # python-fasthtml>=0.12.0, fastapi>=0.115, uvicorn>=0.30, httpx>=0.27, python-dotenv>=1.0
├── web/
│   ├── layout.py / views.py / ai.py / charts.py / suite_auth.py / api_core.py / api.py / account_auth.py / google_auth.py / developer.py / landing.py
│   └── static/
├── static/  docs/  scripts/  Dockerfile  docker-compose.yml  .env.sample  SKILLS.md  swagger.json
└── data/             # 运行时数据库（桌面态落点，**勿打包进 EXE**）
```

> 克隆时只保留源码，排除 `.venv/`、`data/`、根目录已生成的 `fastinsights.sqlite`。

### 入口与端口

- **服务入口**：`web_app.py` 末尾 `serve(port=PORT, reload=os.getenv("FASTINSIGHTS_RELOAD","0")=="1")`；`PORT = int(os.getenv("FASTINSIGHTS_PORT", "5008"))`。
- **桌面入口**：`main.py` 计算 `RESOURCE_DIR = Path(sys._MEIPASS)`、`DATA_DIR = exe父目录/"data"`，`os.environ.setdefault("FASTINSIGHTS_DB", str(DATA_DIR/"fastinsights.sqlite"))`，`os.chdir(RESOURCE_DIR)`，`find_free_port(5008)`，`wait_for_server(...)`，`webview.create_window("FastInsights", url, width=1280, height=840)`。`SERVER_ONLY=1` 无头模式。

### 数据库约定（`db.py`）

```python
DB_PATH = os.getenv("FASTINSIGHTS_DB") or str(Path(__file__).parent / "fastinsights.sqlite")
```

### 合成数据播种与导入顺序（**最关键**）

> FastInsights 的 `web/api.py` 在 **import 期**即 `SQLiteBackend(..., initialize=db.init_app_schema)`，要求数仓表（`wh_orders` 等）**已存在**。因此**必须在 `import web_app` 之前先 `seed.build()`**，否则直接 ImportError。上游 `Dockerfile` 的 CMD 也是「先 seed 再启动」，印证此顺序。

`main.py` / `start.py` / `dev_check.py` 都内置 `_bootstrap_db()`：

```python
def _bootstrap_db():
    import db
    if not db.db_exists():
        import seed
        seed.build()
```

**务必「先 seed 再 import web_app」。**

### 三件套机制

- **`main.py`**：EXE 入口，`os.chdir(RESOURCE_DIR)` 后 `import web_app`，`uvicorn.Server(Config(web_app.app, host="127.0.0.1", port=port, reload=False))` 起服务，再 pywebview 开窗口。
- **`start.py`**：`ensure_env()` 幂等建 venv 并装依赖；`start()` 调 `_bootstrap_db()`；`--check`/`--reseed`/`--port` 见上。
- **`dev_check.py`**：`TestClient(web_app.app)` 进程内验证：未登录 `/`→非 500、登录流、业务路由 `/dashboards /queries /build /sql /sources /ai /guide`→200、`/swagger.json`→合法 JSON、静态资源→200。全过打印 `[GATE] 全部通过，可交付/可打包`。

### 打包为 EXE（PyInstaller 要点）

扁平布局（同 03）：仓库根即冻结态 `RESOURCE_DIR = Path(sys._MEIPASS)`（无 `app/`）。推荐用技能级构建驱动：

```bash
python scripts/build_fast_example.py \
  --project-dir examples/06-FastInsights --app-name FastInsights --port 5008
```

等效手动命令（最小构建 venv，在 `examples/06-FastInsights/` 内）：

```bash
pyinstaller main.py --onefile --noupx --console \
  --name FastInsights \
  --collect-submodules fasthtml --collect-submodules sqlite3 --collect-data certifi \
  --hidden-import clr \
  --hidden-import webview.platforms.winforms --hidden-import webview.platforms.edgechromium \
  --hidden-import _sqlite3 --hidden-import fastapi --hidden-import starlette \
  --hidden-import pydantic --hidden-import python_multipart \
  --additional-hooks-dir scripts/pyinstaller_hooks \
  --add-data "webview/lib;webview/lib" \
  --add-data "static;static" --add-data "web/static;web/static" --add-data "swagger.json;."
```

要点：
1. **项目模块自动收集**：`web_app.py` `db.py` `seed.py` `web/` 经 `import web_app` 自动收入冻结包，无需 `--add-data`。
2. **sqlite3**：须用 `scripts/pyinstaller_hooks/hook-sqlite3.py`（`--additional-hooks-dir`）收集 `_sqlite3.pyd` / `sqlite3.dll`；DB 走 `FASTINSIGHTS_DB` 重定向到可写 `data/`。
3. **pywebview**：`clr` + `webview.platforms.winforms` + `webview.platforms.edgechromium` + `webview/lib` 必须。
4. **图表渲染（无 Python 依赖）**：FastInsights 图表走**浏览器端 Plotly.js**（CDN `cdn.plot.ly` 加载，见 `web/layout.py`），服务端仅生成 Plotly spec，**不依赖 Python `plotly` 包**——打包时**无需** `plotly` hidden-import 或 `--collect-submodules plotly`。
5. **冒烟**：启动 EXE 验证 `http://127.0.0.1:5008/` 返回 200 且窗口句柄存在；图表由浏览器端 JS 渲染，无需额外打包。

### 环境变量完整清单

| 变量 | 默认 | 说明 |
|---|---|---|
| `FASTINSIGHTS_DB` | `fastinsights.sqlite` | SQLite 路径（桌面态重定向到 `data/`） |
| `FASTINSIGHTS_PORT` | `5008` | 服务端口 |
| `FASTINSIGHTS_ADMIN_EMAIL` | `admin@fastinsights.example` | 登录邮箱 |
| `FASTINSIGHTS_ADMIN_PASSWORD` | `FastInsights2026$` | 登录密码 |
| `FASTINSIGHTS_SECRET` | 随机 | 会话签名密钥 |
| `FASTINSIGHTS_ENV_LABEL` | `FastInsights` | UI 标签 |
| `FASTINSIGHTS_RELOAD` | `0` | 开发热重载 |
| `MODEL_PROVIDER` | `xai` | xai / openai / anthropic / google |
| `MODEL_NAME` | `grok-4-1-fast-reasoning` | 模型名 |
| `XAI_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` | 空 | 对应厂商 Key |

---

## 许可

MIT。属于 [`fasthtml-oss-migrations`](https://github.com/predictivelabsai/fasthtml-oss-migrations) 计划。
