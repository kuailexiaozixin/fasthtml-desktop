# 打包命令与参数说明

> 本文档覆盖 PyInstaller 打包命令、参数详解、DLL 依赖诊断与修复、
> pythonnet + pywebview 混合打包注意事项。

---

## 铁律：严禁使用 --onedir 模式

**所有 fasthtml-desktop 项目的 EXE 必须使用 `--onefile`（单文件模式），严禁使用 `--onedir`（目录模式）。**

| 模式 | EXE 形态 | 是否允许 | 原因 |
|------|---------|---------|------|
| `--onefile` | 单个 `.exe` 文件，自包含 | ✅ 强制使用 | 用户拿到即可运行，无需额外文件 |
| `--onedir` | 目录内含 EXE + `_internal/` 依赖 | ❌ 禁止 | 依赖文件散落，移动/分发时易遗漏 `_internal/` 导致崩溃 |

`--onedir` 模式下 EXE 只是一个引导加载器（bootloader），真正的依赖（`python312.dll`、`.pyd` 模块等）存放在 `_internal/` 目录中。移走 `_internal/` 后 EXE 立即崩溃。**这违背了桌面工具"双击即用"的基本交付原则。**

> 验收标准：`dist/` 目录下只有 `.exe` 文件和运行时目录（`logs/`、`data/`、`downloads/`），不得出现 `_internal/` 目录。

---

## 完整打包命令

```bash
python -m PyInstaller --onefile --console ^
  --name MyApp ^
  --collect-submodules fasthtml ^
  --hidden-import clr ^
  --hidden-import webview.platforms.winforms ^
  --hidden-import webview.platforms.edgechromium ^
  --additional-hooks-dir pyinstaller_hooks ^
  --add-data "src;src" ^
  --icon assets/icon.ico ^
  --version-file version_info.txt ^
  --exclude-module unittest ^
  --exclude-module pydoc ^
  --exclude-module tkinter ^
  main.py
```

### 参数说明

| 参数 | 作用 |
|------|------|
| `--onefile` | 单文件 EXE |
| `--console` | Web 桌面应用必须显示终端（用户查看启动日志和地址） |
| `--name` | 输出 EXE 文件名 |
| `--collect-submodules fasthtml` | FastHTML 路由/组件子模块不会被导入分析完全覆盖 |
| `--hidden-import clr` | pywebview 的 Edge 模式依赖 pythonnet |
| `--hidden-import webview.platforms.edgechromium` | PyInstaller 漏扫平台模块 |
| `--hidden-import webview.platforms.winforms` | pywebview WinForms 回退模式 |
| `--additional-hooks-dir pyinstaller_hooks` | 加载 custom hook（元数据包） |
| `--add-data "src;src"` | 包含业务代码目录 |
| `--icon assets/icon.ico` | 设置 EXE 图标（参见 [04-advanced-config.md](04-advanced-config.md)） |
| `--version-file version_info.txt` | 注入 Windows 版本信息（参见 [04-advanced-config.md](04-advanced-config.md)） |
| `--exclude-module` | 排除不必要的模块减小体积（注意：**不要排除 pip 和 wheel**） |

---

## 常见故障

| 症状 | 根因 | 修复 |
|------|------|------|
| 打包后运行白屏/无响应 | `clr` 或 `pythonnet` 未声明 hidden-import | 添加 `--hidden-import clr` |
| `ModuleNotFoundError: webview.platforms.edgechromium` | PyInstaller 漏扫平台模块 | 添加 `--hidden-import webview.platforms.edgechromium` |
| 打包后 `serve()` 卡死 | `reload=True` 冻结后失效 | 改为 `uvicorn.run(app, reload=False)` |
| 静态文件 404 | 打包后路径变化 | 必须全部内联 |

---

## DLL 依赖诊断与修复

pywebview + pythonnet 组合在 PyInstaller 打包后，常见的崩溃原因是系统 DLL 缺失。
PyInstaller 的二进制依赖分析器不会自动追踪 `ctypes.CDLL()` 动态加载的 DLL。

### 诊断步骤

```bash
# 1. 检查 _ctypes 是否正常加载（注意：pythonnet 3.1 / pywebview 6 实际依赖 libffi-8.dll，旧文档写的 ffi-8.dll 已不成立）
python -c "import ctypes; print('libffi-8.dll:', ctypes.CDLL('libffi-8.dll'))"

# 2. 检查 _ssl 是否正常（pythonnet 依赖 ssl）
python -c "import ssl; print(ssl.OPENSSL_VERSION)"

# 3. 检查 clr 模块是否完整
python -c "import clr; print('clr OK', clr.__file__)"

# 4. 完整诊断：检查所有可能缺失的 DLL
python -c "
import sys, pathlib
dlls = ['libffi-8.dll', 'libcrypto-3-x64.dll', 'libssl-3-x64.dll']
python_dir = pathlib.Path(sys.base_prefix)
for dll in dlls:
    found = list(python_dir.rglob(dll))
    if found:
        print(f'[OK]   {dll} -> {found[0]}')
    else:
        print(f'[FAIL] {dll} -> 未找到，打包后可能崩溃')
"
```

### 修复方案

如果诊断发现 DLL 缺失，使用 `--add-binary` 显式打包到 EXE：

```bash
# 找到 Python 环境中的 DLL 目录
python -c "import sys; print(sys.base_prefix)"
# 输出示例：C:\Users\<user>\AppData\Local\Programs\Python\Python313

# 注意：DLL 实际名称/位置因 Python 发行版而异：
#   - 标准安装：<base>/Library/bin/libffi-8.dll / libcrypto-3-x64.dll / libssl-3-x64.dll
#   - 嵌入式(cpython-3.13-windows-x86_64-none)：<base>/DLLs/libffi-8.dll / libcrypto-3-x64.dll / libssl-3-x64.dll
# 推荐用 build_windows_exe.ps1 的递归搜索自动定位，不要硬编码 Library\bin。
# 下面以标准安装为例（实际请按 sys.base_prefix 递归查找结果替换路径）：
python -m PyInstaller --onefile --console ^
  --add-binary "%PYTHON_HOME%\Library\bin\libffi-8.dll;." ^
  --add-binary "%PYTHON_HOME%\Library\bin\libcrypto-3-x64.dll;." ^
  --add-binary "%PYTHON_HOME%\Library\bin\libssl-3-x64.dll;." ^
  ...
```

`%PYTHON_HOME%` 替换为 Python 安装目录。如果使用 `.venv`，DLL 仍在系统 Python 的 `Library/bin/` 下，不在 `.venv` 中。

### 自动诊断脚本

在项目 `scripts/` 目录中保存以下脚本，打包前运行：

```python
# scripts/check_dlls.py
import sys, pathlib

PY = pathlib.Path(sys.base_prefix)
DLL_DIR = PY / "Library" / "bin"
REQUIRED = ["libffi-8.dll", "libcrypto-3-x64.dll", "libssl-3-x64.dll"]

print("=== DLL 依赖检查 ===")
all_ok = True
for dll in REQUIRED:
    found = list(PY.rglob(dll))
    if found:
        print(f"  [OK] {dll} -> {found[0]}")
    else:
        print(f"  [FAIL] {dll} -> 缺失，打包后 EXE 可能崩溃")
        all_ok = False

if not all_ok:
    print(f"\n修复：使用 --add-binary 将缺失 DLL 打包进 EXE")
else:
    print("\n所有 DLL 依赖正常，可以继续打包。")
```

### 崩溃场景速查

| 症状 | 缺失 DLL | 修复 |
|------|---------|------|
| `ImportError: DLL load failed while importing _ctypes` | `libffi-8.dll`（旧文档误写作 `ffi-8.dll`） | `--add-binary "<py>/DLLs/libffi-8.dll;."`（路径以实际查找结果为准，标准安装为 `<py>/Library/bin/libffi-8.dll;.\`） |
| `ModuleNotFoundError: No module named '_ssl'` | `libcrypto-3-x64.dll` + `libssl-3-x64.dll` | 同时添加两个 openssl DLL |
| `SystemError: <class '_socket.socket'>` | `_socket.pyd` 依赖的 SSL DLL | 检查 `libcrypto-*` 版本是否匹配 |
| `ModuleNotFoundError: No module named '_lzma'` | `liblzma.dll`（Conda 环境典型） | `--add-binary "<conda>/Library/bin/liblzma.dll;."` 或改用官方 Python |
| `xml.parsers.expat` 相关解析错误 / `pyexpat` 导入失败 | `libexpat.dll`（Conda 环境典型） | `--add-binary "<conda>/Library/bin/libexpat.dll;."` 或改用官方 Python |

### Conda 环境 DLL 依赖链（Windows 特有，强烈建议规避）

Conda 发行版的 C 扩展 `.pyd`（如 `pyexpat.pyd`、`_lzma.pyd`、`_sqlite3.pyd`）链接的是 Conda 自带 `Library/bin/` 下的 DLL，PyInstaller **不会自动收集**它们，导致 EXE 在无 Conda 的机器上崩溃。已知易缺清单：`sqlite3.dll`、`libffi-8.dll`、`libexpat.dll`、`libcrypto-3-x64.dll`、`libssl-3-x64.dll`、`liblzma.dll`。

**本技能栈的处理原则**：
1. **首选**：打包一律用 python.org 官方 Python 创建最小 venv（本技能主铁律），从根上规避 Conda DLL 链问题；
2. 若被迫在 Conda 环境打包：将上述 DLL 逐个 `--add-binary "<conda_env>/Library/bin/<dll>;."`（或写入 .spec 的 `binaries`），并把 `check_dlls.py` 的 `REQUIRED` 扩充为上面的完整清单；
3. 打包后必须在**干净机器/干净 PATH**（不含 Conda）下跑冒烟测试，否则系统 PATH 里的 Conda DLL 会掩盖缺失。

---

## pythonnet + pywebview 打包注意事项

pywebview 在 Windows 上使用 Edge Chromium 模式时，底层依赖 `pythonnet`（.NET 互操作库）。
`pythonnet` 的 `clr` 模块在 PyInstaller 打包环境中行为特殊。

### 必须的 hidden-import 与 --add-binary

```bash
--hidden-import clr
--hidden-import webview.platforms.edgechromium
--hidden-import webview.platforms.winforms
--add-binary "<python_dir>\DLLs\libffi-8.dll;."
--add-binary "<python_dir>\DLLs\libcrypto-3-x64.dll;."
--add-binary "<python_dir>\DLLs\libssl-3-x64.dll;."
# 注意：标准安装路径为 <python_dir>\Library\bin\ 而非 DLLs\；请以 sys.base_prefix 递归查找为准
```

`<python_dir>` 替换为 Python 安装目录（通过 `python -c "import sys; print(sys.base_prefix)"` 查看）。

### pythonnet 版本兼容性

| pythonnet 版本 | Python 版本 | 备注 |
|---------------|------------|------|
| 3.0.x | 3.8 - 3.11 | 稳定，推荐 |
| 3.0.4+ | 3.12 | 实验性支持 |
| 3.0.5+ | 3.13 | 需要额外 DLL 处理 |

> 如果使用 Python 3.13 + pythonnet 3.1+，打包后必须手动补充 `libffi-8.dll`（注意名称是 libffi-8.dll，不是 ffi-8.dll；见 DLL 诊断章节）。

### console=True 是必要的

pywebview + pythonnet 的 EXE **必须**设置 `--console`：

| 模式 | 行为 |
|------|------|
| `console=True` | 终端窗口显示启动日志，用户可确认服务就绪 |
| `console=False` | 隐藏窗口，进程可能在后台静默崩溃，用户无任何反馈 |

### pywebview + pythonnet 打包检查清单

- [ ] `--hidden-import clr` 已添加
- [ ] `--hidden-import webview.platforms.edgechromium` 已添加
- [ ] `--hidden-import webview.platforms.winforms` 已添加
- [ ] `--console` 已设置
- [ ] 打包前执行 DLL 诊断脚本确认 `libffi-8.dll` 可达（旧文档误为 ffi-8.dll）
- [ ] EXE 在无 Python 的测试机上验证过
- [ ] 如果使用 Python 3.13，手动添加 `libcrypto-3-x64.dll` + `libssl-3-x64.dll`

---

## FastHTML + Pydantic AI 组合备注

如果应用用到了 Pydantic AI（如接入 LLM），打包时额外注意：

```bash
pip install "pydantic-deep[cli]" PyInstaller
python -m PyInstaller --onefile --console \
  --name MyApp \
  --collect-submodules fasthtml \
  --additional-hooks-dir pyinstaller_hooks \
  main.py
```

应用入口必须 `reload=False`，Pydantic AI 模型配置属于该技能的主题。

---

## 浏览器自动打开模板

```python
threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
```

> 注：pywebview 壳已自带浏览器窗口，自动打开系统浏览器这一步不是必需的。
> 可以保留作为备选（当 pywebview 窗口无法打开时用户可通过浏览器访问）。
