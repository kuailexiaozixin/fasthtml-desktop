# 打包与 EXE 交付

> 本文档汇总 fasthtml + pywebview 桌面应用的打包知识，
> 以及本技能特有的组合打包参数与铁律。
>
> 详细内容按模块拆分到 `packaging/` 目录下，通过下方导航快速定位。

---

## 快速导航

| # | 主题 | 文件 | 内容摘要 |
|---|------|------|---------|
| 1 | **核心工作流** | [packaging/01-core-workflow.md](packaging/01-core-workflow.md) | 环境审计、9 步打包流程、最小 venv 体积控制 |
| 2 | **打包命令与参数** | [packaging/02-build-commands.md](packaging/02-build-commands.md) | `--onefile` 铁律、完整命令、参数说明、常见故障 |
| 3 | **DLL 依赖诊断与修复** | [packaging/02-build-commands.md](packaging/02-build-commands.md#dll-依赖诊断与修复) | DLL 诊断脚本、崩溃场景速查、自动修复 |
| 4 | **pythonnet + pywebview** | [packaging/02-build-commands.md](packaging/02-build-commands.md#pythonnet--pywebview-打包注意事项) | hidden-import 清单、版本兼容、console 必要性 |
| 5 | **路径适配** | [packaging/03-path-and-meta.md](packaging/03-path-and-meta.md#路径适配sysfrozen-检测) | `sys._MEIPASS` vs `sys.executable.parent` 标准模板 |
| 6 | **路径含空格/特殊字符** | [packaging/03-path-and-meta.md](packaging/03-path-and-meta.md#路径含空格的处理) | PowerShell 打包、Python subprocess、8.3 短路径 |
| 7 | **元数据依赖包** | [packaging/03-path-and-meta.md](packaging/03-path-and-meta.md#元数据依赖包处理copy_metadata) | copy_metadata 钩子、自动检测脚本 |
| 8 | **控制台编码** | [packaging/03-path-and-meta.md](packaging/03-path-and-meta.md#控制台编码windows) | GBK 编码限制、Emoji 替代方案 |
| 9 | **沙箱环境构建** | [packaging/03-path-and-meta.md](packaging/03-path-and-meta.md#沙箱环境构建) | 企业沙箱兼容、tempdir 构建 |
| 10 | **禁用 UPX** | [packaging/03-path-and-meta.md](packaging/03-path-and-meta.md#禁用-upx) | 杀毒误报回避 |
| 11 | **版本信息（version_info.txt）** | [packaging/04-advanced-config.md](packaging/04-advanced-config.md#version_infotxtwindows-文件属性) | VSVersionInfo 格式、字段说明、注入方式 |
| 12 | **构建元数据（build_info.json）** | [packaging/04-advanced-config.md](packaging/04-advanced-config.md#build_infojson程序内部构建元数据) | 自动生成脚本、与应用集成 |
| 13 | **EXE 图标（--icon）** | [packaging/04-advanced-config.md](packaging/04-advanced-config.md#exe-图标--icon) | ICO 格式要求、Pillow 生成脚本、注入方式 |
| 14 | **excludes 配置** | [packaging/04-advanced-config.md](packaging/04-advanced-config.md#excludes-配置详解analysis-排除策略) | 不排除 pip/wheel、安全排除清单 |
| 15 | **冒烟测试** | [packaging/05-smoke-test.md](packaging/05-smoke-test.md) | 完整 Python 脚本、HTTP 200 验证、窗口检测 |
| 16 | **CI/CD 集成** | [packaging/05-smoke-test.md](packaging/05-smoke-test.md#cicd-适应方案) | GitHub Actions、Jenkins Pipeline、无头环境 |
| 17 | **故障排除** | [packaging/06-troubleshooting.md](packaging/06-troubleshooting.md) | 启动闪退、运行慢/内存高、杀毒误报 |
| 18 | **数字签名** | [packaging/06-troubleshooting.md](packaging/06-troubleshooting.md#使用-signtool-进行数字签名) | signtool 命令、时间戳签名、CI/CD 集成 |
| 19 | **常见构建错误** | [packaging/06-troubleshooting.md](packaging/06-troubleshooting.md#常见的构建错误) | Fatal error、ImportError、Failed to execute script |
| 20 | **多端适配总览** | [11-cross-platform.md](11-cross-platform.md) | 后端矩阵（T1 实证）、各 OS 打包矩阵、cefpython3 限制、pywebview 自动 hook、DRY-RUN 铁律 |
| 21 | **macOS 打包（py2app）** | [11-cross-platform.md](11-cross-platform.md#4-macos-打包py2app-路线t4-实证模板) | cocoa 后端、签名/公证、build_macos_py2app.py |
| 22 | **Linux 打包（AppImage）** | [11-cross-platform.md](11-cross-platform.md#5-linux-打包appimage-路线t4-实证模板) | gtk 后端、appimagetool、build_linux_appimage.py |
| 23 | **构建加固（高级陷阱）** | [packaging/07-build-hardening.md](packaging/07-build-hardening.md) | 不稳定 stdhook 覆盖(SubprocessDiedError)、裁剪优于全量收集、.spec 时 CLI flag 非法 |

---

## 快速参考：打包命令速查

```bash
# 标准打包（fasthtml + pywebview 桌面应用）
# 注意：--noupx 必加（铁律#8，回避杀毒误报）；--additional-hooks-dir 指向项目 hook 目录。
# 若项目有函数内懒加载模块（如第三方常驻网关 / 重型 SDK），追加：--hidden-import <懒加载模块名>
# （更优做法：写入 src/pyinstaller_hidden_imports.txt，由 build_windows_exe.ps1 自动读取）。
python -m PyInstaller --onefile --console --noupx ^
  --name MyApp ^
  --collect-submodules fasthtml ^
  --hidden-import clr ^
  --hidden-import webview.platforms.winforms ^
  --hidden-import webview.platforms.edgechromium ^
  --hidden-import webview.platforms.mshtml ^
  --additional-hooks-dir pyinstaller_hooks ^
  --add-data "src;src" ^
  --icon assets/icon.ico ^
  --version-file version_info.txt ^
  --exclude-module unittest ^
  --exclude-module pydoc ^
  --exclude-module tkinter ^
  main.py

# 最小环境打包（推荐：控制体积）
# 构建期工具用 uv pip install 装进独立打包 venv（不写入运行时依赖，也不用 uv add）
python -m venv .build-venv
uv pip install --python .build-venv\Scripts\python.exe python-fasthtml pywebview pythonnet uvicorn
.build-venv\Scripts\python -m PyInstaller --onefile --console --noupx --name MyApp main.py
rmdir /s /q .build-venv

# 纯 Python 构建驱动（零 PowerShell 依赖，AppBuilder 模式；PS 不可用 / 路径含空格 / CI 首选）
# 环境检查→清理→PyInstaller→产物校验→强制冒烟（health-url 全 200 才放行）→清理，一条命令走完
# 已实证：真实 FastHTML+pywebview 应用 46s 构建 17.9MB onefile，打包态 22 项断言 ALL_PASS
<venv>\Scripts\python.exe scripts/build_windows_exe.py --project-dir . --app-name MyApp ^
  --entry src/main.py --health-url http://127.0.0.1:8642/health
```

> **跨平台统一构建驱动**（`scripts/build_cross_platform.py`，零 PowerShell 依赖，三端 MATRIX 已实证）：
> 按 `--platform windows|macos|linux` 生成对应 hidden-import 矩阵；**非当前平台仅 DRY-RUN 命令预演**
> （PyInstaller/py2app 不支持交叉编译）。Windows 实跑产出 onefile，macos/linux 命令正确。
> ```bash
> # 当前平台（如 Windows）实跑
> <venv>/python build_cross_platform.py --entry src/main.py --app-name MyApp
> # 非当前平台仅预演（不构建）
> <venv>/python build_cross_platform.py --platform macos --entry src/main.py --app-name MyApp --dry-run
> ```

> **macOS / Linux 专用驱动**（仅在对应 OS 执行；本 Windows 环境只做 `py_compile` + 平台守卫核验）：
> ```bash
> # macOS（py2app，cocoa 后端）：python build_macos_py2app.py --entry src/main.py --app-name MyApp
> # Linux（PyInstaller onefile → AppImage，gtk 后端）：
> #   python build_linux_appimage.py --entry src/main.py --app-name MyApp
> ```
> 三端 hidden-import 矩阵与完整步骤见 `references/11-cross-platform.md`。

> **上游参考**：pywebview 官方打包指引镜像于 `user_skills/pywebview/scripts/pywebview-pyinstaller.md`（PS 无关），
> 其要点（hidden-import 三件套、webview/lib DLL 打包）已吸收进本文件与 `build_windows_exe.py`/`.ps1`。

---

## 构建期依赖清单（与运行时依赖分清）

> 铁律见 SKILL.md「依赖管理分级」：**运行时依赖**用 `uv add` 写入 `pyproject.toml`；
> **构建期工具**（PyInstaller、pythonnet 等）**严禁写入运行时依赖**，用独立打包 venv 装。

构建 venv（`.build-venv`，打包完即删）应只含：

| 类别 | 包 | 说明 |
|------|-----|------|
| 框架/运行时 | `python-fasthtml`、`pywebview`、`pythonnet`、`uvicorn` | 应用实际运行所需 |
| 打包工具 | `PyInstaller` | 仅构建期，不进运行时依赖 |
| 可选 | 无（界面质检为 pywebview 原生窗口，零额外浏览器依赖） | 界面质检无需额外浏览器 / Chromium |

运行时 `pyproject.toml` 只写业务包（fasthtml / pywebview / 业务库），**不要**出现 `pyinstaller` / `pythonnet`。
构建期依赖用 `uv pip install --python .build-venv/Scripts/python.exe <包>` 装进独立打包 venv。

---

## 打包铁律（最高优先级）

| # | 铁律 | 违背后果 |
|---|------|---------|
| 1 | **必须使用 `--onefile`**，严禁 `--onedir` | 分发时 `_internal/` 缺失导致 EXE 崩溃 |
| 2 | **必须最小 venv 打包** | 体积从 16MB 膨胀至 154MB |
| 3 | **Web 桌面应用必须 `console=True`** | 用户看不到启动日志和地址 |
| 4 | **必须包含 pywebview hidden-import** | 运行时白屏/闪退 |
| 5 | **必须包含 fasthtml collect-submodules** | 路由/组件加载失败 |
| 6 | **必须冒烟测试**（不可跳过） | 打包后是否正常工作不可知 |
| 7 | **"不要排除 pip 和 wheel"** | setuptools 钩子冲突导致包加载失败 |
| 8 | **必须禁用 UPX** | 杀毒软件误报 |
| 9 | **清理旧产物前必须杀残留进程**（`build_windows_exe.ps1` 已实现） | 残留 pywebview 子进程持有 `dist/*.exe` 句柄 → PyInstaller 覆盖时 `PermissionError (WinError 5)` 打包失败 |
| 10 | **函数内懒加载模块必须 `--hidden-import`**（项目 `src/pyinstaller_hidden_imports.txt` 或 `-ExtraHiddenImports`） | 运行时 `ModuleNotFoundError: No module named 'X'`；PyInstaller 打包"成功"、冒烟测试 HTTP 200 仍**假绿**——后台业务子进程（如第三方常驻网关）静默崩溃 |

> **清理前杀残留进程（防御性硬化）**：冒烟测试 `proc.Kill()` 后，pywebview 子进程释放 `dist/<AppName>.exe` 句柄存在竞态，下一轮 PyInstaller 在覆盖该文件时**可能**抛 `PermissionError`（WinError 5）。脚本在清理 `build/ dist/ *.spec` **前**插入「按 `AppName` 终止残留进程 + `WaitForExit(2000)` + `Start-Sleep 1`」，并把 `Remove-Item` 改为「最多重试 3 次、间隔 1s、仍失败则 `exit 1` 显式报错」——**干净失败优于带病进打包**。注：本项目实际构建中**未复现**该 WinError 5，此处为预防性硬化；逻辑本身正确，不建议移除。

---

## 函数内懒加载模块（致命但易漏，铁律 #10）

PyInstaller 只做**静态**分析：它能从入口脚本出发，追踪**模块顶层** `import X` 并打包。但**函数 / 方法体内部**的 `from X import Y`（延迟加载）它**看不到**，不会打包，运行时才报 `ModuleNotFoundError: No module named 'X'`。

**典型踩坑**：某项目在 `launcher.py` 的函数体内 `from <gateway_pkg>.gateway import run_gateway`（为了"GUI 启动轻量"而延迟导入常驻网关内核）。通用 `build_windows_exe.ps1` 不认识项目特有的该模块，未打包它 → EXE 启动后常驻网关子进程崩溃（`ModuleNotFoundError`）——但 uvicorn 仍正常返回 HTTP 200、窗口进程也存在 → **冒烟测试假绿**，直到用户真正使用该功能才发现后台已死。

**铁律**：任何"为保持 GUI 启动轻量而延迟到函数内才导入"的模块（第三方常驻网关、重型 SDK 等），必须显式声明，三选一（通用脚本**不允许硬编码**项目专有模块，保持通用）：

- **推荐**：在项目 `src/pyinstaller_hidden_imports.txt` 写一行模块名（如 `gateway_pkg.gateway`），脚本自动读取并加 `--hidden-import`；
- 或运行脚本时传 `-ExtraHiddenImports gateway_pkg.gateway,gateway_pkg.platforms.api_server,aiohttp,aiohttp.payload`；
- 或直接在 PyInstaller 命令加 `--hidden-import gateway_pkg.gateway`。

### 可选依赖静默导入排查（try/except ImportError 陷阱）

与懒加载同族的隐蔽坑：第三方库常用 `try: import X / except ImportError: X = None` 做**可选依赖静默降级**。打包后若 X 未被收集，库不报错、只是**功能静默缺失**（如 pandas 缺 openpyxl 时 `to_excel` 才报错、requests 缺 chardet 时编码探测退化）——冒烟测试通常发现不了。

**排查方法**：
- 对关键功能路径写「打包态功能断言」（不仅测端点通、还要真正调用一次导出/解析等依赖可选包的功能）；
- 全文检索项目直接依赖中的 `except ImportError`，凡运行时确实需要的可选包，显式加入运行时依赖并（必要时）`--hidden-import`；
- 打包后可用 `python -c "import 可选包"` 等价断言写进冒烟脚本。

---

## 冒烟测试必须验证「业务健康端点」（防假绿）

原冒烟测试只查 **HTTP 200 + 窗口进程**。这对"HTTP 服务正常、但后台业务子进程崩溃"的场景是**假绿**（见上节）。

**铁律**：若应用有后台业务子进程（网关 / Hermes / 工作进程等），必须让冒烟测试验证其**业务健康端点**，任一不可达即 `exit 1` 阻断交付：

- 在项目 `src/health_endpoints.txt` 写一行端点（如 `http://127.0.0.1:8642/health`）；
- 或运行脚本时传 `-HealthCheckUrls http://127.0.0.1:8642/health`；
- 脚本在 HTTP 200 + 窗口就绪**后**，逐个轮询端点（默认 45s 超时 / 个），全部 200 才算通过；否则 `FAIL` + `exit 1`。

> 本项目应用自身已有 `_health_ok()` 轮询 `127.0.0.1:8642/health`，可直接复用该地址作为冒烟端点。

---

## 最小 venv 口径说明（消除文档 / 脚本不一致）

- **主铁律（SKILL.md）**："必须创建最小 venv" = `python -m venv .venv`，即项目运行时 venv 必须**只装真实运行时依赖**（不混装 pytest / 构建工具等）。`build_windows_exe.ps1` 默认就用这个 `.venv` 跑 PyInstaller —— **符合主铁律**。
- **体积优化变体（本文 § 快速参考）**：为把体积从 154MB 压到最小，可用独立 `.build-venv` 只装框架 + PyInstaller，打包完即删。这是**可选优化**，**不是**额外硬性要求。脚本提供 `-BuildVenv <path>` 参数接入此路线；不传则用 `.venv`。
- 二者都满足"最小 venv 打包"铁律。切勿误以为"必须用 `.build-venv`"——`.venv` 同样合规，只要它干净（无无关依赖）。

---

## 零 fork 机制速查（通用脚本读取的项目声明文件）

| 文件 | 作用 | 格式 |
|------|------|------|
| `src/pyinstaller_hidden_imports.txt` | 声明函数内懒加载 / 项目专有模块 | 每行一个模块名，`#` 开头为注释 |
| `src/health_endpoints.txt` | 声明关键业务健康端点（冒烟测试强制验证） | 每行一个 URL |
| `src/pyinstaller_excludes.txt` | 声明额外排除模块（体积优化） | 每行一个模块名 |
| `scripts/hooks` 或 `src/pyinstaller_hooks` | 自定义 PyInstaller hook 目录 | 目录，脚本自动探测 |

---

## 快速定位故障

| 症状 | 排查方向 | 参考文档 |
|------|---------|---------|
| EXE 启动闪退 | DLL 缺失 / hidden-import 遗漏 | [02-build-commands.md#dll-依赖诊断与修复](packaging/02-build-commands.md#dll-依赖诊断与修复) |
| 白屏/无响应 | clr/pythonnet 未声明 | [02-build-commands.md#常见故障](packaging/02-build-commands.md#常见故障) |
| 文件 404 | 路径未用 `sys._MEIPASS` | [03-path-and-meta.md#路径适配sysfrozen-检测](packaging/03-path-and-meta.md#路径适配sysfrozen-检测) |
| 数据库/数据写入失败、EXE 同级目录生成异常文件 | 冻结模式下数据目录取 `sys.executable.parent`（EXE 同级），部署到只读/无写权限目录会失败 | 见下方「冻结模式数据目录」说明 |
| 启动慢 | --onefile 解压延迟 | [06-troubleshooting.md#1-单文件--onefile启动延迟](packaging/06-troubleshooting.md#1-单文件--onefile启动延迟) |
| EXE 启动"成功"但后台子进程崩溃 / `ModuleNotFoundError: No module named 'X'`，HTTP 200 冒烟仍假绿 | 函数内懒加载模块未 `--hidden-import`（PyInstaller 静态分析抓不到） | 见上文「函数内懒加载模块」：在 `src/pyinstaller_hidden_imports.txt` 声明 + 用 `src/health_endpoints.txt` 让冒烟测试抓假绿 |

### 冻结模式数据目录（易踩陷阱）

PyInstaller `--onefile` 运行时，应用代码位于只读临时目录 `sys._MEIPASS`，但**持久化数据（SQLite、用户配置、日志）必须写到可写位置**。常见写法：

```python
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent   # EXE 同级目录
else:
    BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "data" / "app.db"
```

⚠️ **隐患**：`sys.executable.parent` 在以下场景会失败或产生副作用：
- 把 EXE 放到 `C:\Program Files\`（标准用户无写权限）→ 启动即因建库/写库崩溃；
- 多用户共用一台机器 → 数据写在 EXE 旁，互相覆盖。

✅ **推荐做法**：冻结模式下优先用系统可写应用数据目录：

```python
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(os.environ.get("APPDATA", Path(sys.executable).parent)) / "YourApp"
else:
    BASE_DIR = Path(__file__).parent.parent.parent
```

若确实要放 EXE 同级（如单机绿色版），需在文档中明确告知用户「请勿放到只读目录」。

### 应用日志规范：用 logging 落盘，不依赖 print

- 本栈默认 `--console`（铁律 #4），`print` 可见；但**若产品要求改用 `--windowed/--noconsole`，冻结后 `sys.stdout/stderr` 为 `None`，`print` 会直接抛异常或静默丢失**——这是 GUI 打包最常见的"开发正常、EXE 诡异崩溃"来源之一。
- **规范**：应用代码一律用 `logging`（`logging.basicConfig` + `FileHandler` 落盘到数据目录，如 `%APPDATA%\YourApp\logs\app.log`）；`print` 仅允许出现在冒烟/自验证脚本的断言输出（供外部采集 `ALL_PASS`）。
- windowed 模式加固：入口处兜底 `if sys.stdout is None: sys.stdout = open(os.devnull, 'w')`（stderr 同理），防止第三方库内部 print 崩溃。
- 控制台中文乱码提示：Windows 控制台默认 GBK，EXE 输出 UTF-8 中文会显示乱码但**不影响程序逻辑与断言**；日志文件显式 `encoding='utf-8'` 即可。
| 杀毒误报 | UPX / 未签名 | [06-troubleshooting.md#杀毒软件误报](packaging/06-troubleshooting.md#杀毒软件误报) |

---

## Nuitka 替代打包方案（实证：内置 PywebViewPlugin）

> **适用场景**：PyInstaller 打包体积过大、启动慢、或需要 C 级优化的场景。Nuitka 将 Python 编译为 C 后再编译为本机机器码，通常产出更小、更快的二进制。

Nuitka 对 pywebview 有**内置官方插件**（`nuitka/plugins/standard/PywebViewPlugin.py`），`isAlwaysEnabled()` 返回 `True`——在 standalone 模式下**自动激活**，无需手动配置：

- 自动包含目标平台的 pywebview 后端模块（winforms/edgechromium/cocoa/qt/gtk）
- 自动收集 `webview/lib`、`webview/js` 资源
- 自动处理 pythonnet（Windows）/ pyobjc（macOS）/ PyGObject（Linux）依赖

### 基本命令（standalone，非 onefile）

```bash
# 安装 Nuitka（构建期工具，不进运行时依赖）
uv pip install --python .build-venv\Scripts\python.exe nuitka

# Windows standalone 构建
.build-venv\Scripts\python -m nuitka --standalone --follow-imports \
  --include-package=fasthtml \
  --include-package=uvicorn \
  --enable-plugin=pylint-warnings \
  --output-dir=build_nuitka \
  --windows-console-mode=force \
  main.py
# 产物：build_nuitka/main.dist/main.exe（目录形态，非单文件）
```

### Nuitka vs PyInstaller 对比

| 维度 | PyInstaller | Nuitka |
|------|-------------|--------|
| 原理 | 字节码打包 + 运行时解压 | 编译为 C → 本机机器码 |
| 产物形态 | `--onefile` 单文件 EXE | standalone 目录（`main.dist/`） |
| pywebview 支持 | 自带 hook（`__pyinstaller/`） | 内置插件（自动激活） |
| 体积 | 通常 15-30 MB | 通常 20-40 MB（含 C 运行时） |
| 启动速度 | onefile 需解压延迟 | 本机代码直接启动，更快 |
| 反编译风险 | 字节码可被提取 | 编译为 C，难以逆向 |
| 构建速度 | 30-90 秒 | 3-10 分钟（C 编译） |
| 调试 | 错误信息较清晰 | C 编译错误较难定位 |

> ⚠️ **Nuitka 无 `--onefile` 铁律的等价物**：Nuitka 的 standalone 模式产出的是目录（`main.dist/`），不是单文件。若需单文件分发，可用 Nuitka 的 `--onefile` 选项（实验性，启动时自解压到临时目录），但稳定性和兼容性不如 PyInstaller `--onefile`。
> **本技能默认推荐 PyInstaller `--onefile`**；Nuitka 作为性能/安全敏感场景的替代方案。

---

## 构建脚本自身编码纪律

> 构建脚本（`build_windows_exe.py` / `build_windows_exe.ps1` 等）是交付流水线的核心，其自身代码质量直接影响构建可靠性和可维护性。

### 纪律清单

| # | 纪律 | 原因 |
|---|------|------|
| 1 | **使用 type hints**（Python 脚本） | 构建脚本参数复杂，类型标注防止误传 |
| 2 | **禁止裸 `except:`** | 必须写 `except Exception as e:` 并记录 `e`；裸 `except` 会吞掉 `KeyboardInterrupt` / `SystemExit` |
| 3 | **用 `logging` 而非 `print`** | 构建脚本日志应可配置级别、可重定向到文件 |
| 4 | **用 `pathlib.Path` 而非字符串拼接** | 跨平台路径安全，避免 `\` / `/` 混用 |
| 5 | **`subprocess` 必须设 `timeout`** | PyInstaller 可能挂起（如等待 DLL），无 timeout 会永久阻塞 CI |
| 6 | **`subprocess.run` 检查 `returncode`** | 不要假设子进程成功，显式 `check=True` 或手动判断 |
| 7 | **函数职责单一** | 构建、清理、冒烟、校验各自独立函数，不混在一个 `main()` 里 |

### 示例：规范的构建脚本骨架

```python
#!/usr/bin/env python3
"""Build script: PyInstaller onefile for FastHTML + pywebview desktop app."""
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def run_pyinstaller(project_dir: Path, app_name: str, entry: Path) -> bool:
    """Execute PyInstaller build. Returns True on success."""
    cmd = [
        sys.executable, '-m', 'PyInstaller', '--onefile', '--console', '--noupx',
        '--name', app_name,
        '--collect-submodules', 'fasthtml',
        '--hidden-import', 'clr',
        '--hidden-import', 'webview.platforms.winforms',
        '--hidden-import', 'webview.platforms.edgechromium',
        str(entry),
    ]
    try:
        result = subprocess.run(cmd, cwd=str(project_dir), timeout=600, check=False)
        if result.returncode != 0:
            logger.error('PyInstaller failed with exit code %d', result.returncode)
            return False
        logger.info('Build succeeded: dist/%s.exe', app_name)
        return True
    except subprocess.TimeoutExpired:
        logger.error('PyInstaller timed out after 600s')
        return False
    except Exception as e:
        logger.error('Build error: %s', e, exc_info=True)
        return False

def main() -> int:
    project_dir = Path(__file__).parent
    if not run_pyinstaller(project_dir, 'MyApp', project_dir / 'src' / 'main.py'):
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
```

---

## `--exclude-module` 的有效性边界

> PyInstaller 的 `--exclude-module` 常被误用为"减小体积的万能工具"。实际上，它的效果受模块依赖图约束：

- **仅当被排除模块不被任何已打包模块间接引用时才有效**。若模块 A（已打包）`import B`，则即使指定 `--exclude-module B`，PyInstaller 仍会把 B 打包进来（依赖图强制收集）。
- **常见无效排除**：`--exclude-module tkinter` 看似安全，但如果 pythonnet / 某些 GUI 库间接引用了 tkinter 相关模块，排除静默无效。
- **有效排除示例**：`--exclude-module unittest` / `--exclude-module pydoc` / `--exclude-module test`——这些是标准库测试/文档工具，几乎不会被运行时代码间接引用。
- **验证方法**：构建后用 `pyinstaller --onefile ... 2>&1 | findstr "WARNING"` 查看 PyInstaller 的排除警告；或对比加/不加 `--exclude-module` 的产物体积，若体积不变则排除无效（被依赖图拉回）。

> **体积优化正确顺序**：① 最小 venv 打包（铁律 #2，最有效）；② `--exclude-module` 仅排除确认无间接依赖的标准库模块；③ `--noupx`（铁律 #8，非体积优化但必加）；④ 裁剪 `--collect-submodules` 范围（仅 fasthtml，不盲目全量收集）。切勿依赖 `--exclude-module` 做主要体积优化手段。
