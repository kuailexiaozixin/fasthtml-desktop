# 一键启动器：标准交付物与方法论

> 本文是 `SKILL.md`「标准交付物：一键启动器」的完整展开。`SKILL.md` 只保留方法论要点指针，具体规则与理由在此。
>
> **定位说明（重要）**：以下条目是**方法论与铁律（原则）**，不是必须逐字复制的「模板」。技能提供 `templates/shared/launcher.py` 作为一个**无状态、配置驱动的参考引擎**——它把所有项目差异放进同目录的 `launcher.json`，20 个示例的 `launcher.py` 逐字节相同（由 `scripts/gen_launchers.py` 统一分发），你既可以**直接采用它**，也可以按这些铁律**自行编写**启动器。**只要遵守下列铁律，启动器的具体形态可以灵活**，不必拘泥于某个固定文件结构。这避免了「模板过于僵硬、无法应对复杂多样场景」的问题。

---

### 场景分叉铁律（最高优先级）

**开发工作流（真实项目）** 与 **examples（演示语料）** 是**两个目的相反的场景**——环境策略、依赖策略、可接受副作用**全部相反**，二者只在「用户双击 `启动.bat` 就能跑」这一件事上相同。**禁止把一个场景的启动器直接搬进另一个场景**（尤其禁止把开发工作流的「重型可写启动器」搬进 examples：演示跑完就走，却会在用户全局环境留永久副作用，且多个示例争抢同一块 `site-packages`）。下方拆为 **通用规则 / §A 开发工作流 / §B examples** 三块，每块只描述本场景规则，互不套用。

---

### 通用规则（两个场景都必须遵守）

* **启动.bat 是唯一标准的一键启动器形态**：用户**双击 `启动.bat`** 即可启动应用，无需终端、无需手动装环境。**`.py` 文件双击默认用编辑器打开、不会运行**，故任何 f-d 项目的用户入口统一是 `启动.bat`；`start.py` / `dev_main.py` 等仅作开发者 CLI（质量门禁 / 无头调试）。**每个 f-d 项目都必须随附 `启动.bat`；缺失即补全**（技能级模板见 `templates/project-blueprints/web-desktop-exe/启动.bat.tmpl`，`bootstrap_project` 已自动产出）。

* **`启动.bat` 必须是 GBK/ANSI 编码 + CRLF 行尾，严禁 UTF-8/LF**：`cmd.exe` 默认按系统 ANSI 编码（中文 Windows 即 CP936）读取 `.bat`，且只认 `\r\n` 作为行尾。若保存为 UTF-8（尤其无 BOM）或 LF 行尾，中文/命令会被拆碎执行，表现为「双击闪退/满屏乱码」且不会生成 `启动诊断.log`。模板 `templates/project-blueprints/web-desktop-exe/启动.bat.tmpl` 与所有 examples 的 `启动.bat` 均已转存为 **GBK + CRLF**；`scripts/bootstrap_project.ps1` 生成时显式按 GBK 读写并强制规范化为 CRLF，确保新项目不会重蹈覆辙。

* **启动器分层铁律（bat 只派发，Python 做决策）**：`启动.bat` 只做三件事——`cd` 到目录、确认 PATH 中有 `python`、把控制权交给同目录 `launcher.py`（目标 ≤8 行）。**严禁在 batch 中实现依赖预检、依赖安装、注册表查询、日志取证等任何决策逻辑**。理由：batch 无异常处理、无数据结构、`errorlevel` 在括号块内语义诡异、`%VAR%` 解析期展开、中文强依赖 GBK——把决策放进表达能力最弱的语言，等于把最脆弱的环节放在最关键的位置。`launcher.py` 用 `sys.executable` 天然消除解释器二义性。参照 tkinter-desktop：其示例 `启动.bat` 仅 6-7 行，全部决策在 `launcher.py`，因而全部可稳定启动。

* **启动器统一真源（推荐采用配置驱动引擎，但非强制）**：`templates/shared/launcher.py` 是一个**无状态参考引擎**——它本身逐字一致，所有项目差异都放在同目录 `launcher.json`（键：`app_name` / `entry` / `use_venv` / `isolated_venv` / `bundled_venv` / `auto_install` / `side_processes` / `install_note` / `startup_note`）。若采用它，用 `scripts/gen_launchers.py` 把 `launcher.py`（引擎副本）+ `launcher.json` + `启动.bat` 分发到各示例与项目模板，**避免逐个示例手改**（改逻辑只改 `templates/shared/launcher.py` 再跑 gen）。分发方式是「复制引擎 + 写 JSON + 写 bat」三件零风险操作，**不再用正则把配置渲染进代码**（旧 `sync_launchers.py` 的正则渲染是「模板过于僵硬、BUG 多」的根因，已废弃）。**但这是推荐做法，不是硬性禁令**——若某示例有独特需求，完全可以另写符合铁律的启动器，不必强求共享。技能不要求所有启动器形态一致，只要求都遵守本文件的铁律。

* **切解释器重入禁止 `os.execv`（Windows 路径含空格必炸）**：启动器凡需切换解释器重新执行自身（`USE_VENV=True` 进项目 `.venv`、`ISOLATED_VENV` 进外置隔离环境），**必须用 `subprocess.call([...])` + `sys.exit(rc)`，禁止 `os.execv`**。Windows 的 CRT `execv` 把 argv 用空格拼成命令行且**不加引号**，脚本路径只要含空格（实测 `...\WPS 灵犀\...`）子进程就报 `can't open file 'C:\Users\x\AppData\Roaming\WPS'` 后静默失败；`subprocess` 走 `list2cmdline` 会正确加引号。代价仅是多留一个父进程壳。重入时须给子进程传 `FD_REEXEC=1`，让它以**追加模式**续写同一份 `启动诊断.log`，否则子进程会把父进程刚写的建环境记录截断。

* **依赖预检铁律（必须解析 requirements.txt，禁止写死子集）**：预检**必须逐条读取 `requirements.txt` 并 `importlib.util.find_spec()` 检查**，禁止使用手写的模块名常量（如 `import fasthtml, webview, uvicorn`）。写死子集会产生**假阳性放行**——预检通过 → 跳过安装 → 应用在真正缺失的包上崩溃（实测：03-FastCRM 预检通过但缺 `fastapi`，01 缺 `requests`，均在导入期崩溃）。包名与 import 名不一致者需维护映射表（`python-fasthtml→fasthtml`、`pywebview→webview`、`python-dotenv→dotenv`、`Pillow→PIL`）。**无 `requirements.txt` 的示例必须先补齐**，不得依赖脚本内的兜底安装列表。

* **禁止全量重定向输出**：严禁 `"%PY%" "%ENTRY%" > "%LOG%" 2>&1` 这类把全部输出吞进文件的写法——pip 安装数分钟内界面完全静默，用户无法判断是卡死还是在工作，失败后才一次性吐出大段日志。**实时可观测性的诊断价值远高于事后取证**。需要留档时用 `tee` 式双写，不得牺牲控制台实时输出。

* **Windows 桌面窗口硬依赖 Microsoft WebView2 Runtime（静默闪退头号诱因）**：pywebview 在 Windows 上默认走 **Edge WebView2** 后端，若本机未装 **WebView2 Runtime**，窗口会静默打不开——表现为主进程 0 退出、无窗口、旧版 `启动.bat` 直接双击闪退。**`启动.bat` 已内置检测与告警**：运行前通过注册表 `HKLM\SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}` 与 `Program Files (x86)\Microsoft\EdgeWebView\Application` 目录双重探测；缺失时打印中文告警 + 官方安装指引 + `pause`，**绝不再静默闪退**。安装方式：到 Microsoft 官网下载 "WebView2 Runtime 引导程序（Evergreen Bootstrapper）" 运行即可（企业机若被策略封锁，联系 IT 放行）。详见 `references/11-cross-platform.md` 后端矩阵。

* **README 必须具备双用途**：每个 f-d 项目必须有 `README.md`，同时是 (1) **用户使用说明书**（给最终用户：怎么装 / 怎么启动 / 怎么退出）与 (2) **LLM 克隆说明书**（给 LLM：目录树 / 入口约定 / 依赖 / 打包要点，可对照克隆出一模一样的应用）。缺失即补全（技能级模板见 `templates/project-blueprints/web-desktop-exe/README.md.tmpl`）。

---

### §A 启动器 A：开发工作流（真实项目）

> 目的：交付一个可打包成 EXE 的产品。环境策略=**隔离优先**，可接受「为可复现打包而动一下项目目录内的环境」（建最小 `.venv`）。

* **建最小项目 venv（`use_venv: true`）**：`启动.bat` 通过 `launcher.py` 的 `use_venv: true` 在**项目目录内**创建并使用最小 `.venv` 解释器，依赖安装进该 venv（**不污染用户全局 `site-packages`**）。这与 examples「复用全局」**正好相反**，不可混用。打包阶段另用独立**最小构建 venv**（见 §打包 铁律），与运行期 venv 互不干扰。

* **依赖锁定，服务可复现打包**：运行时业务依赖用 `uv add <包名>` 写入 `pyproject.toml`（如 fasthtml、pywebview、业务库），版本锁定、`uv sync` 可复现；构建期工具（PyInstaller 等）严禁进运行时依赖。

* **允许写日志文件、允许完整取证**：开发工作流是长期演进的产品，启动器**可写 `启动诊断.log` 做完整取证**；但即便写日志也必须用 `tee` 式双写（见通用规则「禁止全量重定向」），保证控制台实时可见。

* **开发流程门禁（必须用 启动.bat 充分验证后才打包）**：在 ⑥ 编码与 ⑦ 运行验证阶段，**必须反复用 `启动.bat` 启动应用**完成 测试 / 调试 / 检查 / 验证 / 修 BUG；**确认绝对准确无误、可交付后**，才进入 ⑧ 打包 EXE，再开展 ⑨ 交付。禁止「绕过 启动.bat、未充分验证就直接打包」——打包只是交付的最后一步，不是验证手段。

---

### §B 启动器 B：examples（演示语料）

> 目的：给 LLM 当参考语料 + 给人快速看效果。环境策略=**副作用最小优先**，对宿主机的影响**应当近似只读**。examples 里的每一行都在「教」未来的模型，硬编码路径 / 包管理器启发式都是会被继承的坏范式。

> **examples 启动器的具体策略不在本文件展开**——复用全局环境、禁止 `.venv`、禁止写死路径、版本互斥处置、外置隔离环境（`ISOLATED_VENV` / `BUNDLED_VENV`）、禁止降级用户已装包、验证门禁等完整细则，统一见 [`examples/README.md` §启动器策略（examples 专属）](../examples/README.md)。该策略与 §A（真实项目建最小 `.venv`）**正好相反**，不可混用启动器。

---

### 方法论小结：如何「极简」地给一个示例加启动器

铁律很严，但**创建过程可以很轻**——不必每次手写数百行启动器：

1. **绝大多数示例（03~07、09~20 这类单进程 fasthtml+uvicorn）**：直接采用配置驱动引擎即可——在 `scripts/gen_launchers.py` 的 `CONFIGS` 里加一行（示例名 + `app_name` + `entry`），跑一次 `python scripts/gen_launchers.py`，`launcher.py` + `launcher.json` + `启动.bat` 自动落位（`launcher.py` 引擎副本逐字节一致，`启动.bat` 为 GBK+CRLF）。**无需写任何启动逻辑**。
2. **版本互斥 / 重型可选依赖 / 多进程外部服务（01、02、08 这类例外）**：同样采用引擎，只是在 `launcher.json` 里多声明几项——`isolated_venv`（版本互斥，如 01 的 picolink、08 的 fasthtml==0.5.1）、`bundled_venv`（重型可选依赖收纳，如 02 的 pydantic-ai/logfire）、`side_processes`（多进程外部服务，如 01 的 `langgraph dev`）。引擎已内置这些能力，示例侧零额外代码。
3. **若某示例需求特殊到共享引擎也难覆盖**：按本文件铁律**自写**一个 `launcher.py`（或任何名字的 Python 决策层）+ 薄 `启动.bat` + `launcher.json`，只要满足「bat 只派发 / 逐条预检 / 禁止降级 / 禁止全量重定向 / GBK+CRLF / 切解释器用 subprocess」即可，形态不限。

> 核心思想：**铁律是硬的，模板是软的**。把「必须守的边界」和「可以灵活的形态」分开，复杂多样的示例就不会被一个僵硬模板卡死。
