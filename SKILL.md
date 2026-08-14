---

name: fasthtml-desktop
description: >
  FastHTML + pywebview 桌面应用的全生命周期技能。覆盖从需求澄清、FastHTML Web 开发、
  pywebview 桌面壳包装到 PyInstaller 打包交付的完整链路。
  最终交付物是包含 pywebview 原生窗口的 FastHTML 桌面 EXE（WebView2 渲染，本地 HTTP 服务）。
  当用户提到"fasthtml""pywebview""Web 桌面""HTMX 界面""本地 HTTP 服务"
  "带原生窗口的 Web 应用""pywebview 打包"时使用本技能。
version: "1.4.0"
author: agent
agent_created: true
platform: multi

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

**写任何 FastHTML 代码前，必须先读** **`references/fasthtml-refs/fasthtml-llms-ctx.txt`。**

该文件是 FastHTML 官方 LLMs 上下文文件（约 10,100 行），覆盖所有 API 签名、路由模式、FastTags、HTMX 集成等。**写任何代码前必须阅读**，阅读后聚焦本任务相关的关键结论、API 签名/组件、以及与 FastAPI 的语法差异；否则 API 使用错误、组件属性遗漏、路径映射失败。

**必须按工作流制定任务计划，不得跳过任何步骤，不得漏步骤未执行。** 尤其重视 ⑦ 质量门禁的三个阶段（持续验证→全面验证→预发布门禁），每个阶段中的所有检查项均须执行通过，不可省略。

***

## 排障

> **排障指南（问题沉淀首选）**：`./docs/troubleshooting.md` —— 执行过程中发现的问题（现象、本质）及解决办法，**优先沉淀到此文件**，除非是特别重要的主干内容。SKILL.md 只保留铁律/规则本身，踩坑叙事与排障步骤迁入 troubleshooting.md。

***

## 架构约束（选型前必读）

FastHTML 是**服务端渲染**框架：HTML 由 uvicorn 按请求实时生成，**磁盘上无静态 HTML 入口文件**。

1. **禁用依赖静态 HTML 入口的工具**（注入式质检、`/live` 热重载、SSR 预渲染等）。
2. **正确路径是「真实渲染引擎」驱动**：用 pywebview 原生窗口质检与自动化（`scripts/ui_window_verify.py`、`scripts/ui_automate.py`），无需第二个浏览器；无 GUI 时用 headless HTML 审计（`scripts/ui_audit.py`）。两者都**非**解析静态 HTML。


> pywebview 导入/启动、质检脚本用法、DOM 断言检查能力、像素截图等技术要点见 `references/quality-check/05-ui-verification-details.md`。

***

## 目录结构与主题路由

> 原则：先按意图命中下表，再读对应文件；命中多个时优先读更具体的那个。

### 入口与决策

* **不清楚该从哪里开始** / 想了解完整流程：`./docs/glossary.md` → 读完回归此表

* **需求澄清**、首轮话术、必问问题：`./references/01-need-discovery.md`

### 环境与项目初始化

* **必须先运行** `./scripts/ensure_uv_env.sh` 或 `./scripts/ensure_uv_env.ps1`：检查/安装 uv、配置镜像、安装 Python。任何新建项目的第一步，**禁止跳过**

* 项目初始化、蓝图实例化：`./scripts/bootstrap_project.sh` 或 `./scripts/bootstrap_project.ps1`

* 依赖管理（uv add、uv sync）：`./references/04-agent-execution-and-env.md`

### 架构设计

* **架构设计**（18 个章节，覆盖系统上下文、核心业务流、模块分解、数据架构、接口设计、统一架构框架、场景驱动的架构类型选择等）：`./references/architecture/INDEX.md`

* **功能模块设计**（功能-模块分配矩阵、模块接口契约、模块依赖图、数据流图）：`./references/02-module-design.md`

### 编码与结构规范

文件体系分为四个层级，按顺序自上而下查阅。**Layer 1 为前置必读**，后面层级根据任务需要按需引用。

#### Layer 1：FastHTML 核心 API（前置必读）

> **PyPI 包名**：本框架在 PyPI 上的发行包名为 **`python-fasthtml`**（导入名仍为 `fasthtml`，即 `pip install python-fasthtml` 后使用 `from fasthtml.common import *`）。PyPI 上没有名为 `fasthtml` 的发行包。

| 文件                                               | 说明                                                              | 优先级            |
| ------------------------------------------------ | --------------------------------------------------------------- | -------------- |
| `references/fasthtml-refs/fasthtml-llms-ctx.txt` | **FastHTML 官方 LLMs 上下文**（llms-ctx-full，约 10,100 行），完整 API 签名与示例 | **写任何代码前必须先读** |
| `references/fasthtml-refs/fastlite-llms.txt`     | **FastLite 官方 LLMs 上下文**，FastLite API 签名与用法示例                   | 数据库操作时查阅       |

#### Layer 2：框架集成与项目结构

| 文件                                      | 说明                                                                                                                                                           |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `references/05-project-structure.md`    | 项目结构、代码规范、分层原则                                                                                                                                               |
| `references/10-ft-handlers-typing.md`   | **FastHTML 参数绑定规则**：绑定顺序、特殊参数名、方法选择、结构化类型、常见签名错误                                                                                                             |
| `references/06-pywebview-shell.md`      | pywebview 桌面壳（**跨平台后端**：Edge/mshtml/cocoa/gtk/qt、窗口控制、JS 桥接、对话框、菜单、**外链行为** **`webbrowser.open`** **内部实现**、DOM 操作、`window.state` 共享状态、透明窗口、拖拽区、文件下载/拖放、系统托盘） |
| `references/pywebview-examples/`        | **60 个已验证示例脚本**（A 类高价值缺口修正 / B 类 API 覆盖 / D 类增补实证 / E 类跨平台专属），每个文件含 FastHTML+pywebview 适配注释头，py\_compile 全通过                                                 |
| `references/07-integration-patterns.md` | **三者协同**（fasthtml + pywebview + PyInstaller）：启动顺序、端口协商、双入口、优雅退出                                                                                              |
| `references/11-cross-platform.md`       | **多端适配总览**：后端矩阵（T1 实证）、各 OS 打包矩阵（Windows PyInstaller / macOS py2app / Linux AppImage）、cefpython3 限制、pywebview 自动 hook、DRY-RUN 铁律                             |

#### Layer 3：UI 框架与设计质量

| 类别     | 文件                                                | 说明                                |
| ------ | ------------------------------------------------- | --------------------------------- |
| CSS 框架 | `references/fasthtml-refs/picocss-reference.md`   | PicoCSS 参考                        |
| CSS 框架 | `references/fasthtml-refs/monsterui-llms-ctx.txt` | MonsterUI 参考                      |
| CSS 框架 | `references/fasthtml-refs/faststrap-llms.txt`     | FastStrap 参考                      |
| 界面设计   | `references/03-ui-design.md`                      | 原型驱动界面设计：三步法、布局模板、CSS 框架选型、交互位置标注 |

#### Layer 4：补充参考（按需查阅）

| 文件                                                       | 说明                                                                        |
| -------------------------------------------------------- | ------------------------------------------------------------------------- |
| `references/fasthtml-refs/genui-hypermedia-reference.md` | GenUI 超媒体参考                                                               |
| `references/12-fasthtml-fastapi.md`                      | **FastAPI 集成**：在 fasthtml 中挂载 FastAPI 子应用，创建 RESTful API 并自动生成 OpenAPI 文档 |

### 质量检查

* 代码检查、运行验证、语法门禁、冒烟测试、界面验证（机器视觉质检：`ui_window_verify.py` DOM 断言+截图；UI 交互自动化：`ui_automate.py` 点击/输入/导航/断言；两者均 pywebview 原生、零额外浏览器、零浏览器授权）：`./references/quality-check/INDEX.md`

* 测试驱动开发（单元/集成/数据驱动/回归，pytest）：`./references/09-test-driven-development.md`

* **测试夹具 schema 对齐**（防 fixture rot，insert 字典键校验）：`./docs/troubleshooting.md` 第五章

* FastHTML 参数绑定与签名规范（绑定顺序、特殊参数名、方法选择、结构化类型）：`./references/10-ft-handlers-typing.md`

### 打包与交付

* **打包的硬规则、深入资料索引与构建脚本**统一见下方 `### 打包` 一节（该节内含 `--onefile` / 最小 venv / hidden-import 等铁律，以及 `08-packaging.md`、跨平台矩阵、各 OS 构建脚本的索引）。

* **启动器标准交付物（启动.bat + 决策层 + 双用途 README）完整规则与理由**见 `references/launch-standard-deliverable.md`（SKILL.md 仅留要点）。

### 参考实现

* **项目骨架（空白模板）**：`./templates/project-blueprints/web-desktop-exe/` —— 已内置 **`启动.bat`（一键启动器）** + **双用途** **`README.md.tmpl`** + `requirements.txt`，`bootstrap_project` 生成项目时自动实例化，无需手工补文件。

* **共享入口模板**：`./templates/shared/main.py`（修改后运行 `scripts/sync_examples.sh` 同步到各示例）

* **原型模板**：`./templates/prototype-app.py.tmpl`（含搜索表单/结果表格/分页/统计栏完整骨架）

* **完整示例**（业务场景参考语料）：`./examples/` —— 20 个真实业务应用（知识库 / 交通看板 / CRM / ERP / HRM / BI / 在线表格 / 演示文稿 / 文件管理 / 法务助手 / 学习管理 / 会议协作 / 邮件客户端 / 生成式 UI / 代码助手 / 文档编辑器 / 企业服务管理 / 按揭服务权管理 / 文档工作流 / 客服工单），是**最值得直接借鉴的范式样本**：入口壳、分层组织、FastHTML+HTMX 组件化、标准库优先、认证、打包等均已落地可跑。

  > **复用优先（非必要不自造轮子）**：在 ① 需求澄清 / ② 架构设计 / ⑥ 编码 各阶段，**先扫一遍** **`examples/`** **有没有可复用的技术**——入口壳（`templates/shared/main.py`）、认证模块（`web/account_auth.py`）、`_bootstrap_db()` 约定、扁平布局、启动器套件、`build_fast_example.py` 打包 hidden-import 清单等，能直接套用就不重写。examples 里的每一行都在「教」未来模型，照抄优于自造。

  > **完整目录（业务场景 / 默认端口 / 技术要点 / 各示例差异）见** **`./examples/README.md`**——该文件是 examples 的权威索引，本 SKILL.md 不重复罗列细节。

* 术语解释：`./docs/glossary.md`

***

> 技术栈全景见 `references/11-cross-platform.md`。

## 完整工作流（= 后续 AI 的最低执行清单）

> 本流程即后续 AI 的唯一执行清单，按 ①→⑨ 顺序执行，**不可跳过、不可乱序**。各步骤的铁律与门禁细节见下方「必须遵守的铁律」各小节及对应 references。

```
用户说"帮我做个桌面工具"
  │
  ├─ 分支：新建项目 / 已有项目？
  │     │
  │     ├─ 新建项目 → 走以下完整流程
  │     │
  │     └─ 已有项目 → 跳过 ①-④，执行结构合规检查：
  │         1. 检查 src/ 下存在 app.py 或 <pkg>/app.py
  │         2. 检查 src/main.py 是否存在且入口正确
  │         3. 检查 启动.bat / launcher.json / requirements.txt（或 pyproject.toml）是否存在（依赖装进项目 venv，由 launcher.json 的 use_venv 管理，不污染用户全局环境）
  │         4. 检查 pyproject.toml 依赖是否完整
  │         5. 检查界面渲染与交互（图标/重叠/对比度/空白页等）
  │         合规检查通过后 → 进入 ⑤ 界面设计（如有新 UI）或直接 ⑥ 编码
  │
  ├─ ① 需求澄清（01-need-discovery.md）
  │    问清楚：做什么？输入输出？给谁用？
  │    ▶ 同时捕获**可测试验收标准**（输入/输出/边界/异常路径），作为 ⑥ 测试与 ⑨ 验收的依据
  │    ▶ **先看 examples 有没有同类业务场景**：扫一遍 `./examples/README.md`，若已有相似应用（如 CRM/ERP/表格/文件管理），直接复用其业务建模与入口范式，非必要不自造轮子
  │    ▶ 产出：需求优先级表（MoSCoW 分级）
  │
  ├─ ② 架构设计（先读 references/architecture/INDEX.md）
  │    定 MVP 边界、选架构模式、画业务流图
  │    ▶ **先看 examples 同类应用的架构**：扁平布局 / 分层（`app.py`+`db.py`+`routes_*.py`）/ 插件化 / 入口壳（`templates/shared/main.py`）等，直接套用成熟范式，不重新发明
  │    ▶ 产出：docs/architecture.md（MVP 边界表 + 模块分解 + 业务流图 + 接口设计）
  │
  ├─ ②-α 功能模块设计（02-module-design.md）
  │    功能-模块分配矩阵 → 模块接口契约 → 模块依赖图 → 数据流图
  │    ▶ 模块接口契约即**测试契约**：每个契约点对应一个 ⑥ 的测试用例
  │    ▶ 产出：docs/modules.md（功能-模块矩阵 + 接口契约 + 依赖图）
  │
  ├─ ③ 环境准备（铁律：先跑 ensure_uv_env.sh）
  │    安装 uv、配置镜像、安装 Python
  │    ▶ 产出：uv + Python 环境已就绪
  │
  ├─ ④ 项目初始化（铁律：跑 bootstrap_project.sh）
  │    生成 web-desktop-exe 骨架 → 用 `uv add` 补充业务依赖 → uv sync
  │    ▶ **产出含标准交付物（每个 f-d 项目必备）**：骨架 + .gitignore + .env.example + **`启动.bat`（一键双击启动器）** + **`launcher.py`（一键启动决策层，双击后端的唯一逻辑源）+ `launcher.json`（启动配置）** + **双用途 `README.md`（用户说明书 + LLM 克隆说明书）** + `requirements.txt`（启动.bat 装依赖用）
  │    ▶ `启动.bat`：通过 `launcher.json` 的 `use_venv=true` 在**项目目录内建最小 `.venv`** 并 re-exec 进去（隔离优先、不污染用户全局环境，与 examples「复用全局」相反）→ 首次运行预检依赖，缺失则 `pip install` 到**该 venv** → 启动 main.py 弹桌面窗口；普通用户双击即用，无需终端。**`.py` 双击默认用编辑器打开不会运行**，故用户入口统一是 `启动.bat`，`start.py` 仅作开发者 CLI。
  │    ⚠ 骨架用 bootstrap 脚本，逐文件 Write，禁单条巨命令；命令超时见下方「命令执行与超时」铁律
  │
  ├─ ⑤ 界面设计（先读 03-ui-design.md）
  │    用 FastHTML 写出纯界面原型，预览后迭代
  │    设计质量评审详见「编码与结构规范 > Layer 3」
  │    ▶ UI 行为变更须同步更新/新增对应测试；界面交付以 **机器视觉质检（UI 自动化测试）** 为唯一机器手段：`scripts/ui_window_verify.py`（pywebview 原生窗口 + 可选 html2canvas 无头截图，详见 09-test-driven-development.md §1）
  │    ▶ 产出：prototype_app.py（可运行纯界面原型）
  │
  ├─ ⑥ 编码（先读 fasthtml-refs/fasthtml-llms-ctx.txt【前置必读】 + 10-ft-handlers-typing.md【参数绑定规则】 + 07-integration-patterns.md）
  │    在 src/app.py 中写业务逻辑
  │    最小可运行版本先行：先跑通空壳确认技术栈兼容，再加业务
  │    src/main.py 不动（pywebview + uvicorn 入口）
  │    ▶ **写业务代码前先查 examples 有没有现成实现**：认证/登录（`web/account_auth.py`）、FastHTML+HTMX 局部刷新、FastAPI 子应用挂载、标准库导出、PyInstaller hidden-import 套路等，能 copy-adapt 就不重写
  │    ▶ **⑥-β 测试驱动（详见 09-test-driven-development.md）**：每新增业务模块先写失败测试（Red-Green-Refactor）；
  │      修 bug 走 Prove-It（先写复现测试）；禁止「先实现后补测」。
  │    ▶ 产出：src/app.py + 各模块文件 + tests/ 对应测试
  │
  ├─ ⑦ 质量门禁（打包前必过，分三个阶段按序执行）
  │
  │    [阶段一：持续验证]（每次改代码后立即执行）
  │    ▶ `py_compile` 语法检查 + `python -c "from app import app"` 导入测试
  │    ▶ `uv run pytest` 单元/集成测试全绿（逻辑门禁，非零即阻断）
  │    ▶ 语法 / 导入 / 静态检查细则见 references/quality-check/01-static-code-checks.md
  │
  │    [阶段二：全面验证]（功能开发完成后执行）
  │    ▶ **用 `启动.bat` 启动应用**，自测正常+异常路径
  │    ▶ UI 反模式检查（`scripts/ui_audit.py`，纯 headless，禁止跳过；自动抓取 `<link rel=stylesheet>` 外部 CSS 纳入审计，CSS 外部化项目不再误报；可用 `--ignore-ban "禁令名/序号/子串"` 豁免已知误报；反模式规则详见 references/quality-check/02-ui-audit.md）
  │    ▶ 机器视觉质检（`scripts/ui_window_verify.py`：DOM 断言+可选截图；HTML 结构验证通过≠界面没问题；无 GUI 强制 HTML 结构验证）
  │    ▶ UI 交互自动化（`scripts/ui_automate.py`：点击/输入/导航/断言，验证交互行为正确性）
  │    ▶ 质检脚本详细用法见 `references/quality-check/05-ui-verification-details.md`
  │    ▶ 测试夹具 schema 对齐：新增测试须用 `scripts/fixture_schema_helper.py` 校验 insert 键全部存在于真实 db 列（见 `docs/troubleshooting.md` 第五章）
  │
  │    [阶段三：预发布门禁]（打包前执行一次）
  │    ▶ 前端→后端路由链路校验（`scripts/check_routes_linkage.py`：捕获前端引用但后端未注册的路由，防运行时 404。exit 1 = 阻断发布；规则详见 references/quality-check/03-route-hygiene.md）
  │    ▶ 统一发布门禁（`scripts/release_gate.py`：串联 pytest → check_routes → check_routes_linkage → UI 视觉质检 → verify_imports → check_refs，全绿才放行）
  │    ▶ 冒烟测试（HTTP 200 + 窗口句柄存在 + 后台业务健康端点可达；详见 references/quality-check/04-smoke-and-delivery.md）
  │
  │    ⚠ **核心节流点**：禁止「绕过 启动.bat、未充分验证就直接打包」。打包只是交付的最后一步，不是验证手段。
  │    ⚠ **打包后又改代码**：不立即重新打包，先用 `启动.bat` 跑源码验证改动，并主动提示用户当前 EXE 为旧快照；用户确认前不重打包。
  │    ▶ 放行判据：pytest 全绿 + 机器视觉质检通过 + 路由链路校验通过 + 主流程走通 + 启动无报错
  │    ▶ 产出：pytest 报告 + 审计报告 + 质检报告 + 路由链路报告
  │
  ├─ ⑧ 打包（08-packaging.md + 11-cross-platform.md + 构建脚本）
  │    门禁已在 ⑦ 预发布阶段通过，本步骤专注构建：
  │    最小 venv → PyInstaller `--onefile`（Windows；macOS/Linux 见 `references/11-cross-platform.md`）→ 冒烟测试 → 清理
  │    ▶ 产出：`dist/*.exe`（Windows）
  │    ▶ **跨平台 DRY-RUN 铁律**：PyInstaller 不支持交叉编译；非当前 OS 目标只生成**命令预演**（`--dry-run`），严禁伪造运行结果（见 11-cross-platform.md）
  │    ⚠ 构建必带大 timeout=600 或后台运行（PyInstaller --onefile 常 >120s）
  │
  └─ ⑨ 交付（先读 docs/delivery-checklist.md）
      填写交付清单 → 说明产物位置、用法、退出方式 → 交付确认
      ▶ 交付清单须含**测试证据**（pytest 全绿 + 机器视觉质检通过：`ui_window_verify.py`），供用户验收参考
      ▶ 产出：已填写的交付清单 + 双用途 README（用户说明书 + LLM 克隆说明书）
```

### 各步骤产出物清单

| 步骤         | 产出物                                                                                                                                    | 验收标准                                                                                                                                                |
| ---------- | -------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| ① 需求澄清     | 需求优先级表                                                                                                                                 | Must/Should/Could/Won't 已分级，MVP 清单已确认                                                                                                               |
| ② 架构设计     | `docs/architecture.md`                                                                                                                 | 含 MVP 边界表 + 模块分解 + 业务流图 + 接口设计                                                                                                                      |
| ②-α 功能模块设计 | `docs/modules.md`                                                                                                                      | 含功能-模块分配矩阵 + 模块接口契约 + 模块依赖图 + 数据流图                                                                                                                  |
| ③ 环境准备     | uv + Python + 镜像已配置                                                                                                                    | `uv --version` 正常输出                                                                                                                                 |
| ④ 项目初始化    | 骨架 + `.gitignore` + `.env.example` + **`启动.bat`** + **`launcher.py`** **+** **`launcher.json`** + 双用途 `README.md` + `requirements.txt` | 双击 `启动.bat` 可自动建项目 venv 并装依赖启动（依赖装进项目内 venv，`use_venv=true`，不污染全局 Python）；`uv sync` 成功                                                              |
| ⑤ 界面设计     | `prototype_app.py`                                                                                                                     | 可运行预览，含模拟数据，确认布局后进入编码                                                                                                                               |
| ⑥ 编码       | `src/app.py` + 各模块文件 + `tests/` 对应测试                                                                                                   | 语法检查通过 + 模块导入测试通过 + **对应单元/集成测试存在且通过（Red-Green-Refactor，禁止先实现后补测）**                                                                                 |
| ⑦ 质量门禁     | pytest 报告 + 审计报告 + 质检报告 + 路由链路报告                                                                                                       | **三个阶段全通过**：持续验证（pytest 全绿）→ 全面验证（机器视觉质检通过 + 启动.bat 主流程走通）→ 预发布门禁（路由链路校验通过 + 冒烟测试通过）                                |
| ⑧ 打包       | `dist/*.exe`（Windows；macOS/Linux 产物见 `references/11-cross-platform.md`）                                                                | **打包前 pytest 全绿门禁通过** + 冒烟测试通过（HTTP 200 + 窗口正常）+ 跨平台目标遵守 DRY-RUN（非当前 OS 仅命令预演）                                                                      |
| ⑨ 交付       | `delivery-checklist.md` 已填写 + `README.md`（双用途：用户说明书 + LLM 克隆说明书）                                                                       | 用户双击 `启动.bat` 即可独立使用，无需额外配置；README 可对照克隆出同等应用                                                                                                       |

***

## 必须遵守的铁律（最高优先级）

### 环境与初始化

* **环境先行**：任何新建项目前，**必须率先运行** `./scripts/ensure_uv_env.sh`（优先）或 `./scripts/ensure_uv_env.ps1`。**禁止跳过**。> `.sh` 版本是对 `.ps1` 的包装（通过 `dash -c powershell.exe` 间接调用），AI 默认执行 `.sh` 版本。无 `dash` 环境时可用 tclsh 替代

* **必须跑 bootstrap 脚本**：新建项目必须运行 `./scripts/bootstrap_project.sh`（优先）或 `./scripts/bootstrap_project.ps1` 生成骨架。**禁止从零手写 pyproject.toml 或逐级 mkdir**

* **依赖管理分级**：

  * **运行时业务依赖**用 `uv add <包名>` 写入 `pyproject.toml`（如 fasthtml、pywebview、业务库）。

  * **构建期工具**（PyInstaller、pythonnet 等）**严禁写入运行时依赖**：用 `uv pip install --python <build-venv>/Scripts/python.exe <包名>` 装进独立打包 venv（参考 `references/08-packaging.md` 最小 venv 章节）。**既不要用** **`uv add`（会污染运行时依赖），也不要在业务 venv 裸用** **`pip install`。**

* **必须先有骨架再写代码**：骨架落地前，禁止开始写任何 .py 业务代码

* **必须创建最小 venv**：项目目录创建后，立即 `python -m venv .venv`，否则打包体积膨胀（16MB → 154MB 的差距）

### 编码

* **接口层入口必须** **`reload=False`**：`uvicorn.run(app, reload=False)`，禁止 `serve()` 打包

* **路径适配必须用** **`sys.frozen`** **检测**：`BASE_DIR = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent`

* **FastHTML 组件参数顺序**：位置参数（子元素）必须在关键字参数（HTML 属性）之前。`Div(H1("标题"), cls="box")` ✅；`Div(cls="box", H1("标题"))` ❌

* **APIRouter 必须显式声明路径**：每个路由用 `@ar("/projects/{pid}")` 显式声明路径，禁止依赖自动路由生成（函数名下划线转连字符，与手写 href 不匹配，导致全站 404）

* **URL 一律用 127.0.0.1**：`http://127.0.0.1:{PORT}`，禁止使用 `localhost`（某些环境 localhost 解析被拦截，导致页面加载失败或白屏）

* **uvicorn 线程必须 daemon**：`threading.Thread(target=run_server, daemon=True)`，否则关闭窗口后进程不退出

### 质量

* **语法检查门禁（代码发布前必跑）**：写入任何 `.py` 文件后，立即做 `py_compile.compile()` 语法验证，防语法错误逃逸；连同模块导入测试 `python -c "from app import app"` 一起执行，**禁止跳过**。详见 `references/04-agent-execution-and-env.md` § 编码铁律。

* **编码门禁（文件编码）**：`.py` 源码一律 UTF-8 无 BOM，禁止 PowerShell `Set-Content` 写源码（详见 `references/04-agent-execution-and-env.md` 编码铁律）。禁止混合 CRLF/LF 行尾。

* **冒烟测试门禁（不可跳过）**：打包后必须启动 EXE、等待 HTTP 200、确认窗口句柄存在。**若应用有后台业务子进程（网关 / Hermes 等），还须验证其业务健康端点（如** **`http://127.0.0.1:8642/health`，见** **`08-packaging.md`），任一不可达即阻断交付——防"HTTP 正常但后台崩溃"的假绿。严禁让用户代为测试**

* **界面交付门禁（机器视觉质检 + UI 自动化，必须）**：**必须用机器手段验证界面**：`scripts/ui_window_verify.py`（pywebview 原生窗口 DOM 断言+截图，无需第二个浏览器、零浏览器授权；无头截图自动回退 html2canvas）+ `scripts/ui_automate.py`（UI 交互自动化：点击/输入/导航/断言，验证按钮/表单/状态切换等交互行为正确性）。HTML 结构验证（`ui_audit.py`）通过 ≠ 界面没问题。质检/自动化 exit 1 即禁止发布。

* 注：本技能**不限制运行时使用 CDN**（jsdelivr/unpkg 等外部资源引用允许），CDN 可用性由项目自行决定。纯主观审美不在机器范围，按需人工判断，但**不将人工截图作为验收手段**。

* **测试驱动门禁（逻辑层，必须）**：新业务模块必须 test-first（Red-Green-Refactor），**禁止「先实现后补测」**；bug 修复必须 Prove-It（先写复现测试）；**每次改动后跑全量** **`uv run pytest`** **+ HTML 审计，非零即阻断**。pytest 管「逻辑对不对」，绝不写脆弱的 DOM/渲染单测（那是 `ui_window_verify.py` 的职责）。详见 `references/09-test-driven-development.md`。

* **控制台输出禁止 emoji**：打包后 EXE 运行在 Windows 控制台（GBK 编码），emoji 会导致乱码。用 `[OK]` / `[FAIL]` 替代 ✅ / ❌，用 `[INFO]` / `[WARN]` / `[ERROR]` 替代图标。

### 标准交付物：一键启动器（启动.bat + 决策层 + 双用途 README）

> ⚠️ **场景分叉铁律**：开发工作流（真实项目）与 examples（演示语料）的环境/依赖策略**全部相反**，禁止互相套用启动器。

完整规则与理由见 [`references/launch-standard-deliverable.md`](references/launch-standard-deliverable.md)，要点：

* **bat 只派发，Python 做决策**：`启动.bat`（≤8 行，GBK+CRLF）只交权给 `launcher.py`，严禁在 batch 里写决策逻辑。

* **逐条解析** **`requirements.txt`** **预检**，禁止写死模块名子集。

* **禁止降级用户已装包**；**禁止** **`os.execv`**（Windows 路径含空格必炸，用 `subprocess.call` + `sys.exit`）。

* **`启动.bat`** **必须 GBK/ANSI + CRLF**。

* **README 双用途**：用户说明书 + LLM 克隆说明书。

> `templates/shared/launcher.py` 是配置驱动的参考引擎（`launcher.json` 管差异，`gen_launchers.py` 统一分发），也可按铁律自行编写。examples 策略见 `examples/README.md` §启动器策略。

### 打包

* **必须最小 venv 打包**：创建干净 venv → 仅装实际依赖 → 在该 venv 中执行 PyInstaller

* **必须使用** **`--onefile`** **单文件模式**：**严禁使用** **`--onedir`** **目录模式**。`--onedir` 产物的 `_internal/` 目录与 EXE 捆绑不可分离，移动/分发时易遗漏导致崩溃。

  * 验收标准：`dist/` 下不得出现 `_internal/` 目录

  * 自动化检查：打包后运行 `ls dist/*/_internal/ 2>/dev/null`，有输出则拒绝发布

* **Web 桌面应用必须** **`console=True`**：用户需要看到启动日志和访问地址

* **必须包含 pywebview 的 hidden-import**：pywebview 自带 PyInstaller hook，自动收集 `webview/lib`、动态库与 `webview/js`，**无需手动** **`--hidden-import webview`**。业务壳只需补目标平台后端子模块：

  * **Windows**：`--hidden-import clr --hidden-import webview.platforms.winforms --hidden-import webview.platforms.edgechromium --hidden-import webview.platforms.mshtml`

  * **macOS / Linux**：见 `references/11-cross-platform.md` §跨平台构建矩阵。

  * **DRY-RUN 铁律**：PyInstaller 不支持交叉编译，非当前 OS 仅命令预演，严禁伪造结果。

* **必须包含 fasthtml 的 collect-submodules**：`--collect-submodules fasthtml`

* **必须显式声明函数内懒加载模块**：若业务代码在函数 / 方法体内部 `from X import Y`（如第三方常驻网关模块 `gateway_pkg.gateway`，为保持 GUI 启动轻量而延迟导入），PyInstaller 静态分析**抓不到**，必须用 `--hidden-import` 或在项目 `src/pyinstaller_hidden_imports.txt` 声明，否则运行时 `ModuleNotFoundError` 且冒烟测试假绿（详见 `08-packaging.md` 铁律 #10）。通用脚本**不允许硬编码**项目专有模块——通过声明文件 / `-ExtraHiddenImports` 传入。

* **必须打包 pywebview 原生运行时**：pywebview 自带 hook 自动收集（Windows: `webview/lib` + 动态库 + `webview/js`），`build_windows_exe.py` 沿用此 hook，无需手写 `--add-data`。自定义 hook 放 `scripts/hooks` 或 `src/pyinstaller_hooks`。macOS/Linux 见 `references/11-cross-platform.md`。

* **冒烟测试须验证业务健康端点（防假绿）**：见上方「冒烟测试门禁」；用 `src/health_endpoints.txt` 或 `-HealthCheckUrls` 声明关键端点，全部 200 才放行。

* **打包后改代码不立即重打包**：EXE 是打包时刻源码快照，改动后仍先用 `启动.bat` 跑源码验证；**主动提示用户 EXE 未更新、需重新打包**，**用户确认前不重新打包**——频繁重打包（`--onefile` 常 >120s）会严重拖慢开发，打包只在用户拍板交付时触发。

* **服务启动时序（防窗口白屏）**：在 `webview.start()` 前必须等待 FastHTML 服务就绪。`main.py` 中应包含：`for _ in range(30): try: requests.get(f"http://127.0.0.1:{PORT}", timeout=1); break; except: time.sleep(1)`。同时确认使用 `127.0.0.1` 而非 `localhost`。

* **深入资料与构建脚本**：

  * PyInstaller 深度指南：`references/08-packaging.md`；打包子专题：`references/packaging/`（7 文件，按流程顺序）

  * 多端适配总览：`references/11-cross-platform.md`

  * Windows EXE：`scripts/build_windows_exe.py`（推荐）/ `.ps1` / `.sh`

  * 跨平台驱动：`scripts/build_cross_platform.py`（非当前 OS 仅 `--dry-run`）

### 命令执行与超时

> `run_command` 默认超时 120s。详细分析见 `docs/troubleshooting.md`。

* **禁止单条 shell 命令批量造文件**：源码/配置/资源文件**逐文件 Write/Edit**，严禁 `cat <<'EOF' > file` 连写多文件。

* **可能 >120s 的操作必须显式传** **`timeout=600`** **或后台运行**：构建（PyInstaller `--onefile` 常 >120s）尤其如此。

* **失败即拆步**：超时则拆成更小步骤，每步独立可验证。

***

## 命令代执行规则

* 涉及 `uv init`、`uv add`、`uv sync`、`uv run`、`ruff`、`mypy`、`pytest`、`pyinstaller` 时，默认由 AI 发起

* **环境先行**：创建项目目录后的第一件事是 `python -m venv .venv`，否则禁止安装任何依赖

* 中国网络环境下，涉及 uv、Python 与包安装时，默认先设置镜像再执行

* 如果运行命令需要系统授权、联网安装或写文件，AI 负责发起

* 除非用户明确要求学习命令行，否则不要把"请你在终端执行以下命令"当成默认答案

* **每次** **`file(action=edit)`** **修改代码后，必须执行验证**：`py_compile.compile()` 语法检查 + `python -c "from app import app"` 导入测试。这是防止精确替换导致断裂引用的最后防线

## 代码与结构原则

* 新项目使用 `src` 结构

* 在 `pyproject.toml` 的 `[project.scripts]` 中定义启动别名，`uv run <别名>` 运行

* 业务逻辑、页面组件、配置读取、文件读写分层

* 默认补齐类型注解、日志、错误提示、`.env.example`、`.gitignore`

* 日志默认按日期分文件、单文件 5MB、保留最近 30 天

* 单文件过大时主动拆分
