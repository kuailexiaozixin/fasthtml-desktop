# FastHRM（桌面版 / Desktop）

**FastHRM** 是一个基于 [FastHTML](https://fastht.ml) 的开源 HR 系统，是 [Frappe HR (HRMS)](https://github.com/frappe/hrms) 核心的「服务器端 + HTMX」移植版，聚焦三大支柱：**人**（员工目录 + 部门）、**时间**（请假 + 考勤）、**薪**（工资单）。纯 Python、无 JS 框架，并带一个基于实时（合成）数据的 AI 助手。

*People ops, without the spreadsheets.* 默认端口 **5010**。

> ⚠️ **仅含合成数据，无真实 PII。** 全部数据由 `seed.py` 生成确定性合成数据。

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

> ⚠️ 注意：`start.py` 是**开发者命令行工具**，不是供最终用户双击的启动器——`.py` 双击默认会用编辑器打开，不会运行。用户入口统一是 **`启动.bat`**。



首次运行：① 若没有 `.venv` 则创建并 `pip install -r requirements.txt pywebview`；② 若本地无数据库自动 `seed.build()`；③ 启动服务（默认 `http://127.0.0.1:5010`）并打开桌面窗口。

### 登录凭据（默认）

- 邮箱：`admin@fasthr.example`
- 密码：`FastHR2026$`

可在 `.env` 中用 `FASTHR_ADMIN_EMAIL` / `FASTHR_ADMIN_PASSWORD` 覆盖。

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
| `/` | 仪表盘：人数、今日在岗、30 天出勤率、待批请假、部门人数、今日请假、待办工作流 |
| `/employees` | 员工目录：按部门筛选、可搜索；档案含**假期余额**、色码**考勤条**、**工资单** |
| `/departments` | 部门：人数、负责人、年度薪资 |
| `/leave` | 请假：按状态（待批 / 已批 / 已拒 …） |
| `/attendance` | 考勤：今日登记与状态分布 |
| `/payroll` | 薪资：各期工资单，含完整扣款明细 |
| `/ai` | AI 助手（右侧栏） |
| `/guide` | 使用指引 |

**AI 助手**：slash 命令 `/headcount /leave /today /payroll` **无需 API Key**；自由聊天需厂商 Key。

### 数据落点

桌面运行时 SQLite 通过 `FASTHR_DB` 重定向到 **可执行文件所在目录的 `data/fasthr.sqlite`**（可写）。开发态默认 `fasthr.sqlite`。重置：`python start.py --reseed`。

### AI（自由聊天）配置

```ini
MODEL_PROVIDER=xai          # xai | openai | anthropic | google
MODEL_NAME=grok-4-1-fast-reasoning
XAI_API_KEY=...             # 或 OPENAI_API_KEY / ANTHROPIC_API_KEY / GOOGLE_API_KEY
```

无 Key 时应用与 slash 命令仍可用，仅自由聊天不可用。

---

## 用途二：给 LLM / 开发者（克隆说明书）

### 目录树

```
05-FastHRM/
├── web_app.py        # 路由、鉴权、SSE 聊天、boot（serve(port=PORT)）
├── db.py             # SQLite schema（people/time/pay）+ 读取 helper；DB_PATH = getenv("FASTHR_DB")
├── seed.py           # 确定性合成：组织、请假、考勤、薪资
├── main.py           # 桌面入口（pywebview + uvicorn）
├── start.py          # 一键脚本：建 venv / 装依赖 / 启动 / --check / --reseed
├── dev_check.py      # 进程内 TestClient 质量门禁
├── requirements.txt  # python-fasthtml>=0.12.0, fastapi>=0.115, uvicorn>=0.30, httpx>=0.27, python-dotenv>=1.0
├── web/
│   ├── layout.py / views.py / ai.py / api_core.py / api.py / account_auth.py / google_auth.py / developer.py / landing.py
│   └── static/
├── static/  docs/  docs/openhr-reference/  scripts/  Dockerfile  docker-compose.yml  .env.sample  SKILLS.md  swagger.json
└── data/             # 运行时数据库（桌面态落点，**勿打包进 EXE**）
```

> 克隆时只保留源码，排除 `.venv/`、`data/`、根目录已生成的 `fasthr.sqlite`。`docs/openhr-reference/` 为历史参考实现，可保留也可忽略。

### 入口与端口

- **服务入口**：`web_app.py` 末尾 `serve(port=PORT, reload=os.getenv("FASTHR_RELOAD","0")=="1")`；`PORT = int(os.getenv("FASTHR_PORT", "5010"))`。
- **桌面入口**：`main.py` 计算 `RESOURCE_DIR = Path(sys._MEIPASS)`、`DATA_DIR = exe父目录/"data"`，`os.environ.setdefault("FASTHR_DB", str(DATA_DIR/"fasthr.sqlite"))`，`os.chdir(RESOURCE_DIR)`，`find_free_port(5010)`，`wait_for_server(...)`，`webview.create_window("FastHR", url, width=1280, height=840)`。`SERVER_ONLY=1` 无头模式。

### 数据库约定（`db.py`）

```python
DB_PATH = os.getenv("FASTHR_DB") or str(Path(__file__).parent / "fasthr.sqlite")
```

### 合成数据播种与导入顺序（关键）

`web_app.py` 启动时 `_ensure_db()` 自动 `seed.build()`。`main.py` / `start.py` / `dev_check.py` 都内置 `_bootstrap_db()`，在 `import web_app` **之前**先播种：

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
- **`dev_check.py`**：`TestClient(web_app.app)` 进程内验证：未登录 `/`→非 500、登录流、业务路由 `/employees /departments /leave /attendance /payroll /ai /guide`→200、`/swagger.json`→合法 JSON、静态资源→200。全过打印 `[GATE] 全部通过，可交付/可打包`。

### 打包为 EXE（PyInstaller 要点）

扁平布局（同 03）：仓库根即冻结态 `RESOURCE_DIR = Path(sys._MEIPASS)`（无 `app/`）。推荐用技能级构建驱动：

```bash
python scripts/build_fast_example.py \
  --project-dir examples/05-FastHRM --app-name FastHRM --port 5010
```

等效手动命令（最小构建 venv，在 `examples/05-FastHRM/` 内）：

```bash
pyinstaller main.py --onefile --noupx --console \
  --name FastHRM \
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
2. **sqlite3**：须用 `scripts/pyinstaller_hooks/hook-sqlite3.py`（`--additional-hooks-dir`）收集 `_sqlite3.pyd` / `sqlite3.dll`；DB 走 `FASTHR_DB` 重定向到可写 `data/`。
3. **pywebview**：`clr` + `webview.platforms.winforms` + `webview.platforms.edgechromium` + `webview/lib` 必须。
4. **冒烟**：启动 EXE 验证 `http://127.0.0.1:5010/` 返回 200 且窗口句柄存在。

### 环境变量完整清单

| 变量 | 默认 | 说明 |
|---|---|---|
| `FASTHR_DB` | `fasthr.sqlite` | SQLite 路径（桌面态重定向到 `data/`） |
| `FASTHR_PORT` | `5010` | 服务端口 |
| `FASTHR_ADMIN_EMAIL` | `admin@fasthr.example` | 登录邮箱 |
| `FASTHR_ADMIN_PASSWORD` | `FastHR2026$` | 登录密码 |
| `FASTHR_SECRET` | 随机 | 会话签名密钥 |
| `FASTHR_ENV_LABEL` | `FastHR` | UI 标签 |
| `FASTHR_RELOAD` | `0` | 开发热重载 |
| `MODEL_PROVIDER` | `xai` | xai / openai / anthropic / google |
| `MODEL_NAME` | `grok-4-1-fast-reasoning` | 模型名 |
| `XAI_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` | 空 | 对应厂商 Key |

---

## 许可

MIT。属于 [`fasthtml-oss-migrations`](https://github.com/predictivelabsai/fasthtml-oss-migrations) 计划（FastHRM 整合了早期 openhr 项目，参考实现见 `docs/openhr-reference/`）。
