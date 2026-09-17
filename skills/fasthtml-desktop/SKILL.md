---
name: fasthtml-desktop
description: >
  FastHTML + pywebview 桌面应用的全生命周期技能。覆盖从需求澄清、FastHTML Web 开发、
  pywebview 桌面壳包装到 PyInstaller 打包交付的完整链路。
  最终交付物是包含 pywebview 原生窗口的 FastHTML 桌面 EXE（WebView2 渲染，本地 HTTP 服务）。
  当用户提到"fasthtml""pywebview""Web 桌面""HTMX 界面""本地 HTTP 服务"
  "带原生窗口的 Web 应用""pywebview 打包"时使用本技能。
version: "1.12.0"
author: agent
agent_created: true
platform: multi
license: MIT

metadata:
  openclaw:
    requires:
      bins:
        - python
    homepage: https://github.com/kuailexiaozixin/fasthtml-desktop
    emoji: "🖥️"
---


# fasthtml-desktop

***

## HARD-GATE：必须先读 fasthtml-llms-ctx.txt（不可跳过）

**写任何 FastHTML 代码前，必须先读** **`references/05-coding/fasthtml-refs/fasthtml-llms-ctx.txt`。**

该文件是 FastHTML 官方 LLMs 上下文文件（约 10,100 行），覆盖所有 API 签名、路由模式、FastTags、HTMX 集成等。**写任何代码前必须阅读**，阅读后聚焦本任务相关的关键结论、API 签名/组件、以及与 FastAPI 的语法差异；否则 API 使用错误、组件属性遗漏、路径映射失败。

**必须按工作流制定任务计划，不得跳过任何步骤，不得漏步骤未执行。** 尤其重视 ⑦ 质量门禁的三个阶段（持续验证→全面验证→预发布门禁），每个阶段中的所有检查项均须执行通过，不可省略。

***

## 排障

> **排障指南（问题沉淀首选）**：`./docs/troubleshooting.md` —— 执行过程中发现的问题（现象、本质）及解决办法，**优先沉淀到此文件**，除非是特别重要的主干内容。SKILL.md 只保留铁律/规则本身，踩坑叙事与排障步骤迁入 troubleshooting.md。

***

## 完整工作流与分步执行详解（= 后续 AI 的唯一执行清单）

> 本流程即后续 AI 的唯一执行清单，按 ①→⑨ 顺序执行，**不可跳过、不可乱序**。每个步骤内联必读参考、复用要点、产出物与验收标准，**铁律直接写在本步骤内**——没有独立的"铁律章节"，读到哪步执行哪步的规则。须读完并执行完本步骤全部内容后再进入下一步，**不得跳过任一字段**。

### 分支：新建项目 / 已有项目

用户说"帮我做个桌面工具"时，先判断是新建项目还是已有项目：

* **新建项目** → 按下方 ①→⑨ 完整流程执行。
* **已有项目** → 跳过 ①-④，执行结构合规检查：
  1. 检查 src/ 下存在 app.py 或 <pkg>/app.py
  2. 检查 src/main.py 是否存在且入口正确
  3. 检查 启动.bat / launcher.json / requirements.txt（或 pyproject.toml）是否存在（依赖装进项目 venv，由 launcher.json 的 use_venv 管理，不污染用户全局环境）
  4. 检查 pyproject.toml 依赖是否完整
  5. 检查界面渲染与交互（图标/重叠/对比度/空白页等）
  合规检查通过后 → 进入 ⑤ 编码（界面与业务一体）；界面观感完善与视觉质检走 ⑥。

### ① 需求澄清

* **任务**：问清楚做什么、输入输出、给谁用；产出需求优先级表。
* **必读**：`references/01-need-discovery.md`（首轮话术、必问问题、可测试验收标准捕获）。
* **复用**：扫 `examples/README.md`，若已有同类业务场景（CRM/ERP/表格/文件管理等）直接复用其业务建模与入口范式，非必要不自造轮子。
* **要点**：同时捕获**可测试验收标准**（输入/输出/边界/异常路径），作为 ⑤ 测试与 ⑨ 验收的依据。
* **产出物**：需求优先级表（MoSCoW 分级）。
* **验收标准**：Must/Should/Could/Won't 已分级，MVP 清单已确认。

### ② 架构设计

* **任务**：定 MVP 边界；**定骨架（几层、哪几个业务域、域间依赖方向，建筑结构图）**；**定域内细节（每域功能清单、接口契约、数据流，房间布置图）**；**数据模型与状态机前置**；**完成界面设计活动（信息架构、布局决策、设计系统选型）**。
* **必读**：`references/02-architecture/INDEX.md`（模块设计 + 18 章导航）。按项目复杂度选读章节：
  * 简单项目：`references/02-architecture/01-system-context.md`（系统上下文与边界）、`references/02-architecture/10-checklist.md`（设计检查清单）、`references/02-architecture/17-mvp-boundary.md`（MVP 边界表）
  * 中等复杂度：另加 `references/02-architecture/03-module-decomposition.md`（模块分解）、`references/02-architecture/05-interface-design.md`（接口设计）、`references/02-architecture/07-scenario-driven.md`（场景驱动的架构类型选择）、`references/02-architecture/04-data-architecture.md`（数据架构）、`references/02-architecture/12-state-machine.md`（状态机）
  * 复杂企业应用：01-18 全部章节（02 核心业务流 `references/02-architecture/02-business-flow.md` / 06 统一架构框架 `references/02-architecture/06-unified-framework.md` / 08 ADR `references/02-architecture/08-adr.md` / 09 常见架构错误 `references/02-architecture/09-common-mistakes.md` / 11 架构模式选型 `references/02-architecture/11-pattern-selection.md` / 13 存储选择 `references/02-architecture/13-storage-selection.md` / 14 技术债 `references/02-architecture/14-tech-debt.md` / 15 错误处理 `references/02-architecture/15-error-handling.md` / 16 非功能设计 `references/02-architecture/16-non-functional.md` / 18 图生成指南 `references/02-architecture/18-diagram-guide.md`）
  * 界面设计活动：`references/05-coding/ui-design.md`（信息架构 / 布局决策 / CSS 框架与设计系统选型）
* **复用**：先看 `examples/` 同类应用的架构（**分层模块化：`web/` 表示层 + 业务域包 + `db.py` 数据层，参照 `examples/04-FastERP/`**；插件化；入口壳（`templates/shared/main.py`）等），直接套用成熟范式，不重新发明。
* **铁律（架构选型：服务端渲染约束，选型前必读）**：FastHTML 是**服务端渲染**框架——HTML 由 uvicorn 按请求实时生成，**磁盘上无静态 HTML 入口文件**。
  * **禁用依赖静态 HTML 入口的工具**（注入式质检、`/live` 热重载、SSR 预渲染等）。
  * **正确路径是「真实渲染引擎」驱动**：用 pywebview 原生窗口质检与自动化（`scripts/ui_window_verify.py`、`scripts/ui_automate.py`），无需第二个浏览器；无 GUI 时用 headless HTML 审计（`scripts/ui_audit.py`）。两者都**非**解析静态 HTML。
  * pywebview 导入/启动、质检脚本用法、DOM 断言检查能力、像素截图等技术要点见 `references/07-quality-gate/Test/04-ui-tools.md`。
* **铁律（架构分层）**：所有项目强制按**表示层（UI/视图）→ 业务层（逻辑）→ 数据层（存储）** 三层分层，依赖方向**单向自上而下**，禁止跨层调用、禁止反向依赖：

  ```
  表示层（FastHTML 视图 / HTMX 组件 / 路由）
          │  只调业务层接口，不直接读写数据库
          ▼
  业务层（业务逻辑 / 用例编排 / 校验）
          │  只调数据层 Repository，不依赖 FastHTML UI 细节
          ▼
  数据层（SQLite / Repository / 存储）
  ```

  * **模块化（业务域优先）**：按**业务域**拆分模块（如 `sales`、`purchasing`、`inventory`、`accounting`，参照 `examples/04-FastERP/fasterp/`），技术横切（auth / config / errors）为第二维度；每个模块高内聚（只做自己的事）、低耦合（模块间只经显式接口通信，禁止互相 import 内部实现）。
  * **关注点分离**：UI（渲染/交互）、业务逻辑、数据访问、配置读取、日志各自独立成层，禁止把 SQL 写在视图里、把业务规则写在路由里。
  * **高内聚低耦合**：一个模块/类只承担单一职责；依赖通过接口或函数注入，不产生循环依赖；公共逻辑抽到 `common/` 或 `utils/` 复用，消除 copy-paste。
  * **数据模型与状态机前置**：对数据管理型项目，架构设计的核心不是抽象分层，而是**表结构与状态流转**——表结构清单 + 状态机定义（如订单 Draft→Confirmed→Delivered→Invoiced→Closed、发票 Unpaid→Partly Paid→Paid→Overdue）列在产出物首位。数据模型定了，界面和业务函数都是它的投影（参照 FastERP：`db.py` 表结构 + 状态流转即价值重心）。
  * **接口契约即测试契约**：每个契约点直接落成 **pytest 骨架文件**——契约、测试、实现三者在编码阶段同步演进（参照 FastERP：`tests/test_accounting.py`、`tests/test_api.py` 对着业务域接口写）。
  * **设计活动内联**：页面结构清单（每页有哪些元素）、布局决策、CSS 框架与设计系统选型在本阶段确定，编码时直接实现，不单独制作原型文件。
* **产出物**：`docs/architecture.md`（MVP 边界表 + **表结构清单 + 状态机定义** + 分层与业务域骨架 + 每域功能清单与接口契约 + 数据流图 + **页面结构清单** + **pytest 接口骨架文件**）。
* **验收标准**：含 MVP 边界表 + 数据模型与状态机 + 模块分解 + 接口契约 + 业务流图 + 页面结构清单 + pytest 接口骨架。

### ③ 环境准备

* **任务**：安装 uv、配置镜像、安装 Python、创建虚拟环境。
* **必读**：`references/03-environment.md`（环境初始化 / 依赖管理 / pywebview 版本验证 / 命令代执行规则）。
* **执行**：先跑 `scripts/ensure_uv_env.sh`（或 `.ps1`），任何新建项目第一步，禁止跳过。
* **铁律**：
  * **环境先行**：任何新建项目前，**必须率先运行** `./scripts/ensure_uv_env.sh`（优先）或 `./scripts/ensure_uv_env.ps1`，**禁止跳过**。> `.sh` 版本是对 `.ps1` 的包装（通过 `dash -c powershell.exe` 间接调用），AI 默认执行 `.sh` 版本。无 `dash` 环境时可用 tclsh 替代
  * **必须创建最小 venv**：项目目录创建后，立即 `python -m venv .venv`，否则打包体积膨胀（16MB → 154MB 的差距）
  * **依赖管理分级**：运行时业务依赖用 `uv add <包名>` 写入 `pyproject.toml`；**构建期工具**（PyInstaller、pythonnet 等）**严禁写入运行时依赖**——用 `uv pip install --python <build-venv>/Scripts/python.exe <包名>` 装进独立打包 venv（参考 `references/08-packaging/deep-dive.md` 最小 venv 章节）。**既不要用 `uv add`（会污染运行时依赖），也不要在业务 venv 裸用 `pip install`。**
  * **中国网络环境**：涉及 uv、Python 与包安装时，默认先设置镜像（`uv config set index-url https://mirrors.aliyun.com/pypi/simple/`）再执行。
* **命令代执行规则**：`uv init`、`uv add`、`uv sync`、`uv run`、`ruff`、`mypy`、`pytest`、`pyinstaller` 默认由 AI 发起；运行命令需要系统授权、联网安装或写文件时 AI 负责发起；除非用户明确要求学习命令行，否则不要把"请你在终端执行以下命令"当成默认答案。
* **命令执行与超时**：`run_command` 默认超时 120s；**可能 >120s 的操作必须显式传 `timeout=600` 或后台运行**（构建尤其如此）；**失败即拆步**——超时则拆成更小步骤，每步独立可验证。
* **产出物**：uv + Python + 镜像已配置。
* **验收标准**：`uv --version` 正常输出。

### ④ 项目初始化

* **任务**：生成 web-desktop-exe 骨架 → `uv add` 补业务依赖 → `uv sync`。
* **必读**：`references/04-project-init.md`（一键启动器完整规则 + 项目初始化流程）。
* **执行**：跑 `scripts/bootstrap_project.sh`（或 `.ps1`）生成骨架，禁止从零手写 pyproject.toml。
* **铁律**：
  * **必须跑 bootstrap 脚本**：新建项目必须运行 `./scripts/bootstrap_project.sh`（优先）或 `./scripts/bootstrap_project.ps1` 生成骨架。**禁止从零手写 pyproject.toml 或逐级 mkdir**；**必须先有骨架再写代码**——骨架落地前，禁止开始写任何 .py 业务代码。
  * **标准交付物（每个 f-d 项目必备）**：骨架 + `.gitignore` + `.env.example` + **`启动.bat`（一键双击启动器）** + **`launcher.py`（一键启动决策层，双击后端的唯一逻辑源）+ `launcher.json`（启动配置）** + **双用途 `README.md`（用户说明书 + LLM 克隆说明书）** + `requirements.txt`（启动.bat 装依赖用）。
  * **启动器铁律（场景分叉）**：开发工作流（真实项目）与 examples（演示语料）的环境/依赖策略**全部相反**，禁止互相套用启动器。要点：
    * **bat 只派发，Python 做决策**：`启动.bat`（≤8 行，GBK+CRLF）只交权给 `launcher.py`，严禁在 batch 里写决策逻辑。
    * **逐条解析 `requirements.txt` 预检**，禁止写死模块名子集。
    * **禁止降级用户已装包**；**禁止 `os.execv`**（Windows 路径含空格必炸，用 `subprocess.call` + `sys.exit`）。
    * **`启动.bat` 必须 GBK/ANSI + CRLF**。
    * README 双用途：用户说明书 + LLM 克隆说明书。
    * 启动器通过 `launcher.json` 的 `use_venv=true` 在**项目目录内建最小 `.venv`** 并 re-exec 进去（隔离优先、不污染用户全局环境）→ 首次运行预检依赖，缺失则 `pip install` 到该 venv → 启动 main.py 弹桌面窗口；普通用户双击即用，无需终端。**`.py` 双击默认用编辑器打开不会运行**，故用户入口统一是 `启动.bat`，`start.py` 仅作开发者 CLI。
    * `templates/shared/launcher.py` 是配置驱动的参考引擎（`launcher.json` 管差异，`gen_launchers.py` 统一分发），也可按铁律自行编写。examples 策略见 `examples/README.md` §启动器策略。
* **警告**：骨架用 bootstrap 脚本，逐文件 Write，禁单条巨命令。
* **产出物**：可双击 `启动.bat` 的完整骨架。
* **验收标准**：双击 `启动.bat` 自动建项目 venv 并装依赖启动（依赖装进项目内 venv，`use_venv=true`，不污染全局 Python）；`uv sync` 成功。

### ⑤ 编码

* **任务**：按 ② 的分层骨架与接口契约编码，**界面与业务一体实现**——服务端渲染下"界面"即路由函数返回的 HTML 片段（如 `views.order_detail(oid)` 同时是界面与业务出口）；按 ② 的页面结构清单与设计系统实现布局与组件；最小可运行版本先行（先跑通空壳确认技术栈兼容，再加业务）；`src/main.py` 不动（pywebview + uvicorn 入口）。**不制作独立纯界面原型文件**。
* **必读（前置）**：`references/05-coding/fasthtml-refs/fasthtml-llms-ctx.txt`（FastHTML 官方 LLMs 上下文，写任何代码前必读）；`references/05-coding/execution-and-env.md`（编码与执行规范：PowerShell 红线 / 编码铁律 / 命令超时 / 修改后验证纪律）；`references/05-coding/ft-handlers-typing.md`（参数绑定规则）；`references/05-coding/integration-patterns.md`（fasthtml+pywebview+PyInstaller 协同）。
* **必读（按需）**：
  * `references/05-coding/ui-design.md`（界面实现：布局模板、CSS 框架选型、交互位置标注、图标处理）
  * `references/05-coding/project-structure.md`（分层模块化标准结构：web/ + 业务域包 + db.py）
  * `references/05-coding/fasthtml-refs/picocss-reference.md`（PicoCSS 参考）
  * `references/05-coding/fasthtml-refs/fastlite-llms.txt`（数据库操作时）
  * `references/05-coding/pywebview-shell.md`（pywebview 桌面壳：后端矩阵 / 窗口控制 / JS 桥接 / 对话框 / 菜单 / DOM / 拖拽 / 系统托盘）
  * `references/05-coding/fasthtml-refs/genui-hypermedia-reference.md`（GenUI 超媒体）
  * `references/05-coding/fasthtml-fastapi.md`（FastAPI 集成）
  * `references/05-coding/pywebview-examples/`（59 个已验证示例脚本，按能力域查阅）：
    * 窗口基础/生命周期：`simple_browser.py`, `multiple_windows.py`, `destroy_window.py`, `hide_window.py`, `confirm_close.py`, `window_title_change.py`, `change_url.py`, `get_current_url.py`, `http_server.py`, `localhost_ssl.py`
    * 窗口外观/行为：`frameless.py`, `transparent.py`, `fullscreen.py`, `toggle_fullscreen.py`, `on_top.py`, `min_size.py`, `resize.py`, `move_window.py`, `icon.py`, `vibrancy.py`, `window_state.py`, `state.py`, `focus.py`, `screens.py`, `loading_animation.py`, `localization.py`
    * JS 桥接 / DOM：`js_api.py`, `expose.py`, `evaluate_js.py`, `evaluate_js_async.py`, `run_js.py`, `get_elements.py`, `dom_events.py`, `dom_manipulation.py`, `dom_traversal.py`, `dom_state_dragregion_verified.py`, `load_html.py`, `load_css.py`, `headers.py`, `user_agent.py`, `settings.py`, `debug.py`, `remote_debugging.py`, `multiprocess.py`
    * 对话框 / 文件 / 下载：`open_file_dialog.py`, `save_file_dialog.py`, `confirmation_dialog.py`, `downloads.py`, `drag_drop.py`, `links.py`, `cookies.py`
    * 菜单 / 托盘 / 集成：`menu.py`, `pystray_icon.py`, `drag_region.py`, `events.py`
    * 跨平台 / 后端专用：`cef.py`, `qt_test.py`, `py2app_setup.py`, `multiple_servers.py`
* **铁律（编码）**：
  * **接口层入口必须 `reload=False`**：`uvicorn.run(app, reload=False)`，禁止 `serve()` 打包
  * **路径适配必须用 `sys.frozen` 检测**：`BASE_DIR = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent`
  * **FastHTML 组件参数顺序**：位置参数（子元素）必须在关键字参数（HTML 属性）之前。`Div(H1("标题"), cls="box")` ✅；`Div(cls="box", H1("标题"))` ❌
  * **APIRouter 必须显式声明路径**：每个路由用 `@ar("/projects/{pid}")` 显式声明路径，禁止依赖自动路由生成（函数名下划线转连字符，与手写 href 不匹配，导致全站 404）
  * **URL 一律用 127.0.0.1**：`http://127.0.0.1:{PORT}`，禁止使用 `localhost`（某些环境 localhost 解析被拦截，导致页面加载失败或白屏）
  * **uvicorn 线程必须 daemon**：`threading.Thread(target=run_server, daemon=True)`，否则关闭窗口后进程不退出
  * **编码门禁（文件编码）**：`.py` 源码一律 UTF-8 无 BOM（PEP 3120），禁止 PowerShell `Set-Content` 写源码（会乱码）；`.ps1` 一律 UTF-8 with BOM + CRLF；禁止混合 CRLF/LF 行尾（详见 `references/05-coding/execution-and-env.md`）
  * **语法检查门禁（代码发布前必跑）**：写入任何 `.py` 文件后，立即做 `py_compile.compile()` 语法验证，连同模块导入测试 `python -c "from app import app"` 一起执行，**禁止跳过**
  * **控制台输出禁止 emoji**：打包后 EXE 运行在 Windows 控制台（GBK 编码），emoji 会导致乱码。用 `[OK]` / `[FAIL]` 替代 ✅ / ❌，用 `[INFO]` / `[WARN]` / `[ERROR]` 替代图标
  * **禁止单条 shell 命令批量造文件**：源码/配置/资源文件**逐文件 Write/Edit**，严禁 `cat <<'EOF' > file` 连写多文件
* **铁律（TDD，测试驱动开发）**：先写测试，再写代码；测试不是「事后验证」，而是「事前设计」。
  * **红-绿-重构循环**：🔴 写一个失败的测试 → 🟢 写最少量的代码让测试通过 → 🔵 优化结构（测试全绿前提下重构）→ 重复循环。
  * **核心原则**：测试先行 / 小步快跑 / 测试即文档 / 回归保障。
  * **落地**：新业务模块必须 test-first（Red-Green-Refactor），**禁止「先实现后补测」**；修 bug 走 **Prove-It**（先写复现测试 → 实现修复 → 测试通过 → 跑全量防回归）；pytest 管「逻辑对不对」，绝不写脆弱的 DOM/渲染单测（那是 `ui_window_verify.py` 的职责）；每次改动后跑全量 `uv run pytest` + HTML 审计，**非零即阻断**。详见 `references/07-quality-gate/Test/01-test-driven-development.md` 与 `references/07-quality-gate/Debug/01-debug-discipline.md`。
* **复用**：写业务代码前先查 `examples/`（认证 `web/account_auth.py`、HTMX 局部刷新、FastAPI 挂载、PyInstaller hidden-import 套路），能 copy-adapt 就不重写。
* **产出物**：`src/app.py`（组装入口：fast_app + 模块注册 + 路由转发）+ `web/` 视图模块 + 业务域包 + `db.py` 数据层 + `tests/` 对应测试。
* **验收标准**：语法检查 + 导入测试 + 对应单元/集成测试存在且通过（Red-Green-Refactor，禁止先实现后补测）。

### ⑥ 界面完善与视觉质检

* **任务**：逐页打磨界面观感（布局、视觉层级、间距、对比度、状态反馈），完善交互细节；用机器视觉质检验证界面。**先编码后完善**——⑤ 产出可运行的界面+业务，本步骤负责把观感打磨到位。
* **必读**：`references/06-ui-polish.md`（完善流程 / 迭代日志 / 质检工具分工）；`references/05-coding/ui-design.md`（布局模板、设计质量评审）。
* **铁律（界面交付门禁）**：**必须用机器手段验证界面**：
  * `scripts/ui_audit.py`（反模式审计，纯 headless，13 条禁令 / AI Slop / a11y，**禁止跳过**；自动抓取 `<link rel=stylesheet>` 外部 CSS 纳入审计；可用 `--ignore-ban "禁令名/序号/子串"` 豁免已知误报）
  * `scripts/ui_window_verify.py`（pywebview 原生窗口视觉质检：DOM 断言+可选截图；无头截图自动回退 html2canvas；**HTML 结构验证通过 ≠ 界面没问题**；无 GUI 强制 HTML 结构验证）
  * `scripts/ui_automate.py`（UI 交互自动化：点击/输入/导航/断言，验证按钮/表单/状态切换等交互行为正确性）
  * 质检/自动化 **exit 1 即禁止发布**；纯主观审美不在机器范围，按需人工判断，但**不将人工截图作为验收手段**。
* **要点**：UI 行为变更须同步更新/新增测试；质检脚本详细用法见 `references/07-quality-gate/Test/04-ui-tools.md`；设计质量评审详见 `references/05-coding/ui-design.md` 审美取向方法论。
* **产出物**：完善后的界面 + 质检报告（ui_audit / ui_window_verify / ui_automate）。
* **验收标准**：机器视觉质检通过 + 反模式审计通过 + UI 交互自动化通过。

### ⑦ 质量门禁（打包前必过，三阶段按序执行）

* **总入口**：`references/07-quality-gate/INDEX.md`（Check/Test/Debug 三层心智图）。
* **Check 层（静态关卡，不运行完整应用）**，入口 `references/07-quality-gate/Check/INDEX.md`：
  * `references/07-quality-gate/Check/01-static-code-checks.md`（语法/导入/Ruff/运行验证/UI 反模式检查）
  * `references/07-quality-gate/Check/02-ui-audit.md`（`ui_audit.py` 13 条禁令 / 产品 UI 检查 / AI Slop / a11y）
  * `references/07-quality-gate/Check/03-route-hygiene.md`（路由显式化 `check_routes.py` / 前端→后端链路 `check_routes_linkage.py`）
* **Test 层（动态验证，运行真实代码路径）**，入口 `references/07-quality-gate/Test/INDEX.md`：
  * `references/07-quality-gate/Test/01-test-driven-development.md`（TDD 核心）
  * `references/07-quality-gate/Test/02-e2e.md`（业务路径 E2E + 视觉 E2E）
  * `references/07-quality-gate/Test/03-smoke-and-delivery.md`（冒烟门禁 / 打包前清单 / release_gate）
  * `references/07-quality-gate/Test/04-ui-tools.md`（`ui_audit` / `ui_headless_verify` / `ui_window_verify` / `ui_automate` 分工）
* **Debug 层（失败处理闭环，任何 Check/Test 失败后进入）**，入口 `references/07-quality-gate/Debug/INDEX.md`：`references/07-quality-gate/Debug/01-debug-discipline.md`（调试总纲 / Prove-It / Flaky / 干净复测）。
* **阶段一（持续验证，每次改代码后立即执行）**：
  * `py_compile` 语法检查 + `python -c "from app import app"` 导入测试（细则见 Check/01）
  * `uv run pytest` 单元/集成测试全绿（逻辑门禁，非零即阻断）
* **阶段二（全面验证，功能开发完成后执行）**：
  * **用 `启动.bat` 启动应用**，自测正常+异常路径
  * UI 反模式检查（`scripts/ui_audit.py`，纯 headless，禁止跳过；反模式规则详见 Check/02）
  * 机器视觉质检（`scripts/ui_window_verify.py`：DOM 断言+可选截图；HTML 结构验证通过≠界面没问题；无 GUI 强制 HTML 结构验证）
  * UI 交互自动化（`scripts/ui_automate.py`：点击/输入/导航/断言，验证交互行为正确性）
  * 测试夹具 schema 对齐：新增测试须用 `scripts/fixture_schema_helper.py` 校验 insert 键全部存在于真实 db 列（见 `docs/troubleshooting.md` 第五章）
* **阶段三（预发布门禁，打包前执行一次）**：
  * 前端→后端路由链路校验（`scripts/check_routes_linkage.py`：捕获前端引用但后端未注册的路由，防运行时 404。exit 1 = 阻断发布；规则详见 Check/03）
  * 统一发布门禁（`scripts/release_gate.py`：串联 pytest → check_routes → check_routes_linkage → UI 视觉质检 → verify_imports → check_refs，全绿才放行）
  * 冒烟测试（HTTP 200 + 窗口句柄存在 + 后台业务健康端点可达；详见 `references/07-quality-gate/Test/03-smoke-and-delivery.md`）
* **铁律（测试驱动门禁，逻辑层，必须）**：新业务模块必须 test-first（Red-Green-Refactor），**禁止「先实现后补测」**；bug 修复必须 Prove-It（先写复现测试）；**每次改动后跑全量 `uv run pytest` + HTML 审计，非零即阻断**。pytest 管「逻辑对不对」，绝不写脆弱的 DOM/渲染单测（那是 `ui_window_verify.py` 的职责）。
* **警告（核心节流点）**：禁止「绕过 启动.bat、未充分验证就直接打包」。打包只是交付的最后一步，不是验证手段。
* **警告（打包后又改代码）**：不立即重新打包，先用 `启动.bat` 跑源码验证改动，并主动提示用户当前 EXE 为旧快照；用户确认前不重打包。
* **放行判据**：pytest 全绿 + 机器视觉质检通过 + 路由链路校验通过 + 主流程走通 + 启动无报错。
* **产出物**：pytest 报告 + 审计报告 + 质检报告 + 路由链路报告。
* **验收标准**：三个阶段全通过（持续验证 pytest 全绿 → 全面验证机器视觉质检通过 + 主流程走通 → 预发布门禁路由链路校验 + 冒烟通过）。

### ⑧ 打包

* **任务**：门禁已在 ⑦ 预发布阶段通过，本步骤专注构建：最小 venv → PyInstaller `--onefile`（Windows；macOS/Linux 见 `references/08-packaging/cross-platform.md`）→ 冒烟测试 → 清理。
* **必读**：`references/08-packaging/INDEX.md`（打包总览 + 子专题导航）；`references/08-packaging/deep-dive.md`（PyInstaller 深度指南）；`references/08-packaging/cross-platform.md`（后端矩阵 / 各 OS 打包矩阵 / cefpython3 / DRY-RUN 铁律）；打包子专题（按流程顺序）：
  * `references/08-packaging/01-core-workflow.md`（前置检查 → 打包 → 验证）
  * `references/08-packaging/02-build-commands.md`（--onefile / --console / --noupx 等命令与参数）
  * `references/08-packaging/03-path-and-meta.md`（路径适配与元数据处理）
  * `references/08-packaging/04-advanced-config.md`（版本信息 / 图标 / 构建元数据 / 排除策略）
  * `references/08-packaging/05-smoke-test.md`（打包产物冒烟验证）
  * `references/08-packaging/06-troubleshooting.md`（打包故障排除）
  * `references/08-packaging/07-build-hardening.md`（构建加固：高级陷阱与实战经验）
* **执行**：`scripts/build_windows_exe.py`（Windows）；`scripts/build_cross_platform.py`（非当前 OS 仅 `--dry-run` 命令预演，严禁伪造结果）。
* **铁律（打包）**：
  * **必须最小 venv 打包**：创建干净 venv → 仅装实际依赖 → 在该 venv 中执行 PyInstaller
  * **必须使用 `--onefile` 单文件模式**：**严禁使用 `--onedir` 目录模式**（`_internal/` 目录与 EXE 捆绑不可分离，移动/分发时易遗漏导致崩溃）。验收标准：`dist/` 下不得出现 `_internal/` 目录；自动化检查：打包后运行 `ls dist/*/_internal/ 2>/dev/null`，有输出则拒绝发布
  * **Web 桌面应用必须 `console=True`**：用户需要看到启动日志和访问地址
  * **必须包含 pywebview 的 hidden-import**：pywebview 自带 PyInstaller hook，自动收集 `webview/lib`、动态库与 `webview/js`，**无需手动 `--hidden-import webview`**。业务壳只需补目标平台后端子模块：
    * **Windows**：`--hidden-import clr --hidden-import webview.platforms.winforms --hidden-import webview.platforms.edgechromium --hidden-import webview.platforms.mshtml`
    * **macOS / Linux**：见 `references/08-packaging/cross-platform.md` §跨平台构建矩阵
  * **必须包含 fasthtml 的 collect-submodules**：`--collect-submodules fasthtml`
  * **必须显式声明函数内懒加载模块**：若业务代码在函数 / 方法体内部 `from X import Y`（如第三方常驻网关模块），PyInstaller 静态分析**抓不到**，必须用 `--hidden-import` 或在项目 `src/pyinstaller_hidden_imports.txt` 声明，否则运行时 `ModuleNotFoundError` 且冒烟测试假绿（详见 `references/08-packaging/deep-dive.md` 铁律 #10）。通用脚本**不允许硬编码**项目专有模块——通过声明文件 / `-ExtraHiddenImports` 传入
  * **必须打包 pywebview 原生运行时**：pywebview 自带 hook 自动收集（Windows: `webview/lib` + 动态库 + `webview/js`），`build_windows_exe.py` 沿用此 hook，无需手写 `--add-data`。自定义 hook 放 `scripts/hooks` 或 `src/pyinstaller_hooks`。macOS/Linux 见 `references/08-packaging/cross-platform.md`
  * **跨平台 DRY-RUN 铁律**：PyInstaller 不支持交叉编译；非当前 OS 目标只生成**命令预演**（`--dry-run`），严禁伪造运行结果
  * **冒烟测试须验证业务健康端点（防假绿）**：打包后必须启动 EXE、等待 HTTP 200、确认窗口句柄存在；**若应用有后台业务子进程（网关 / Hermes 等），还须验证其业务健康端点**（如 `http://127.0.0.1:8642/health`），任一不可达即阻断交付——防"HTTP 正常但后台崩溃"的假绿。**严禁让用户代为测试**。用 `src/health_endpoints.txt` 或 `-HealthCheckUrls` 声明关键端点，全部 200 才放行
  * **服务启动时序（防窗口白屏）**：在 `webview.start()` 前必须等待 FastHTML 服务就绪。`main.py` 中应包含：`for _ in range(30): try: requests.get(f"http://127.0.0.1:{PORT}", timeout=1); break; except: time.sleep(1)`。同时确认使用 `127.0.0.1` 而非 `localhost`
  * **打包后改代码不立即重打包**：EXE 是打包时刻源码快照，改动后仍先用 `启动.bat` 跑源码验证；**主动提示用户 EXE 未更新、需重新打包**，**用户确认前不重新打包**——频繁重打包（`--onefile` 常 >120s）会严重拖慢开发，打包只在用户拍板交付时触发
* **警告**：构建必带大 `timeout=600` 或后台运行（PyInstaller --onefile 常 >120s）。
* **产出物**：`dist/*.exe`（Windows；macOS/Linux 产物见 `references/08-packaging/cross-platform.md`）。
* **验收标准**：打包前 pytest 全绿门禁通过 + 冒烟测试通过（HTTP 200 + 窗口正常）+ 跨平台目标遵守 DRY-RUN。

### ⑨ 交付

* **任务**：填写交付清单 → 说明产物位置、用法、退出方式 → 交付确认。
* **必读**：`references/09-delivery.md`（交付清单要点 / 双用途 README / 验收）；`docs/delivery-checklist.md`（交付清单）；`docs/glossary.md`（术语）。
* **要点**：交付清单须含测试证据（pytest 全绿 + 机器视觉质检通过 `ui_window_verify.py`），供用户验收参考；README 必须同时服务用户（说明书）与 LLM（克隆说明书）两类读者。
* **产出物**：已填写的交付清单 + 双用途 README（用户说明书 + LLM 克隆说明书）。
* **验收标准**：用户双击 `启动.bat` 即可独立使用，无需额外配置；README 可对照克隆出同等应用。
