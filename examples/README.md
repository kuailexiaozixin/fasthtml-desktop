# 示例 / Examples

> **定位声明（参考语料）**：本目录是给 LLM / 开发者当**参考语料**的「重型应用范例库」，不是交付产品模板。其启动器采用 **「薄 `启动.bat`（≤10 行，仅派发）+ `launcher.py`（决策层）」分层**，`launcher.py` 统一由 `scripts/gen_launchers.py` 从 `templates/shared/launcher.py` 分发——**请勿手写、请勿照抄/硬编码任何绝对路径（尤其 `C:\Users\<name>\...`）**，因为 examples 里的每一行都可能被未来的模型学走。examples 演示场景「复用全局 Python、不建 `.venv`」与真实项目「建最小 `.venv`」环境策略相反，二者**不可互相套用**启动器。

本目录是 `fasthtml-desktop` 技能的**可运行参考实现**。每个子目录都是一个独立、可直接运行的
FastHTML + pywebview 桌面应用示例，用纯 Python 演示「写桌面软件」的多种业务路线与可复用的设计模式。
每个示例都附有 **「可借鉴要点」**——做自己的 fasthtml 桌面应用时，能直接从该示例里抠走的零件。

所有示例共用同一套本地桌面架构：**pywebview 原生窗口（WebView2 控件）+ 本地 FastAPI/uvicorn 服务
@ 127.0.0.1:PORT + 本地 SQLite**，完全离线运行，并非在线网站。双击 `启动.bat` 即可拉起桌面窗口，
依赖自动安装到 Python 全局环境（不建示例目录内的 `.venv`，避免文件夹膨胀）。

| 示例 | 业务 / 技术路线 | 运行期依赖 | 入口 |
|------|----------------|-----------|------|
| `01-Bricksmith/` | 企业知识库 + 检索增强问答（predictivelabsai/bricksmith 完整克隆 + 仅加桌面壳，SQLite + sqlite-vec 向量检索） | `fasthtml` `sqlite-vec` `fastembed` `pywebview` `uvicorn` | 双击 `启动.bat`（默认端口 5001，RAG 需 LLM Key） |
| `02-TrafficData/` | 交通数据只读看板（predictivelabsai/traffic-data-analysis 完整克隆 + 仅加桌面壳，6 个 Plotly 页） | `fasthtml` `plotly` `pandas` `numpy` `pywebview` `uvicorn` | 双击 `启动.bat`（默认端口 5001，纯离线） |
| `03-FastCRM/` | 销售 CRM（Frappe CRM 的「服务端 + HTMX」移植） | `fasthtml` `pywebview` `uvicorn` | 双击 `启动.bat`（默认端口 5006） |
| `04-FastERP/` | ERP（predictivelabsai/FastERP **上游完整版**克隆：ERPNext 移植 + fasterp 业务包 + SAP 迁移模块；本地做了 SQLite 化/注册登录离线修复/去大文件） | `fasthtml` `pywebview` `uvicorn` `psycopg` | 双击 `启动.bat`（默认端口 5011） |
| `05-FastHRM/` | HR 系统（predictivelabsai/FastHRM **上游完整版**克隆：人/时间/薪 + ATS 招聘 + 人才平台 + 生命周期；本地做了 SQLite 化/注册登录离线修复/去大文件） | `fasthtml` `pywebview` `uvicorn` `langchain-openai` `pdfplumber` | 双击 `启动.bat`（默认端口 5010） |
| `06-FastInsights/` | BI 工具（Frappe Insights 移植，Plotly + AI 文本转 SQL） | `fasthtml` `pywebview` `uvicorn` | 双击 `启动.bat`（默认端口 5008） |
| `07-genui-weather/` | 生成式 UI 三件套（kafkasl/genUI 完整克隆 + 仅加桌面壳：weather / your_color / hal9000） | `fasthtml` `pywebview` `uvicorn` | 双击 `启动-weather.bat`（weather，默认端口 5001，需 ANTHROPIC_API_KEY）；另含 `启动-your_color.bat` / `启动-hal9000.bat` |
| `08-code-assistant/` | AI 代码助手（phact/code-assistant 完整克隆 + 仅加桌面壳，生成可运行 Web 应用） | `python-fasthtml==0.5.1`（外置隔离 venv）`pywebview` | 双击 `启动.bat`（默认端口 5001，需 LLM Key） |
| `09-FastSheets/` | 电子表格（Frappe Sheets 移植，公式引擎 + 多工作表 + AI 助手） | `fasthtml` `pywebview` `uvicorn` `httpx` | 双击 `启动.bat`（默认端口 5014） |
| `10-FastSlides/` | 演示文稿（Frappe Slides 移植，幻灯片编辑器 + 演示模式 + AI 生成） | `fasthtml` `pywebview` `uvicorn` `httpx` `markdown` | 双击 `启动.bat`（默认端口 5013） |
| `11-FastDrive/` | 文件管理（Frappe Drive 移植，文件/文件夹浏览器 + 分享 + AI 助手） | `fasthtml` `pywebview` `uvicorn` `httpx` | 双击 `启动.bat`（默认端口 5012） |
| `12-FastLegal/` | 法务 AI（predictivelabsai/FastLegal 移植，助手 / 项目 / 表格化审阅 / 工作流） | `fasthtml` `monsterui` `sqlalchemy` `bcrypt` `pywebview` | 双击 `启动.bat`（默认端口 5015） |
| `13-FastLMS/` | 在线教育 LMS（predictivelabsai/FastLMS 移植，课程 / 课时 / 测验 / 排行榜 / 校区管理） | `fasthtml` `fastapi` `sqlalchemy` `pywebview` | 双击 `启动.bat`（默认端口 5016） |
| `14-FastMeet/` | 会议协作（predictivelabsai/FastMeet 移植，日程 / 会议室 / 纪要 / AI 议程） | `fasthtml` `pywebview` `uvicorn` `httpx` | 双击 `启动.bat`（默认端口 5017） |
| `15-FastMail/` | 邮件客户端（predictivelabsai/FastMail 移植，收发件箱 / 标签 / 联系人 / 日历 / AI 摘要） | `fasthtml` `pywebview` `uvicorn` `httpx` | 双击 `启动.bat`（默认端口 5018） |
| `16-FastDocs/` | 文档编辑器（predictivelabsai/FastDocs = Frappe Writer 移植，文件夹文档库 / 块编辑器 / 模板 / 版本历史 / AI 写作助手） | `fasthtml` `fastapi` `pywebview` `uvicorn` `httpx` `markdown` `python-dotenv` `python-multipart` | 双击 `启动.bat`（默认端口 5019） |
| `17-FastESM/` | 企业服务管理 ESM（predictivelabsai/FastESM，服务目录 / 请求编排+SLA / RBAC / 知识库 / 表单工作流设计器 / Plotly 看板 / AI 助手） | `fasthtml` `fastapi` `pywebview` `uvicorn` `httpx` `python-dotenv` `python-multipart` | 双击 `启动.bat`（默认端口 5020） |
| `18-FastMSR/` | 按揭服务权管理（predictivelabsai/FastMSR，贷款组合 / DCF 估值引擎 / 模拟 Freddie Mac CRX 竞价交易所 / 转让流程 / 合规审计） | `fasthtml` `pywebview` `uvicorn` `httpx` `python-dotenv` `python-multipart` | 双击 `启动.bat`（默认端口 5021） |
| `19-open-docflow/` | 文档工作流（predictivelabsai/open-docflow 移植，文档上传 / 状态流转 / 状态统计 / 审计追踪，PostgreSQL→SQLite） | `fasthtml` `sqlalchemy` `pywebview` `uvicorn` `httpx` `python-multipart` `python-dateutil` | 双击 `启动.bat`（默认端口 5022） |
| `20-FastHelpdesk/` | 客服工单台（predictivelabsai/FastHelpdesk = Frappe Helpdesk 移植，工单队列 + 实时 SLA / 会话 / 客服团队 / 知识库 / AI 助手） | `fasthtml` `fastapi` `pywebview` `uvicorn` `httpx` `python-dotenv` `python-multipart` | 双击 `启动.bat`（默认端口 5023） |

> **运行前提**：Windows 10/11 需已安装 **Microsoft Edge WebView2 Runtime**（系统通常预装）；若缺失，
> `启动.bat` 会提示并给出下载地址。examples 不随附预构建 EXE，按需按各子目录 README 的「打包」章节构建。

> **验证状态**：全部 20 个示例均已接入统一启动器（`launcher.py`/`启动.bat` 由 `scripts/gen_launchers.py` 从 `templates/shared/launcher.py` 分发，逐字节同源；项目差异在 `launcher.json`，**禁止手写**）。启动器策略与门禁见下方「启动器策略」一节。各示例的**无头启动**（`launcher.py server`）+ `dev_check.py` 质量门禁均已实测通过：① `launcher.py --check` 依赖预检缺包已清零（仅 **01** 缺 3 个可选依赖 `exa-py`/`pytest-asyncio`/`reportlab`，非核心运行依赖）；② 无头 HTTP 实测全部启动成功；③ **08** 的多厂商接入（`scripts/verify_providers.py`）全 PASS（DeepSeek / OpenRouter / Agnes 2）。需要 LLM Key 的 AI 功能（01 RAG、07 生成式 UI、08 代码生成，及 03/06/09/10/11/13–20 的助手）缺 Key 时页面可开、对应功能走上游报错（非缺陷）。**桌面窗口实际打开需本机 WebView2 环境实测**——沙箱无法开 GUI，故 README 不宣称「双击即运行」未经实测。

---

## 启动器策略（examples 专属 — 请勿手写启动器）

> 本节的详细策略**原本写在 SKILL.md「§B 启动器 B：examples（演示语料）」**，为使 SKILL.md 保持精简、examples 细节集中管理，已整体迁移至此。SKILL.md 仅保留一句指针。

**目的**：给 LLM 当参考语料 + 给人快速看效果。环境策略 = **副作用最小优先**，对宿主机的影响**应当近似只读**——这是关键。examples 里的每一行都在「教」未来的模型，硬编码路径 / 包管理器启发式都是会被继承的坏范式。本策略与 SKILL.md **§A 启动器 A（真实项目，建最小 `.venv`）正好相反**，不可混用启动器。

> **示例拓扑与 Key 依赖分类（一眼看清「为什么全部示例双击即起、离线可跑」）**：
> - **单进程 fasthtml(ASGI) + uvicorn（01~20）**：壳直接 uvicorn 托管上游 app，依赖轻量或已随全局存在，**双击即起、离线可跑**；其中 **01（RAG 知识库）、07（生成式 UI）、08（代码助手）** 的核心 AI 功能需配置 LLM Key，缺 Key 时页面可开但对话/生成会报错（上游行为），其余示例纯离线即可用全部功能。
> - **Key 依赖维度**：所有示例的登录 / 业务路由 / 基础 UI 均**离线可跑**（登录走演示账号或离线注册修复）；**AI 对话 / 生成类功能**（03/06/09/10/11/13~20 的助手，以及 01 RAG、07 生成式 UI、08 代码生成）需按各自 README 配置 LLM Key，缺 Key 时对应功能报错但其余照常。
> - **新增 examples 建议先跑 `python scripts/probe_upstream.py <示例目录>`**，提前发现 picolink 类「上游 import 了但当前 fasthtml 已移除」的 API 漂移。
>
> - **examples 启动器复用全局环境，禁止 `.venv`、禁止写死路径**：用**系统默认 PATH 的 `python`**（`where python`）→ **复用全局 `site-packages`、不建 `.venv`**（保持技能目录体积干净）→ 缺失才装 → 弹桌面窗口。副作用最小优先。**严禁硬编码任何绝对解释器路径**——尤其禁止硬编码用户名目录或 WorkBuddy 托管解释器路径（如 `C:\Users\<name>\.workbuddy\binaries\python\versions\*`）。理由：① 用户终端里的 `python` 才是依赖齐全的那个，写死会指向残缺环境，表现为「明明装了却报缺包」；② 硬编码用户名使脚本不可移植，换机即废；③ examples 是**给 LLM 的参考语料**，硬编码路径会被照抄进真实项目。**注意区分**：打包阶段仍须另行创建**最小构建 venv**（见 SKILL.md §打包 铁律「必须最小 venv 打包」），那是隔离打包依赖、控制 EXE 体积用的，与启动器运行期复用全局环境互不干扰。

- **版本互斥的正确处置（禁止在示例目录内建 `.venv`）**：若某示例依赖版本与既有示例互斥（如某示例锁定 `python-fasthtml==0.5.1` 与 03-06 的 `>=0.12.0` 数学上不可共存），**禁止在示例目录里建 `.venv`**——那会撑大技能目录、违背 examples 定位。正确做法按优先级：① **放宽 pin**，统一到与其他示例共存的版本基线（上游 `uv.lock` 是锁文件，不是运行时硬约束）；② **拆分公共依赖与增量依赖**（`examples/requirements-common.txt` + 各示例增量）；③ **外置隔离环境（`ISOLATED_VENV`）**——见下条；④ 以上都不可行时才**降级为「只预检不安装」**（`AUTO_INSTALL=False`，照 tkinter-desktop 的 `pygubu-designer` 模式打印安装命令让用户自行决定），并在 README 说明「本示例与 XX 版本互斥，需独立环境运行」。

- **外置隔离环境（`ISOLATED_VENV`）：兼顾「不降级全局」与「目录不膨胀」的唯一解**：`launcher.json` 填 `"isolated_venv": "<示例名>"` 后，启动器会在 **`%LOCALAPPDATA%/fasthtml-desktop/venvs/<示例名>`**（非 Windows 取 `~/.cache/...`；环境变量 `FD_VENV_HOME` 可改）建 `--system-site-packages` 环境并重入。三点成立才选它：① 互斥版本只落在该环境内并**遮蔽**全局同名包，用户全局 `site-packages` 一个字节不动；② 环境在示例目录**之外**，技能仓库体积不变（`git status` 干净，无需 `.gitignore` 兜底）；③ 装包优先用 **uv**（包体从 uv 全局 cache **硬链接**，多环境共享同一份盘、装包提速一个量级），uv 失败自动回退 pip（uv 对 requirements 语法更严，如 `--only-binary a,b` 逗号列表 uv 拒收）。配套细节：用 `requirements.txt` 的 md5 **指纹戳**（环境内 `.fd_reqs_stamp`）判断是否需要重装，日常启动零开销；**在隔离环境内不做降级拦截**（遮蔽全局本就是目的）；卸载 = 删除该目录，全局无残留。

- **禁止降级用户已装包**：`启动.bat` / `launcher.py` 安装依赖前必须比对已装版本，若本次安装会导致 **downgrade**，一律**告警 + 中止**，严禁静默覆盖用户全局环境。各（AUTO_INSTALL=True 的）示例共享同一 `site-packages`，一次静默降级即可让其余示例集体失效（已发生过：一次旧 pin 安装挤掉了 `fastapi`/`requests`，导致 01-06 全灭，且 `pip check` 仍报 `No broken requirements found`——损坏是静默的）。注：采用 `ISOLATED_VENV` 或 `BUNDLED_VENV`（`launcher.json` 声明、环境建在目录之外）的示例均不会向全局 `site-packages` 灌包。

- **examples 验证门禁（未实测不得宣称可用）**：新增或修改 examples 的启动脚本后，**必须实际执行一次并确认窗口打开**，留下可核验的运行证据（启动器的窗口已打开日志标记，或等价记录）。**未验证的示例禁止在 README / SKILL.md 中宣称「双击即运行」**——「我写了脚本」不等于「它能用」。

---

## `01-Bricksmith/` — 企业知识库 + RAG 问答（predictivelabsai/bricksmith 移植）

FastHTML + sqlite-vec 的企业知识库与检索增强问答：把文档切块嵌入、存进本地 SQLite 并用向量相似度召回，再交给 LLM 生成答案。要点（详见 [`01-Bricksmith/README.md`](01-Bricksmith/README.md)）：

- **sqlite-vec 原生向量检索**：用 `sqlite-vec` 扩展让 SQLite 直接存向量、做相似度检索，替代自写 numpy 余弦相似度——RAG 的「知识块召回」全程在一个 SQLite 文件内完成，零外部向量库、完全离线。
- **PostgreSQL → SQLite 落地**：上游用 PG，本示例换成本地 SQLite（`data/bricksmith.db` 首启动自动建表播种 `embedding_dim=384`），双击即跑、无外部服务。
- **嵌入模型懒加载 + 离线兜底**：`fastembed` 在首次检索时下载模型；缺网络时可用占位嵌入验证「存储 → 召回」链路，不卡启动。
- **两层启动器 + 统一桌面壳**：复用 `启动.bat`/`launcher.py`，`SERVER_ONLY=1` 无头可跑；`dev_check.py` 8 项门禁全绿（7 公开路由 + 1 静态资源）。

## `02-TrafficData/` — 交通数据只读看板（predictivelabsai/traffic-data-analysis 移植）

FastHTML + Plotly 的纯合成数据只读看板：6 个分析页（总览 / 起讫点 / 车速 / 行程 / 地图 / 数据源），无数据库、无登录、无 API Key。要点（详见 [`02-TrafficData/README.md`](02-TrafficData/README.md)）：

- **零后端依赖的纯看板**：最适合做「双击即看全部功能」的演示——无 DB、无账号、无需任何 Key，六个 Plotly 页全离线可跑。
- **离线 plotly.js 注入（关键）**：桌面壳首启动把已装 `plotly` 包的 `plotly.min.js`（4.6MB）复制到 `vendor/`，把 CDN 指向改成本地 `/vendor/plotly.min.js`，彻底摆脱 CDN 依赖（否则离线时图全白）；`vendor/` 已 gitignore，首启动自动重建。
- **合成数据生成**：首启动数秒生成约 2.3 万条观测（zones/od/speed/journey/gps 各表非空），`dev_check.py` 14 项门禁校验业务页 + 离线注入 + 数据非空全绿。
- **可借鉴套路**：把「重型前端依赖（CDN）」改为「首次启动从已装 Python 包提取并缓存到本地」的离线化模式，通用且零网络。

## `03-FastCRM/` — 销售 CRM（Frappe CRM 移植）

FastHTML 移植版 Frappe CRM：线索、看板交易管道、联系人、组织、任务、活动流 + 实时 AI 助手。要点（详见 [`03-FastCRM/README.md`](03-FastCRM/README.md)）：

- **HTMX 风格交互**：纯 Python 产出「服务端 + HTMX」体验，无 JS 框架。
- **共享认证模块**：`web/account_auth.py` 的 `AccountStore` + 登录弹窗，启动时 `ensure_account()` 种入「已验证」演示账号，并带「Use demo account」一键登录——04/05/06 复用同一套。
- **确定性合成数据**：`seed.py` 生成合成数据，无真实 PII。
- **`_bootstrap_db()` 导入顺序**：多表依赖下的建库/灌数顺序约束，克隆时必读。
- **PyInstaller 打包要点**：跨文件路由 + 资源数据的单文件打包经验。

---

## `04-FastERP/` — ERP（predictivelabsai/FastERP 上游完整版）

FastHTML 移植版 ERPNext，Intuit 风格自包含会计工作区：Order-to-Cash、Procure-to-Stock、库存与会计 + AI 助手；**上游完整版**（含 `fasterp` 业务包 + `migrations/` SAP 迁移模块）。要点（详见 [`04-FastERP/README.md`](04-FastERP/README.md)）：

- **端口分离**：主应用 `@5011`，集成 API `api_app.py` `@5012`，演示「业务 + 集成」双服务布局。
- **完整业务包 + SAP 迁移**：`fasterp/` 域包 + `migration/` + `migrations/`（PostgreSQL 可选，设 `DB_URL` 启用）。
- **会计领域建模**：发票/收款/库存/总账的领域对象与流转，适合做领域驱动桌面应用的参考。
- **共享认证 + 演示账号**：同 03，复用 `web/account_auth.py`（本地修复离线注册/登录）。
- **合成演示公司**：确定性会计数据，演示性软件非生产记账系统。

---

## `05-FastHRM/` — HR 系统（predictivelabsai/FastHRM 上游完整版）

FastHTML 移植版 Frappe HR，在三大支柱（人/时间/薪）基础上，**上游完整版**还含完整的 **ATS 招聘 + 人才平台 + 员工生命周期**模块。要点（详见 [`05-FastHRM/README.md`](05-FastHRM/README.md)）：

- **三大支柱模块化**：员工目录 + 部门树、请假/考勤流转、工资单计算，模块边界清晰。
- **ATS 招聘 + 人才平台**：候选人漏斗、职位申请、面试评分、Offer；能力模型、绩效目标、OKR、反馈、生命周期/入职/离职。
- **版本化迁移**：schema 由 `migrations/*.sql` 管理，`db.migrate()` 按序应用。
- **共享认证 + 演示账号**：同 03，复用 `web/account_auth.py`（本地修复离线注册/登录）。
- **合成数据**：`seed.py` / `seed_talent.py` / `seed_platform.py` 生成，无真实 PII。

---

## `06-FastInsights/` — BI 工具（Frappe Insights 移植）

FastHTML 移植版 Frappe Insights：合成数据仓库、Plotly 图表、已存查询、仪表盘、SQL 实验室 + AI 文本转 SQL。要点（详见 [`06-FastInsights/README.md`](06-FastInsights/README.md)）：

- **星型模型数仓**：合成零售销售数仓（事实表 + 维度表），`_bootstrap_db()` 顺序尤为关键。
- **Plotly 图表服务端渲染**：fasthtml 内联 Plotly，无需前端框架。
- **AI 文本转 SQL**：把自然语言转成查询的助手接线方式，可抠走。
- **共享认证 + 演示账号**：同 03，复用 `web/account_auth.py`。

---

---

## `07-genui-weather/` — 生成式 UI 三件套（kafkasl/genUI 移植）

FastHTML 生成式 UI 三件套（weather / your_color / hal9000），用 Claude 根据提示词生成 fasthtml UI。要点（详见 [`07-genui-weather/README.md`](07-genui-weather/README.md)）：

- **完整克隆 + 仅加桌面壳**：上游 `serve()` 用 fasthtml 默认端口 5001，桌面壳只做「拉起服务 + 开窗 + 缺 Key 时走上游报错」的最小包裹，不侵入任何上游业务代码。
- **生成式 UI 的最小桌面化范式**：三套 demo 共用同一套「Claude 生成 UI」上游，克隆即跑；缺 `ANTHROPIC_API_KEY` 时页面可开、发起对话才报错（上游行为，非缺陷）。
- **可借鉴**：生成式 / AI 类应用「不动上游、只外包桌面壳」的克隆手法，迁移成本最低。

---

## `08-code-assistant/` — AI 代码助手（phact/code-assistant 移植）

FastHTML AI 代码助手：根据自然语言描述生成可运行的 FastHTML Web 应用并预览。要点（详见 [`08-code-assistant/README.md`](08-code-assistant/README.md)）：

- **源码 vendoring 而非 pip 安装**：上游以 pip 包发布，本示例把 `code_assistant/` 整个包 vendor 进目录，桌面壳直接 `python -m code_assistant.code_assistant` 拉起——避免版本漂移、锁定即用。
- **多厂商模型接入（`providers_ext.py`）**：把 **DeepSeek / OpenRouter / Agnes 2** 接入厂商下拉，并 monkey-patch `litellm.get_llm_provider` 与 `astra_assistants.patch.get_headers_for_model`，让 litellm 认识 `agnes2/` 前缀（OpenAI 兼容占位，`AGNES_API_BASE` 由用户填 base URL）；`scripts/verify_providers.py` 全 PASS。
- **版本互斥隔离环境**：上游锁 `python-fasthtml==0.5.1`，与 03-06 的 `>=0.12.0` 数学上不可共存 → 走 `ISOLATED_VENV`（目录外 `%LOCALAPPDATA%/fasthtml-desktop/venvs/08-code-assistant`），全局 `site-packages` 零改动、技能目录不膨胀。
- **Key 弹窗健壮性**：针对 htmx 2.x 局部刷新不执行内联 `<script>`，用 `setInterval` 轮询兜底打开 Key 弹窗，桌面 WebView2 环境不再白屏。

---

## `09-FastSheets/` — 电子表格（Frappe Sheets 移植）

FastHTML 移植版 Frappe Sheets：可编辑网格 + 真实公式引擎（SUM/AVERAGE/MIN/MAX/引用/算术）、多工作表、AI 助手（基于计算值）。要点（详见 [`09-FastSheets/README.md`](09-FastSheets/README.md)）：

- **公式引擎服务端求值**：`engine.py` 实现单元格公式解析与求值，fasthtml 仅做渲染与交互。
- **共享认证 + 离线注册/登录修复**：同 03，复用 `web/account_auth.py`；本批统一修复「无邮件通道时注册 400 / 登录 401」的离线缺陷（见下方「登录与注册修复」）。
- **合成演示数据**：`seed.py` 生成示例工作表，无真实 PII。
- **FastOffice 套件 SSO**：`web/suite_auth.py` 支持套票兑换（`redeem(token, audience)`），与 10/11 同源。

---

## `10-FastSlides/` — 演示文稿（Frappe Slides 移植）

FastHTML 移植版 Frappe Slides：幻灯片库、编辑器、演示模式、AI 从提示词生成幻灯片。要点（详见 [`10-FastSlides/README.md`](10-FastSlides/README.md)）：

- **幻灯片编辑器 + 演示模式**：编辑与放映分离的双视图，fasthtml 组件化渲染。
- **共享认证 + 离线注册/登录修复**：同 03/09，复用 `web/account_auth.py`。
- **AI 生成**：从提示词生成整份演示文稿（需 LLM Key）。

---

## `11-FastDrive/` — 文件管理（Frappe Drive 移植）

FastHTML 移植版 Frappe Drive：文件/文件夹浏览器（面包屑）、共享/星标/最近/回收站视图、文件详情（分享 + 活动）、上传、AI 助手（基于合成树）。要点（详见 [`11-FastDrive/README.md`](11-FastDrive/README.md)）：

- **文件树浏览 + 视图分区**：breadcrumbs + shared/starred/recent/trash 多视图，适合做树形/资源型桌面应用参考。
- **共享认证 + 离线注册/登录修复**：同 03/09/10，复用 `web/account_auth.py`。
- **合成文件树**：`seed.py` 生成演示目录树，无真实文件。

---

## `12-FastLegal/` — 法务 AI（predictivelabsai/FastLegal 移植）

FastHTML + MonsterUI 的法务工作台（上游代号 OpenHarvey）：AI 助手、项目、表格化审阅（Tabular Reviews）、工作流、账户。要点（详见 [`12-FastLegal/README.md`](12-FastLegal/README.md)）：

- **PostgreSQL → SQLite 落地范式**：上游用 `psycopg2` + PG；本示例把 `db.py` 换成 SQLAlchemy SQLite 后端，零外部服务、双击即跑。要还原上游行为只需装回 `psycopg2-binary` 并设 `DB_URL=postgresql://...`。
- **自有认证（非 `account_auth` 体系）**：`bcrypt` 口令散列 + 服务端会话，`POST /login` 用 `HX-Redirect` 跳转（不是 303），`POST /signup` 注册即登录——这是 03–11 之外的第二种登录范式。
- **LLM SDK 懒加载**：`llm.py` 的 `get_chat_model()` 在**函数内**才 `import langchain_openai / langchain_anthropic / langchain_google_genai`，因此三个供应商包**不列入 `requirements.txt` 必需项**，离线首启不会被迫拉取重型依赖树。业务路由完全不依赖它们。
- **独立桌面壳 `desktop.py`**：上游 `main.py` 只在 `__main__` 里起服务，故外挂 `desktop.py` 承担「重定向库路径 → 建库播种 → uvicorn 线程 → pywebview 窗口」，`SERVER_ONLY=1` 走无头。`launcher.py` 通过 `launcher.json` 的 `entry:"desktop.py"` 指向它。

---

## `13-FastLMS/` — 在线教育 LMS（predictivelabsai/FastLMS 移植）

FastHTML + FastAPI 混合的学习管理系统：课程目录、课时、测验、AI 答疑、排行榜、讲师后台、多校区（School）管理。要点（详见 [`13-FastLMS/README.md`](13-FastLMS/README.md)）：

- **`SCHEMA="main"` 迁移技巧（本批最有价值的一招）**：上游全库 SQL 都写成 `{S}.courses` 这类 **schema 限定名**（160+ 处）。SQLite 内置 `main` 别名恰好等价于 PG 的 schema 名，于是只需把 `SCHEMA = os.environ.get("FASTLMS_SCHEMA") or "main"`，**一处改动即让全部限定名原样生效**，无需逐条改写 SQL。DDL 侧再做类型翻译（`SERIAL`→`INTEGER PRIMARY KEY AUTOINCREMENT`、`TIMESTAMPTZ`→`TIMESTAMP`、`JSONB`→`TEXT`、`now()`→`CURRENT_TIMESTAMP`）。
- **SQLite 日期类型适配**：`_register_sqlite_types()` 注册 `date/datetime` 适配器与转换器 + `PARSE_DECLTYPES`，补齐 Python 3.12+ 移除的默认适配器，避免读回来变字符串。
- **双认证并存**：登录弹窗走 `account_auth` 的 `/auth/local/login`（演示账号 `admin@fastlms.example`），上游原生 `/auth/login` 走自有用户表（`instructor@fastlms.dev` / `student@fastlms.dev`，口令均 `admin`，由 `seed.py` 播种）。两套互不干扰，`dev_check.py` 两条路径都验。
- **FastAPI 装饰器 + FastHTML 渲染**：`app = FastHTML(...)` 之后用 `@app.get/@app.post` 而非 `@rt`，返回 FT 对象由 FastHTML 渲染——混合范式参考。

---

## `14-FastMeet/` — 会议协作（predictivelabsai/FastMeet 移植）

FastHTML 会议应用：日程、会议详情与 RSVP、会议室（含实时聊天）、AI 议程/纪要生成。要点（详见 [`14-FastMeet/README.md`](14-FastMeet/README.md)）：

- **`db_exists()` 播种守卫的经典坑（已修）**：`web/api.py` 在 **import 期**就调用 `db.init_schema()`，于是全新安装时库文件已被创建（空表），随后 `_ensure_db()` 的 `if not db.db_exists()` 恒为假 → **演示数据永远不播种**，界面全空。修法是把守卫从「库文件是否存在」改成「关键表是否有数据」。这个坑在「import 副作用建库 + 文件存在性判断」的组合下极易复现，克隆同类项目时优先自查。
- **raw `sqlite3` 后端**：不经 ORM，`db.py` 直接 `sqlite3.connect(DB_PATH, timeout=10)`，`FASTMEET_DB` 环境变量可重定向——桌面壳据此把库落到 `data/`。
- **`fast_app` + 子应用挂载**：`app, rt = fast_app(...)` 后 `app.mount("/api", api)`，演示「页面路由 + REST 子应用」共存。
- **登录弹窗 + 原生 `/login` 并存**：与 13 同构，`dev_check.py` 两套都覆盖（23 项全绿）。

---

## `15-FastMail/` — 邮件客户端（predictivelabsai/FastMail 移植）

FastHTML 邮件客户端：收件箱/已发送/归档、星标、标签、联系人、日历、写信与发送、AI 摘要与草稿。要点（详见 [`15-FastMail/README.md`](15-FastMail/README.md)）：

- **与 14 同源同构**：同样的 raw `sqlite3` + `fast_app` + `mount("/api")` + 双登录范式，同样中了「import 期建库致播种守卫失效」的坑并同法修复——两者对照阅读，可快速掌握这套上游模板的通用改造手法。
- **多视图资源型 UI**：文件夹（Inbox/Sent/Archive）× 标签 × 星标 × 日历的多维过滤，是做「列表 + 详情 + 侧栏筛选」类桌面应用的现成骨架。
- **`FASTMAIL_DB` 重定向**：桌面壳把邮箱库与账号库一并落到 `data/`，`dev_check.py` 另用独立 `devcheck.sqlite`，不污染用户数据。
- **门禁最全**：`dev_check.py` 25 项，覆盖注册→登录→未登录拦截→7 条业务视图→邮件详情→演示邮件播种计数。

---

## `16-FastDocs/` — 文档编辑器（predictivelabsai/FastDocs = Frappe Writer 移植）

FastHTML 服务端渲染、HTMX 驱动的文档编辑器（Frappe Writer 的精简移植）：文件夹式文档库、块编辑器（标题/列表/引用/代码，每块即 Markdown）、可复用模板（会议纪要/项目简报/博客）、版本历史快照与回滚、只读公开分享链接、多供应商 AI 写作助手（从提示词起草整篇文档）。要点（详见 [`16-FastDocs/README.md`](16-FastDocs/README.md)）：

- **块编辑器 + HTMX 片段交换**：增删改/移动块全是 HTMX fragment swap，无整页刷新、无前端框架。
- **共享认证 + 离线注册/登录修复**：同 03，复用 `web/account_auth.py`；本批统一修复「无邮件通道时注册 400 / 登录 401」的离线缺陷（见下方「登录与注册修复」）。
- **合成文档数据**：`seed.py` 生成确定性文档库，无真实 PII；首次启动 `_ensure_db()` 幂等播种。
- **独立桌面壳 `desktop.py`**：上游 `web_app.py` 末尾 `serve()` 在 import 期是空操作，故外挂 `desktop.py` 承担「重定向库路径 → 建库播种 → uvicorn 线程 → pywebview 窗口」，`SERVER_ONLY=1` 走无头。`launcher.py` 通过 `launcher.json` 的 `entry:"desktop.py"` 指向它。

---

## `17-FastESM/` — 企业服务管理 ESM（predictivelabsai/FastESM 移植）

FastHTML 服务端渲染、HTMX 驱动的 **企业服务管理（ESM = ITSM 跨全部门扩展）** 平台：像网店一样浏览请求的**服务目录**、审批→履行工作流 + 实时 **SLA 计时器**的请求编排、**RBAC** 角色视图（Employee / Agent / Manager / Admin）、**知识库**、配置驱动的**表单 & 工作流设计器**、Plotly 看板、基于检索的 AI 助手。要点（详见 [`17-FastESM/README.md`](17-FastESM/README.md)）：

- **ITSM → ESM 横向扩展**：把工单/SLA 模型从 IT 延伸到 HR/设施/财务等全部门，是做「统一服务台」类应用的参考。
- **配置驱动设计器**：表单字段与工作流步骤由配置驱动，运行时可改，是低代码桌面的范式。
- **共享认证 + 离线注册/登录修复**：同 03/16，复用 `web/account_auth.py`。
- **独立桌面壳 `desktop.py`**：与 16 同构，`entry:"desktop.py"` 指向。

---

## `18-FastMSR/` — 按揭服务权管理（predictivelabsai/FastMSR 移植）

FastHTML 服务端渲染、HTMX 驱动的**按揭服务权（MSR）管理驾驶舱**：贷款组合（loan-tape）、简易 **DCF 估值引擎**（含利率冲击情景）、模拟 **Freddie Mac Cash-Released XChange（CRX）** 竞价交易所、服务权转让工作流、合规/风险、完整 **RBAC 审计轨迹**。要点（详见 [`18-FastMSR/README.md`](18-FastMSR/README.md)）：

- **DCF 估值引擎 + 情景**：服务端 Python 实现利率冲击下的 MSR 估值，可抠走做金融计算类应用。
- **模拟交易所**：CRX 竞价为本地定价模型模拟（无外部连接），演示「撮合/竞价」交互。
- **共享认证 + 离线注册/登录修复**：同 03/16，复用 `web/account_auth.py`。
- **独立桌面壳 `desktop.py`**：与 16 同构，`entry:"desktop.py"` 指向；无外部服务依赖，SQLite 离线可跑。

---

## `19-open-docflow/` — 文档工作流（predictivelabsai/open-docflow 移植，PostgreSQL→SQLite）

FastHTML 文档工作流引擎：文档上传（PDF/DOCX）、状态流转（Gautas 收到 → Perziurimas 审阅 → Patvirtintas 批准 / Atmestas 驳回）、按状态汇总统计、按类型/日期/状态检索、带审计追踪的文档详情、状态迁移校验。要点（详见 [`19-open-docflow/README.md`](19-open-docflow/README.md)）：

- **PostgreSQL → SQLite 落地范式**：上游用 `psycopg2` + PG；本示例把 `src/models.py` 换成 SQLAlchemy SQLite 后端（含 `metadata` 保留名冲突修复 → 改名为 `doc_metadata`，DB 列仍 `metadata`），零外部服务、双击即跑。要还原上游行为只需装回 `psycopg2-binary` 并设 `DB_URL=postgresql://...`。
- **修复上游两处 bug**：① 原 `app.py` 在 `CSS` 定义前就用 `Style(CSS)` 调 `fast_app`，import 期 `NameError` —— 收敛为唯一一次 `fast_app` 调用并接入认证层；② `doc.metadata` 保留名冲突 —— 改为 `doc.doc_metadata`。
- **共享认证 + 离线注册/登录修复**：同 03/16，复用 `web/account_auth.py`；`Beforeware` 登录门（未登录访问业务路由 → 303 跳 `/login`）。
- **示例数据播种**：首次启动空表自动 `generate_documents(200)` 播种（演示数据落 `data/`）。
- **质量门禁最全**：`dev_check.py` 17 项，覆盖注册→登录→拦截→业务路由→文档详情→状态流转→空执行人拦截，全绿。
- **独立桌面壳 `desktop.py`**：与 16 同构，`entry:"desktop.py"` 指向，`UPLOAD_DIR` 可重定向到 `data/uploads`。

---

## `20-FastHelpdesk/` — 客服工单台（predictivelabsai/FastHelpdesk = Frappe Helpdesk 移植）

FastHTML 服务端渲染、HTMX 驱动的**客服台**（Frappe Helpdesk 精简移植）：带实时 **SLA 计时器**的工单队列、线程式工单会话、客服与团队、知识库、客户、**基于实时（合成）队列检索的 AI 助手**。要点（详见 [`20-FastHelpdesk/README.md`](20-FastHelpdesk/README.md)）：

- **工单 + 实时 SLA**：队列视图 + 会话线程 + 实时倒计时，是做「支持台/工单系统」类应用的现成骨架。
- **共享认证 + 离线注册/登录修复**：同 03/16，复用 `web/account_auth.py`。
- **合成队列数据**：`seed.py` 生成确定性工单与客户，无真实 PII。
- **独立桌面壳 `desktop.py`**：与 16 同构，`entry:"desktop.py"` 指向。

---

## 登录与注册修复（03–11、13–15、16–20 通用）

上游 `web/account_auth.py` 的注册/登录依赖 Postmark 邮件验证：离线（无 `POSTMARK_API_TOKEN` / `FROM_EMAIL`）时 `register()` 因发不出验证邮件返回 400，`login()` 因账号永远 `is_verified=0` 返回 401，且 `forgot()` 无邮件通道时无重置链接。本批统一修复：

- **注册离线即验证**：`register()` 在 `_send_action()` 失败（无邮件通道）时，直接将账号置 `is_verified=1` 并返回「Account created — you can sign in right away.」，注册即可登录（有 Postmark 时仍走邮件验证，行为不变）。
- **登录放开**：`login()` 对已注册本地账号（`is_verified=1`）正常放行。
- **找回密码离线回退**：`forgot()` 在无法发邮件时直接返回本地重置链接（`/auth/local/reset/{token}`），前端展示该链接，可离线完成重置。
- **演示账号一键登录**：`web_app.py`（13 为 `main.py`）启动时 `ensure_account(VALID_EMAIL, VALID_PASSWORD, verified=True)` 种入已验证演示账号并 `set_demo_credentials(...)`，登录弹窗带「Use demo account」按钮。
- 修复以同一份 canonical `account_auth.py` 分发至 **03、04、05、06、09、10、11、13、14、15、16、17、18、19、20 共 15 份**；端到端（TestClient）与 `dev_check.py` 质量门禁均验证通过（注册→200→登录→200+跳转、演示账号登录→200、找回密码→返回本地链接）。各示例的演示账号由 `ensure_account(..., verified=True)` 种入，登录弹窗「Use demo account」一键带出（具体账号见各子目录 README）。

## 跨示例可复用设计模式

做自己的 fasthtml 桌面应用时，以下零件在多个示例间通用，可直接复用：

- **两层启动器**：`启动.bat`（≤10 行派发壳，GBK+CRLF）→ `launcher.py`（决策层：**解析 `requirements.txt` 全量预检**、降级防护、WebView2 检测、tee 日志、拉起入口）。`launcher.py server` 无头运行、`launcher.py --check` 只体检不启动。两者均由 `scripts/gen_launchers.py` 分发（引擎 `templates/shared/launcher.py` + 每例 `launcher.json`），**禁止手写、禁止在 bat 里写决策逻辑、禁止只预检模块子集**（曾因写死 `fasthtml/webview/uvicorn` 三项而放行缺 `fastapi`/`requests` 的环境）。
- **本地桌面架构**：pywebview 窗口 + 本地 FastAPI + 本地 SQLite，完全离线，无服务器依赖。
- **独立桌面壳 `desktop.py`（12–15）**：当上游入口只在 `if __name__ == "__main__"` 里起服务、或 import 即建库时，不要改上游，外挂 `desktop.py`：重定向库路径到 `data/` → `build_app()` 建库播种并返回 app → uvicorn 线程 + `find_free_port()` + `wait_for_server()` → pywebview 包裹（`import webview` 放在函数内，便于 `dev_check.py` 无 GUI 复用）。配套在 `gen_launchers.py` 的 `launcher.json` 里声明 `entry:"desktop.py"`——`launcher.py` 的入口自动探测只认 `src/main.py`/`main.py`。
- **共享认证模块 `account_auth.py`**：`AccountStore` + 登录弹窗 + `ensure_account()` 种演示账号 + 「Use demo account」一键登录（03–06、09–11、13–15 通用；含离线注册/登录/找回密码修复）。
- **`dev_check.py` 质量门禁**：Starlette `TestClient` 进程内验证「未登录拦截 → 错误口令拒绝 → 正确口令跳转 → 注册 → 业务路由全绿 → 演示数据已播种」，**必须 `follow_redirects=False`**（否则 303 被自动跟随成 200，形成假绿）；用独立库文件避免污染用户 `data/`。交付前必须跑到 `[GATE] 全部通过`。
