# 环境与执行规范

## PowerShell 5.1 红线

- 所有 `.ps1` 与 `.ps1.tmpl` 默认视在 `Windows PowerShell 5.1` 下执行，禁止使用仅 PowerShell 7+ 支持的参数
- 只要创建、修改、复制、分发 `.ps1` 或 `.ps1.tmpl`，一律使用 `UTF-8 with BOM + CRLF`
- 严禁使用 `UTF-8 without BOM` 保存 PowerShell 文件

## AI 生成源码的编码铁律（新增，防止中文源码乱码）

- **`.py` / 纯 Python 源码**：一律 UTF-8 无 BOM（PEP 3120）。禁止用 PowerShell `Set-Content` 写入任何 `.py` 文件——`Set-Content` 在 Windows PowerShell 5.1 下默认编码非 UTF-8，会把中文写成乱码（实战中曾导致测试文件列名损坏、整批测试失败）。
- **写入 .py 的正确方式**：① 用支持显式 UTF-8 的工具整体写入；② `Out-File -Encoding utf8`（PowerShell 5.1 的 utf8 不带 BOM，符合 PEP）；③ `python -c "open(f,'rb').read(3)"` 核对头部无 BOM 标记。
- **`.ps1`**：维持 UTF-8 with BOM + CRLF（见上）。两者不可混淆：BOM 对 .ps1 必需，对 .py 必须无 BOM。
- **核对方法**：写入后用 `python -c "open(f,'rb').read(3)"` 确认 .py 头部无 EF BB BF、.ps1 头部有。

## .sh 包装脚本执行方式

AI 运行环境（Git Bash）不能直接调用 `powershell.exe`，因此每个 `.ps1` 脚本都有对应的 `.sh` 包装脚本：

| .ps1 脚本 | .sh 包装 | 用途 |
|-----------|---------|------|
| `ensure_uv_env.ps1` | `ensure_uv_env.sh` | 环境准备：安装 uv、配置镜像、安装 Python |
| `bootstrap_project.ps1` | `bootstrap_project.sh` | 项目初始化：生成 web-desktop-exe 骨架 |
| `build_windows_exe.ps1` | `build_windows_exe.sh` | 打包：PyInstaller 构建 EXE |

包装原理：`.sh` 通过 `dash -c 'powershell.exe ...'` 间接调用 PowerShell。

**执行优先级**：`.sh` 版本 > `.ps1` 版本。AI 默认执行 `.sh` 包装脚本。
无 `dash` 环境时，可通过 tclsh/perl 替代：

```tcl
# tclsh 替代方案
exec powershell.exe -ExecutionPolicy Bypass -File script.ps1
```

## 环境初始化（铁律）

### ensure_uv_env.ps1

任何新建项目的第一步。脚本会自动：
1. 检测是否已安装 uv
2. 如未安装，自动下载安装
3. 探测最快的中国镜像源
4. 配置环境变量
5. 安装指定版本 Python

**禁止跳过此步骤**，禁止 AI 手动执行 `uv init`、`uv python install` 等零散命令来代替。

### 创建虚拟环境

项目目录创建后，立即执行：

```bash
python -m venv .venv
```

**此步骤不可跳过。** 如果不创建 venv 直接装包，打包时 PyInstaller 会扫描全环境导致体积膨胀（实践中 16MB → 154MB 的差距）。

### 依赖管理

- 新增第三方包：`uv add <包名>`（自动写入 `pyproject.toml` 并安装到当前环境）
- **严禁使用 `pip install`**，这会破坏环境隔离
- `uv sync` 仅用于换机器或给别人用项目时还原环境，日常开发不需要

本技能基础依赖：

```toml
[project]
dependencies = [
    "python-fasthtml>=0.6.0",  # Web 框架
    "pywebview>=5.0",          # 桌面窗口壳
    "pythonnet>=3.0",          # pywebview Edge 模式依赖
    "uvicorn>=0.30",           # FastHTML 生产运行
    "requests>=2.31",          # HTTP 客户端（API 调用、冒烟测试）
    "pydantic>=2.0",           # 数据模型验证
]
```

常用业务依赖（按需追加）：

| 包名 | 用途 | 添加命令 |
|------|------|---------|
| `pandas` | 数据分析、CSV/Excel 处理 | `uv add pandas` |
| `openpyxl` | Excel 读写（pandas 引擎） | `uv add openpyxl` |
| `beautifulsoup4` | HTML 解析、网页抓取 | `uv add beautifulsoup4` |
| `aiohttp` | 异步 HTTP（高并发爬取） | `uv add aiohttp` |

### pywebview 版本与功能验证

pywebview 为关键运行时依赖，打包前必须确认版本兼容：

```bash
python -c "import webview; print(f'pywebview {webview.__version__}')"
# 预期输出：pywebview 5.x 或 6.x
```

不同 pywebview 版本对特定功能的支持差异：

| 功能 | pywebview ≥5.0 | pywebview ≥6.0 | 验证命令 |
|------|---------------|---------------|---------|
| 基础窗口（Edge Chromium） | ✅ | ✅ | `python -c "import webview; webview.create_window('t', 'about:blank')"`（需 GUI）|
| 多窗口 | ✅ | ✅ | `webview.create_window()` 多次调用 |
| 系统托盘 | ⚠️ 有限支持 | ✅ 完整支持 | `python -c "import webview; print(hasattr(webview, 'tray'))"` |
| JS 桥接 | ✅ | ✅ | `window.evaluate_js()` |
| 文件对话框 | ✅ | ✅ | `webview.windows[0].create_file_dialog()` |
| 调试模式（DevTools） | ✅ | ✅ | `webview.start(debug=True)` |
| Cookie 管理 | ⚠️ 需手动 | ✅ `webview.Cookie` | `python -c "import webview; print(hasattr(webview, 'Cookie'))"` |

如果运行环境中 pywebview 版本过低，升级命令：

```bash
uv add pywebview@latest
```

如果 pywebview 缺失 WebView2 运行时，安装 Edge WebView2 Runtime：

```
https://developer.microsoft.com/en-us/microsoft-edge/webview2/
```

打包所需 hidden-imports（`pyproject.toml` 中的 `[tool.pyinstaller]` 或 `.spec` 文件中添加）：

```python
hiddenimports = [
    'clr',                                  # pythonnet
    'webview.platforms.edgechromium',        # pywebview Edge
    'webview.platforms.winforms',           # pywebview WinForms
]
```

### 中国网络环境

涉及 `uv`、Python 与包安装时，默认先设置镜像再执行：

```bash
# 设置 uv 镜像
uv config set index-url https://mirrors.aliyun.com/pypi/simple/
```

---

## 命令代执行规则

- `uv init`、`uv add`、`uv sync`、`uv run`、`ruff`、`mypy`、`pytest`、`pyinstaller` — 默认由 AI 发起
- 如果运行命令需要系统授权、联网安装或写文件，AI 负责发起，用户只需点"允许"
- 除非用户明确要求学习命令行，否则不要把"请你在终端执行以下命令"当成默认答案

## 项目初始化流程

```bash
# 1. 环境就绪（优先 .sh，无 dash 环境再用 .ps1）
bash ./scripts/ensure_uv_env.sh

# 2. 创建项目并进入
mkdir my-desktop-app && cd my-desktop-app
python -m venv .venv

# 3. 运行 bootstrap 生成骨架
bash ../scripts/bootstrap_project.sh -ProjectDir . -AppName "MyApp"

# 4. 补充业务依赖
uv add pandas openpyxl   # 按需
```
