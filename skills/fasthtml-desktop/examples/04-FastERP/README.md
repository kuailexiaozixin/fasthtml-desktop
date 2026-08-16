# FastERP（桌面版 / Desktop）

**FastERP** 是一个基于 [FastHTML](https://fastht.ml) 的开源 ERP，是 [ERPNext](https://github.com/frappe/erpnext) 的「服务器端 + HTMX」移植版，带一套 Intuit 风格、自包含的会计工作区。覆盖 **Order-to-Cash、Procure-to-Stock、库存与会计**，全部使用确定性合成数据。纯 Python、无 JS 框架，并带一个基于实时演示公司数据的 AI 助手。

*Sell, ship, invoice, get paid.* 默认端口 **5011**（集成 API `api_app.py` 在 **5012**）。

> ⚠️ **仅含合成数据。** 全部数据由 `seed.py` 生成确定性合成数据，属于演示性会计软件，**非** QuickBooks/Intuit 集成，也**非**生产记账系统。默认以 SQLite 运行；上游的 PostgreSQL + SAP 迁移能力保留（见「数据库约定」）。

> 本示例为上游 [predictivelabsai/FastERP](https://github.com/predictivelabsai/FastERP) **完整版**克隆（含 `fasterp` 业务包 + `migration/` + `migrations/` SAP 迁移模块），并做了三类本地必要适配：**SQLite 化**、**修复注册登录（离线免邮件验证）**、**移除大体积文档/媒体**。合规见 `../../THIRD_PARTY_NOTICES.md`。

本 README 有**两个用途**：
- **用途一（给最终用户）**：怎么启动、怎么登录、数据在哪、AI 怎么配。
- **用途二（给 LLM / 开发者）**：怎么从零克隆出一模一样的桌面应用，含目录结构、入口约定、`_ensure_db()` 导入顺序、PyInstaller 打包要点。

---

## 用途一：给最终用户（使用说明书）

### 快速开始（一键启动）

**最终用户（双击即用）**：直接**双击 `启动.bat`**，脚本会自动定位 Python、预检/安装依赖、首次运行自动建库播种，随后弹出桌面窗口。无需打开终端。

```bat
启动.bat              # 双击：自动预检/装依赖 → 建库播种 → 弹出桌面窗口
启动.bat server       # 可选：仅启动 HTTP 服务（无头模式，便于浏览器访问 / 调试）
```

> ⚠️ 注意：`start.py` 是**开发者命令行工具**，不是供最终用户双击的启动器——`.py` 双击默认会用编辑器打开，不会运行。用户入口统一是 **`启动.bat`**。

首次运行：① `launcher.py` 预检 `requirements.txt` 依赖（缺失自动装）；② `import web_app` 时顶层 `_ensure_db()` 自动建库并播种合成数据；③ 启动服务（默认 `http://127.0.0.1:5011`）并打开桌面窗口。

### 登录凭据（默认）

- 邮箱：`admin@fasterp.example`
- 密码：`FastERP2026$`

可在 `.env` 中用 `FASTERP_ADMIN_EMAIL` / `FASTERP_ADMIN_PASSWORD` 覆盖。

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
| `/` | 仪表盘：已收收入、应收（含逾期）、库存价值、低库存；销售订单状态、AR 账龄、月度开票、低库存项 |
| `/orders` | 销售订单：按状态筛选，展开行项目、合计、关联发票 |
| `/invoices` | 应收账款（AR）：未付/部分付/已付/**逾期** |
| `/items` | 物料与库存：分组、库存水平、价值、**补货标记** |
| `/customers` | 客户：按应收余额排名 |
| `/suppliers` `/purchase` | 采购：供应商、多行采购订单、收货、入库、应付账款 |
| `/accounting` | 会计：财务 KPI、22 科目表、分类费用、平衡手工日记账、可筛选总账 |
| `/accounting/reports` | 报表：损益、资产负债表、试算平衡、销售税汇总 |
| `/ai` | AI 助手（右侧栏） |
| `/guide` | 使用指引 |

**AI 助手**：slash 命令 `/sales /ar /stock /top /buying /gl` **无需 API Key**；自由聊天需厂商 Key。

> 可选集成 API：`python -m uvicorn api_app:app --port 5012` 打开 `http://localhost:5012/docs`（FastAPI + Swagger，只读桩）。

### 数据落点

桌面运行时 SQLite 通过 `FASTERP_DB` 重定向到 **可执行文件所在目录的 `data/fasterp.sqlite`**（可写）。开发态默认 `fasterp.sqlite`。重置：`python start.py --reseed`。

### AI（自由聊天）配置

```ini
MODEL_PROVIDER=xai          # xai | openai | anthropic | google
MODEL_NAME=grok-4-1-fast-reasoning
XAI_API_KEY=...             # 或 OPENAI_API_KEY / ANTHROPIC_API_KEY / GOOGLE_API_KEY
```

无 Key 时应用与 slash 命令仍可用，仅自由聊天不可用。

### 测试

```bash
python -m pytest -q        # accounting 与 API 不变量测试（tests/）
```

---

## 用途二：给 LLM / 开发者（克隆说明书）

### 目录树

```
04-FastERP/
├── web_app.py        # FastHTML 路由、鉴权、SSE 聊天、boot（顶层 _ensure_db() + serve(port=PORT)）
├── api_app.py        # FastAPI 集成桩 + OpenAPI/Swagger（端口 5012）
├── db.py             # 数据门面：SQLite 默认 / PostgreSQL 可选（DB_URL）
├── seed.py           # 确定性合成：客户、物料、订单、发票、库存（SQLite 模式）
├── main.py           # 桌面入口（pywebview + uvicorn）
├── start.py          # 一键脚本：建 venv / 装依赖 / 启动 / --check / --reseed
├── dev_check.py      # 进程内 TestClient 质量门禁
├── fasterp/          # 上游业务包（config / database / 域模块；PostgreSQL 运行时）
├── migration/        # 迁移生成器 / 工具
├── migrations/       # SAP 迁移 SQL（migrations/postgres/*.sql）
├── requirements.txt  # python-fasthtml>=0.12.0, fastapi>=0.115, uvicorn>=0.30, httpx>=0.27, python-dotenv>=1.0, psycopg[binary]>=3.2, psycopg-pool>=3.2
├── web/
│   ├── layout.py / views.py / accounting.py / ai.py / api_core.py / api.py / account_auth.py / google_auth.py / developer.py / landing.py / seo.py
│   └── static/
├── static/  docs/  scripts/  tests/  Dockerfile  docker-compose.yml  .env.sample  SKILLS.md  swagger.json
└── data/             # 运行时数据库（桌面态落点，**勿打包进 EXE**）
```

> 克隆时只保留源码，排除 `.venv/`、`data/`、根目录已生成的 `fasterp.sqlite`。

### 入口与端口

- **服务入口**：`web_app.py` 末尾 `serve(port=PORT, reload=os.getenv("FASTERP_RELOAD","0")=="1")`；`PORT = int(os.getenv("FASTERP_PORT", "5011"))`。
- **桌面入口**：`main.py` 计算 `RESOURCE_DIR = Path(sys._MEIPASS)`、`DATA_DIR = exe父目录/"data"`，`os.environ.setdefault("FASTERP_DB", str(DATA_DIR/"fasterp.sqlite"))`，`os.chdir(RESOURCE_DIR)`，`find_free_port(5011)`，`wait_for_server(...)`，`webview.create_window("FastERP", url, width=1280, height=840)`。`SERVER_ONLY=1` 无头模式。

### 数据库约定（`db.py`）

```python
DB_PATH = os.getenv("FASTERP_DB") or str(Path(__file__).parent / "fasterp.sqlite")
USE_POSTGRES = bool(os.getenv("DB_URL"))
```

默认 SQLite 离线运行；设置 `DB_URL` 后切换 PostgreSQL 运行时（需先 `scripts/seed_postgres.py` 建种子，且迁移来自 `migrations/postgres/`）。

### 建库播种与导入顺序（关键）

`web_app.py` 在**顶层**调用 `_ensure_db()`（import 即触发）：SQLite 模式下自动 `init_schema()` + 无库时 `seed.build()`。因此 `main.py` / `start.py` / `dev_check.py` **无需**额外的 `_bootstrap_db()`，只需在设置好 `FASTERP_DB` 环境变量后 `import web_app`：

```python
import os
os.environ.setdefault("FASTERP_DB", str(DATA_DIR / "fasterp.sqlite"))
import web_app   # 触发顶层 _ensure_db()：建库 + 播种
```

**务必「先设 `FASTERP_DB`，再 `import web_app`」。**

### 三件套机制

- **`main.py`**：EXE 入口，`os.chdir(RESOURCE_DIR)` 后 `import web_app`，`uvicorn.Server(Config(web_app.app, host="127.0.0.1", port=port, reload=False))` 起服务，再 pywebview 开窗口。
- **`start.py`**：`ensure_env()` 幂等建 venv 并装依赖；`start()` 设 `FASTERP_DB` 后 `import web_app`；`--check`/`--reseed`/`--port` 见上。
- **`dev_check.py`**：`TestClient(web_app.app)` 进程内验证：未登录 `/`→非 500、登录流、业务路由 `/orders /invoices /items /customers /suppliers /purchase /accounting /ai /guide`→200、`/swagger.json`→合法 JSON、静态资源→200。全过打印 `[GATE] 全部通过，可交付/可打包`。

### 打包为 EXE（PyInstaller 要点）

扁平布局：仓库根即冻结态 `RESOURCE_DIR = Path(sys._MEIPASS)`（无 `app/`）。推荐用技能级构建驱动：

```bash
python scripts/build_fast_example.py \
  --project-dir examples/04-FastERP --app-name FastERP --port 5011
```

等效手动命令（最小构建 venv，在 `examples/04-FastERP/` 内）：

```bash
pyinstaller main.py --onefile --noupx --console \
  --name FastERP \
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
1. **项目模块自动收集**：`web_app.py` `db.py` `seed.py` `fasterp/` `web/` 经 `import web_app` 自动收入冻结包，无需 `--add-data`。
2. **sqlite3**：须用 `scripts/pyinstaller_hooks/hook-sqlite3.py`（`--additional-hooks-dir`）收集 `_sqlite3.pyd` / `sqlite3.dll`；DB 走 `FASTERP_DB` 重定向到可写 `data/`。
3. **pywebview**：`clr` + `webview.platforms.winforms` + `webview.platforms.edgechromium` + `webview/lib` 必须。
4. **PostgreSQL（可选）**：默认不启用；如需打包 PostgreSQL 运行时，追加收集 `fasterp.database`（psycopg）。纯 SQLite 桌面分发无需。
5. **冒烟**：启动 EXE 验证 `http://127.0.0.1:5011/` 返回 200 且窗口句柄存在。

### 环境变量完整清单

| 变量 | 默认 | 说明 |
|---|---|---|
| `FASTERP_DB` | `fasterp.sqlite` | SQLite 路径（桌面态重定向到 `data/`） |
| `FASTERP_PORT` | `5011` | Web 服务端口 |
| `FASTERP_ADMIN_EMAIL` | `admin@fasterp.example` | 登录邮箱 |
| `FASTERP_ADMIN_PASSWORD` | `FastERP2026$` | 登录密码 |
| `FASTERP_SECRET` | 随机 | 会话签名密钥 |
| `FASTERP_ENV_LABEL` | `FastERP` | UI 标签 |
| `FASTERP_RELOAD` | `0` | 开发热重载 |
| `DB_URL` | 空 | 非空则切 PostgreSQL 运行时 |
| `MODEL_PROVIDER` | `xai` | xai / openai / anthropic / google |
| `MODEL_NAME` | `grok-4-1-fast-reasoning` | 模型名 |
| `XAI_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` | 空 | 对应厂商 Key |

---

## 许可

MIT。上游 [predictivelabsai/FastERP](https://github.com/predictivelabsai/FastERP)（Predictive Labs Ltd），本地做了 SQLite 化、注册登录离线修复、移除大文件三类必要适配。完整版权与改动说明见 `../../THIRD_PARTY_NOTICES.md`。
