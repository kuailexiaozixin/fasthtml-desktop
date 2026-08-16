# FastCRM（桌面版 / Desktop）

**FastCRM** 是一个基于 [FastHTML](https://fastht.ml) 的开源销售 CRM，是 [Frappe CRM](https://github.com/frappe/crm) 核心的「服务器端 + HTMX」移植版。纯 Python、无 JS 框架：线索、看板式交易管道、联系人、组织、任务、活动流，以及基于实时数据的 AI 助手。

*Simplify sales, amplify relationships.* 默认端口 **5006**。

> ⚠️ **仅含合成数据，无真实 PII。** 全部数据由 `seed.py` 生成确定性合成数据，仓库内不存在真实人物或公司。

本 README 有**两个用途**：
- **用途一（给最终用户）**：怎么启动、怎么登录、数据在哪、AI 怎么配。
- **用途二（给 LLM / 开发者）**：怎么从零克隆出一模一样的桌面应用，含目录结构、入口约定、`_bootstrap_db()` 导入顺序、PyInstaller 打包要点。

---

## 用途一：给最终用户（使用说明书）

### 快速开始（一键启动）

**最终用户（双击即用）**：直接**双击 `启动.bat`**，脚本会自动定位 Python、首次运行创建 `.venv` 并安装依赖、随后弹出桌面窗口。无需打开终端。

```bat
启动.bat              # 双击：自动建 .venv → 装依赖 → 生成种子数据 → 弹出桌面窗口
启动.bat server       # 可选：仅启动 HTTP 服务（无头模式，便于浏览器访问 / 调试）
```

> ⚠️ 注意：`start.py` 是**开发者命令行工具**（见下），不是供最终用户双击的启动器——`.py` 双击默认会用编辑器打开，不会运行。用户入口统一是 **`启动.bat`**。

首次运行会依次：
1. 若没有 `.venv`，则创建并 `pip install -r requirements.txt pywebview`；
2. 若本地没有数据库，自动运行 `seed.py` 生成合成数据；
3. 启动 FastHTML 服务（默认 `http://127.0.0.1:5006`）并通过 pywebview 打开桌面窗口。

### 登录凭据（默认）

- 邮箱：`admin@fastcrm.example`
- 密码：`FastCRM2026$`

可在 `.env` 中用 `FASTCRM_ADMIN_EMAIL` / `FASTCRM_ADMIN_PASSWORD` 覆盖。

### 开发者命令行（`start.py`）

> 供开发者在终端使用：质量门禁、依赖安装、无头调试。普通用户请用 `启动.bat`。

| 命令 | 说明 |
|---|---|
| `python start.py` | 桌面窗口模式（默认） |
| `python start.py --server` | 仅启动 HTTP 服务，不弹窗（便于调试 / 浏览器访问） |
| `python start.py --check` | 运行一键质量门禁 `dev_check.py`（进程内验证，不占端口、不弹窗），全过退出 0 |
| `python start.py --reseed` | 删除本地数据库后重新生成种子数据 |
| `python start.py --port 8080` | 指定端口 |

### 功能模块

| 路由 | 模块 |
|---|---|
| `/` | 仪表盘：KPI 卡片、管道漏斗、Top 交易、活动流 |
| `/deals` | 交易：七阶段看板（Qualification → … → Won / Lost） |
| `/leads` | 线索：状态分段、可搜索 |
| `/tasks` | 任务：跨交易待办 |
| `/contacts` | 联系人目录 |
| `/organizations` | 组织（公司）目录，按成交额排名 |
| `/ai` | AI 助手（右侧栏，基于实时数据快照） |
| `/guide` | 使用指引 |

**AI 助手**：slash 命令 `/pipeline /deals /leads /tasks /kpi /org <name> /help` **无需 API Key** 即可用；自由聊天需配置厂商 Key（见下）。

### 数据落点

桌面运行时，SQLite 通过环境变量 `FASTCRM_DB` 重定向到 **可执行文件所在目录的 `data/fastcrm.sqlite`**（可写）。开发态默认落在仓库根的 `fastcrm.sqlite`。重置数据：`python start.py --reseed`，或手动删除该文件。

### AI（自由聊天）配置

自由聊天需要任一厂商 Key；slash 命令免 Key 即可用。在 `.env` 配置：

```ini
MODEL_PROVIDER=xai          # xai | openai | anthropic | google
MODEL_NAME=grok-4-1-fast-reasoning
XAI_API_KEY=...             # 或 OPENAI_API_KEY / ANTHROPIC_API_KEY / GOOGLE_API_KEY
```

无 Key 时，整个应用与 slash 命令仍可用，仅自由聊天不可用。

### 常见问题

- **端口被占用？** 用 `--port` 指定其他端口，或设置 `FASTCRM_PORT`。
- **想用浏览器而非桌面窗口？** `python start.py --server` 后用浏览器打开提示的地址。
- **数据怎么清掉重来？** `python start.py --reseed`。

---

## 用途二：给 LLM / 开发者（克隆说明书）

### 目录树

```
03-FastCRM/
├── web_app.py        # 路由、鉴权、SSE 聊天端点、boot（serve(port=PORT)）
├── db.py             # SQLite schema + 领域词表 + 读取 helper；DB_PATH = getenv("FASTCRM_DB")
├── seed.py           # 确定性合成数据生成器
├── main.py           # 桌面入口（pywebview + uvicorn 子进程）
├── start.py          # 一键脚本：建 venv / 装依赖 / 启动 / --check / --reseed
├── dev_check.py      # 进程内 TestClient 质量门禁
├── requirements.txt  # python-fasthtml>=0.12.0, fastapi>=0.115, uvicorn>=0.30, httpx>=0.27, python-dotenv>=1.0
├── web/
│   ├── layout.py       # 三栏外壳、CSS 设计变量、聊天 JS
│   ├── views.py        # 页面渲染器
│   ├── ai.py           # slash 命令 + 多厂商流式聊天（MODEL_PROVIDER/MODEL_NAME/XAI_API_KEY...）
│   ├── api.py / api_core.py / account_auth.py / google_auth.py / developer.py / landing.py
│   └── static/
├── static/           # favicon 等静态资源
├── docs/             # ROADMAP、demo GIF
├── scripts/          # build_demo_gif.sh, frappe_doctype_to_schema.py, coolify.py
├── Dockerfile / docker-compose.yml / .env.sample / SKILLS.md / FastHTML.md / swagger.json
└── data/             # 运行时数据库（桌面态落点，**勿打包进 EXE**）
```

> 克隆时只保留源码（`web_app.py` `db.py` `seed.py` `web/` `static/` `requirements.txt` 等），排除 `.venv/`、`data/`、以及根目录已生成的 `fastcrm.sqlite`。

### 入口与端口

- **服务入口**：`web_app.py` 末尾 `serve(port=PORT, reload=os.getenv("FASTCRM_RELOAD","0")=="1")`；`PORT = int(os.getenv("FASTCRM_PORT", "5006"))`。
- **桌面入口**：`main.py` 计算 `RESOURCE_DIR = Path(sys._MEIPASS)`（只读）、`DATA_DIR = Path(sys.executable).parent/"data"`（可写），`os.environ.setdefault("FASTCRM_DB", str(DATA_DIR/"fastcrm.sqlite"))`，`os.chdir(RESOURCE_DIR)`，`find_free_port(5006)`，`wait_for_server(...)` 后用 `webview.create_window("FastCRM", url, width=1280, height=840)`。`SERVER_ONLY=1` 时为无头模式。

### 数据库约定（`db.py`）

```python
DB_PATH = os.getenv("FASTCRM_DB") or str(Path(__file__).parent / "fastcrm.sqlite")
```

未设置 `FASTCRM_DB` 时落到仓库根 `fastcrm.sqlite`；桌面态由 `main.py` 重定向到可写目录。

### 合成数据播种与导入顺序（关键）

- `web_app.py` 启动时会调用 `_ensure_db()`（或等价逻辑）自动 `seed.build()` 生成确定性数据。
- **`main.py` / `start.py` / `dev_check.py` 都内置 `_bootstrap_db()`**：在 `import web_app` **之前**先执行：

  ```python
  def _bootstrap_db():
      import db
      if not db.db_exists():
          print("[INFO] 首次启动：正在生成合成种子数据...")
          import seed
          seed.build()
  ```

  原因：应用在 import 期就依赖表已存在（FastInsights 尤甚，`web/api.py` 在 import 期即 `SQLiteBackend(..., initialize=db.init_app_schema)`，要求仓库表已存在）。**务必「先 seed 再 import web_app」，否则 ImportError / 表不存在。**

### 三件套机制

- **`main.py`**：打包后的 EXE 入口。`sys._MEIPASS` 指向解压目录，`os.chdir(RESOURCE_DIR)` 后 `import web_app`，用 `uvicorn.Server(uvicorn.Config(web_app.app, host="127.0.0.1", port=port, reload=False))` 起服务，再 pywebview 开窗口。
- **`start.py`**：`ensure_env()` 幂等建 `.venv` 并装依赖；`start()` 调 `_bootstrap_db()` 后选桌面/无头模式；`--check` 调 `dev_check.py`；`--reseed` 删 `DATA_DIR/*.sqlite` 后重建。
- **`dev_check.py`**：用 `fastapi.testclient.TestClient(web_app.app)` 进程内验证：未登录 `/`→非 500、登录流、各业务路由 `/leads /deals /tasks /contacts /organizations /ai /guide`→200、`/swagger.json`→合法 JSON、静态资源 `/static/favicon.svg`→200。全过打印 `[GATE] 全部通过，可交付/可打包`。

### 打包为 EXE（PyInstaller 要点）

本示例为**扁平布局**：`main.py` / `web_app.py` / `db.py` / `seed.py` / `web/` / `static/` / `swagger.json` 全在仓库根；冻结态资源目录 `RESOURCE_DIR = Path(sys._MEIPASS)`（顶层，**无 `app/` 子目录**）。推荐用技能级构建驱动（已固化下方全部参数与 sqlite3 hook）：

```bash
# 在技能根目录执行（脚本自动定位 hook-sqlite3 与 webview/lib）
python scripts/build_fast_example.py \
  --project-dir examples/03-FastCRM --app-name FastCRM --port 5006
```

等效的手动 PyInstaller 命令（在 `examples/03-FastCRM/` 内执行，pyinstaller 须装在**最小构建 venv**）：

```bash
pyinstaller main.py --onefile --noupx --console \
  --name FastCRM \
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
1. **项目模块自动收集**：`web_app.py` `db.py` `seed.py` `web/` 经 `main.py` 的 `import web_app` 静态分析自动收入冻结包，**无需** `--add-data` 它们；只需把「按 cwd 读取的数据文件」拷进 `_MEIPASS` 顶层（`static` / `web/static` / `swagger.json`）。
2. **sqlite3**：标准库但 `_sqlite3` 扩展在 Windows venv 下不自动复制二进制，须用 `scripts/pyinstaller_hooks/hook-sqlite3.py`（经 `--additional-hooks-dir` 注入）收集 `_sqlite3.pyd` / `sqlite3.dll`。DB 走 `FASTCRM_DB` 重定向到可写 `data/`，**绝不把可写 DB 打进只读 `MEIPASS`**。
3. **pywebview**：`clr` + `webview.platforms.winforms` + `webview.platforms.edgechromium` 必须 hidden-import（Windows WebView2）；`webview/lib`（WebView2 加载器）须 `--add-data` 拷入。
4. **冒烟**：打包后启动 EXE，验证 `http://127.0.0.1:5006/` 返回 200 且窗口句柄存在，再交付。技能脚本默认 `SERVER_ONLY=1` 无头模式轮询健康端点防假绿。

### 环境变量完整清单

| 变量 | 默认 | 说明 |
|---|---|---|
| `FASTCRM_DB` | `fastcrm.sqlite` | SQLite 路径（桌面态重定向到 `data/`） |
| `FASTCRM_PORT` | `5006` | 服务端口 |
| `FASTCRM_ADMIN_EMAIL` | `admin@fastcrm.example` | 登录邮箱 |
| `FASTCRM_ADMIN_PASSWORD` | `FastCRM2026$` | 登录密码 |
| `FASTCRM_SECRET` | 随机 | 会话签名密钥 |
| `FASTCRM_ENV_LABEL` | `FastCRM` | UI 标签 |
| `FASTCRM_RELOAD` | `0` | 开发热重载 |
| `MODEL_PROVIDER` | `xai` | xai / openai / anthropic / google |
| `MODEL_NAME` | `grok-4-1-fast-reasoning` | 模型名 |
| `XAI_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` | 空 | 对应厂商 Key |

---

## 许可

MIT。属于 [`fasthtml-oss-migrations`](https://github.com/predictivelabsai/fasthtml-oss-migrations) 计划（将 Frappe 应用移植到 FastHTML）。
