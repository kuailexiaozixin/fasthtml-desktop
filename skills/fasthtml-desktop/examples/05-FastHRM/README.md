# FastHRM（桌面版 / Desktop）

**FastHRM** 是一个基于 [FastHTML](https://fastht.ml) 的开源 HR 系统，是 [Frappe HR (HRMS)](https://github.com/frappe/hrms) 核心的「服务器端 + HTMX」移植版。除三大支柱（**人**：员工目录 + 部门；**时间**：请假 + 考勤；**薪**：工资单）外，还包含**完整的 ATS 招聘 + 人才平台 + 员工生命周期**模块。纯 Python、无 JS 框架，并带一个基于实时（合成）数据的 AI 助手。

*People ops, without the spreadsheets.* 默认端口 **5010**。

> ⚠️ **仅含合成数据，无真实 PII。** 全部数据由 `seed.py` / `seed_talent.py` / `seed_platform.py` 生成确定性合成数据。

> 本示例为上游 [predictivelabsai/FastHRM](https://github.com/predictivelabsai/FastHRM) **完整版**克隆（含 recruitment / talent / ATS / 生命周期全套模块），并做了三类本地必要适配：**SQLite 化**、**修复注册登录（离线免邮件验证）**、**移除大体积文档/媒体**。合规见 `../../THIRD_PARTY_NOTICES.md`。

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

首次运行：① `launcher.py` 预检 `requirements.txt` 依赖（缺失自动装）；② `import web_app` 时顶层 `_ensure_db()` 自动建库并播种（HR + ATS 招聘 + 人才绩效）；③ 启动服务（默认 `http://127.0.0.1:5010`）并打开桌面窗口。

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

**三大支柱（人 / 时间 / 薪）**
| 路由 | 模块 |
|---|---|
| `/` | 仪表盘：人数、今日在岗、30 天出勤率、待批请假、部门人数、今日请假、待办工作流 |
| `/employees` | 员工目录：按部门筛选、可搜索；档案含**假期余额**、色码**考勤条**、**工资单** |
| `/departments` | 部门：人数、负责人、年度薪资 |
| `/leave` | 请假：按状态（待批 / 已批 / 已拒 …） |
| `/attendance` | 考勤：今日登记与状态分布 |
| `/payroll` | 薪资：各期工资单，含完整扣款明细 |

**ATS 招聘 + 人才平台 + 生命周期（上游完整版）**
| 路由 | 模块 |
|---|---|
| `/careers` `/jobs/{slug}` | 公开职位页 / 职位详情 + 在线申请 |
| `/talent/candidates` `/talent/jobs` `/talent/offers` | 招聘漏斗：候选人、职位、面试评分、Offer |
| `/talent` `/performance` | 人才平台：能力模型、评分卡、绩效目标、反馈、OKR |
| `/lifecycle/*` | 员工生命周期：入职清单、离职、调动、组织/岗位变更、校友 |
| `/experiments` `/campaigns` | A/B 实验、招聘营销活动 |
| `/ai` | AI 助手（右侧栏） |
| `/guide` | 使用指引 |

**AI 助手**：slash 命令 `/headcount /leave /today /payroll /ats` **无需 API Key**；自由聊天需厂商 Key；简历/CV 提取需配置 LLM（见下）。

### 数据落点

桌面运行时 SQLite 通过 `FASTHR_DB` 重定向到 **可执行文件所在目录的 `data/fasthr.sqlite`**（可写）。开发态默认 `fasthr.sqlite`。重置：`python start.py --reseed`。

### AI（自由聊天）配置

```ini
MODEL_PROVIDER=xai          # xai | openai | anthropic | google
MODEL_NAME=grok-4-1-fast-reasoning
XAI_API_KEY=...             # 或 OPENAI_API_KEY / ANTHROPIC_API_KEY / GOOGLE_API_KEY
```

无 Key 时应用与 slash 命令仍可用，仅自由聊天不可用。

### 简历/CV 提取（可选，依赖 langchain）

```bash
pip install -r requirements.txt   # 已含 langchain-core/langchain-openai/pdfplumber/python-docx/Pillow
# 配一个 OpenAI 兼容 Key（xAI / OpenAI）即可启用简历解析
```

未配置时招聘流程其余功能不受影响，仅 CV 解析会提示缺 Key。

### 测试

```bash
python -m pytest -q        # tests/ 含版本、公开页面等测试
```

---

## 用途二：给 LLM / 开发者（克隆说明书）

### 目录树

```
05-FastHRM/
├── web_app.py        # FastHTML 路由、鉴权、SSE 聊天、boot（顶层 _ensure_db() + serve(port=PORT)，约 2500 行）
├── db.py             # SQLite schema（migrations/）+ 读取 helper；DB_PATH = getenv("FASTHR_DB")
├── talent.py / people.py / recruitment.py / recruitment_communications.py /
│   recruitment_ecosystem.py / recruitment_enterprise.py / recruiting_ops.py / integrations.py
│                     # 领域模块（ATS / 人才 / 生命周期 / 集成）
├── seed.py / seed_talent.py / seed_platform.py   # 确定性合成种子
├── version.py / VERSION                          # 版本号
├── main.py           # 桌面入口（pywebview + uvicorn）
├── start.py          # 一键脚本：建 venv / 装依赖 / 启动 / --check / --reseed
├── dev_check.py      # 进程内 TestClient 质量门禁
├── migrations/       # 版本化 SQL 迁移（0001_baseline ... 0005_recruitment_platform）
├── requirements.txt  # python-fasthtml>=0.12.0, fastapi>=0.115, uvicorn>=0.30, httpx>=0.27, python-dotenv>=1.0, python-multipart, langchain-core, langchain-openai, pdfplumber, python-docx, Pillow
├── web/
│   ├── layout.py / views.py / ai.py / ats.py / careers.py / cv_extract.py / ranking.py /
│   │   performance.py / lifecycle.py / recruiting_platform.py / settings.py /
│   │   api_core.py / api.py / account_auth.py / google_auth.py / developer.py / landing.py / seo.py
│   └── static/
├── static/  docs/  scripts/  skills/  tests/  Dockerfile  docker-compose.yml  .env.sample  SKILLS.md  swagger.json
└── data/             # 运行时数据库（桌面态落点，**勿打包进 EXE**）
```

> 克隆时只保留源码，排除 `.venv/`、`data/`、根目录已生成的 `fasthr.sqlite`。

### 入口与端口

- **服务入口**：`web_app.py` 末尾 `serve(port=PORT, reload=os.getenv("FASTHR_RELOAD","0")=="1")`；`PORT = int(os.getenv("FASTHR_PORT", "5010"))`。
- **桌面入口**：`main.py` 计算 `RESOURCE_DIR = Path(sys._MEIPASS)`、`DATA_DIR = exe父目录/"data"`，`os.environ.setdefault("FASTHR_DB", str(DATA_DIR/"fasthr.sqlite"))`，`os.chdir(RESOURCE_DIR)`，`find_free_port(5010)`，`wait_for_server(...)`，`webview.create_window("FastHRM", url, width=1280, height=840)`。`SERVER_ONLY=1` 无头模式。

### 数据库约定（`db.py`）

```python
DB_PATH = os.getenv("FASTHR_DB") or str(Path(__file__).parent / "fasthr.sqlite")
```

schema 由 `migrations/*.sql` 版本化管理，`db.migrate()` 按文件名顺序应用并记录到 `schema_migrations`。

### 建库播种与导入顺序（关键）

`web_app.py` 在**顶层**调用 `_ensure_db()`（import 即触发）：`migrate()` 应用 SQL 迁移，无数据时依次 `seed.py`（HR）、`seed_talent.py`（招聘漏斗）、`seed_platform.py`（绩效/目标/生命周期）播种。因此 `main.py` / `start.py` / `dev_check.py` **无需**额外的 `_bootstrap_db()`，只需在设置好 `FASTHR_DB` 环境变量后 `import web_app`：

```python
import os
os.environ.setdefault("FASTHR_DB", str(DATA_DIR / "fasthr.sqlite"))
import web_app   # 触发顶层 _ensure_db()：迁移建库 + 三类播种
```

**务必「先设 `FASTHR_DB`，再 `import web_app`」。**

### 三件套机制

- **`main.py`**：EXE 入口，`os.chdir(RESOURCE_DIR)` 后 `import web_app`，`uvicorn.Server(Config(web_app.app, host="127.0.0.1", port=port, reload=False))` 起服务，再 pywebview 开窗口。
- **`start.py`**：`ensure_env()` 幂等建 venv 并装依赖；`start()` 设 `FASTHR_DB` 后 `import web_app`；`--check`/`--reseed`/`--port` 见上。
- **`dev_check.py`**：`TestClient(web_app.app)` 进程内验证：未登录 `/`→非 500、登录流、核心业务路由 `/employees /departments /leave /attendance /payroll /careers /talent/candidates /ai /guide`→200、`/swagger.json`→合法 JSON、静态资源→200。全过打印 `[GATE] 全部通过，可交付/可打包`。

### 打包为 EXE（PyInstaller 要点）

扁平布局：仓库根即冻结态 `RESOURCE_DIR = Path(sys._MEIPASS)`（无 `app/`）。推荐用技能级构建驱动：

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
1. **项目模块自动收集**：`web_app.py` `db.py` 各领域模块 `web/` `migrations/` 经 `import web_app` 自动收入冻结包，无需 `--add-data`。
2. **sqlite3**：须用 `scripts/pyinstaller_hooks/hook-sqlite3.py`（`--additional-hooks-dir`）收集 `_sqlite3.pyd` / `sqlite3.dll`；DB 走 `FASTHR_DB` 重定向到可写 `data/`。
3. **pywebview**：`clr` + `webview.platforms.winforms` + `webview.platforms.edgechromium` + `webview/lib` 必须。
4. **LLM 依赖（可选）**：langchain-openai / pdfplumber / python-docx 用于 CV 提取，桌面主流程不 import，可裁剪以减小 EXE。
5. **冒烟**：启动 EXE 验证 `http://127.0.0.1:5010/` 返回 200 且窗口句柄存在。

### 环境变量完整清单

| 变量 | 默认 | 说明 |
|---|---|---|
| `FASTHR_DB` | `fasthr.sqlite` | SQLite 路径（桌面态重定向到 `data/`） |
| `FASTHR_PORT` | `5010` | 服务端口 |
| `FASTHR_ADMIN_EMAIL` | `admin@fasthr.example` | 登录邮箱 |
| `FASTHR_ADMIN_PASSWORD` | `FastHR2026$` | 登录密码 |
| `FASTHR_SECRET` | 随机 | 会话签名密钥 |
| `FASTHR_ENV_LABEL` | `FastHRM` | UI 标签 |
| `FASTHR_RELOAD` | `0` | 开发热重载 |
| `MODEL_PROVIDER` | `xai` | xai / openai / anthropic / google |
| `MODEL_NAME` | `grok-4-1-fast-reasoning` | 模型名 |
| `XAI_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` | 空 | 对应厂商 Key |

---

## 许可

MIT。上游 [predictivelabsai/FastHRM](https://github.com/predictivelabsai/FastHRM)（Predictive Labs Ltd），本地做了 SQLite 化、注册登录离线修复、移除大文件三类必要适配。完整版权与改动说明见 `../../THIRD_PARTY_NOTICES.md`。
