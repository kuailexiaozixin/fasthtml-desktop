# 11 · 多端适配总览（fasthtml + pywebview 不锁死 Edge）

> **本文档回答一个问题**：FastHTML 除了 Windows 端，能否适配 macOS / Linux？
> 结论：**能，且业务代码零改动**。差异只在「桌面壳后端」与「打包产物形态」。
> 本文档全部结论来自**真实源码内省（T1）+ 真实应用跑通全流程（T2 开发态 / T3 打包态 / T4 产物态）**，
> 非推测。实证环境：Windows 11 + Python 3.13.14 + pywebview 6.2.1 + python-fasthtml 0.14.9 + PyInstaller 6.21.0。

---

## 0. 核心结论（一句话）

- FastHTML 是**纯 Python ASGI/uvicorn** 框架，框架层 100% 跨平台，**磁盘上没有单一静态 HTML 入口**（由 uvicorn 按请求实时渲染）。
- pywebview 是**跨平台桌面壳**，按操作系统**自动选择**原生 WebView 后端；业务代码（FastHTML 路由 + `main.py` 壳）三端**完全相同**。
- 唯一差异：① 壳所用后端（Windows=WinForms+WebView2 / macOS=cocoa / Linux=gtk）；② 打包产物（Windows EXE / macOS .app / Linux AppImage）。
- **CEF 后端（cefpython3）可用但受 Python 版本约束**：cefpython3 仅支持到 **Python 3.9**；现代 Python（≥3.10）下不可作为跨平台一致后端——属 **P1 谨慎项**，需单独在 Python 3.9 环境验证。

---

## 1. 后端矩阵（T1 源码内省铁证）

> 证据来源：`introspect_backends.py` 对 `pywebview 6.2.1` 的 `guilib.py` + `platforms/*.py` 做 `importlib` + `inspect` 内省（留档 `introspect_backends.out.txt`）。
> **注意：`'winforms'` 不是合法的 `gui` 值**（`GUI_TYPES` 白名单不含它）；winforms 是 Windows 的**宿主模块**，renderer 由 winforms 内部再选 edgechromium / mshtml / cef。

### 1.1 合法 `gui` 白名单（环境变量 `PYWEBVIEW_GUI` 只接受这些）

```
GUI_TYPES = ['qt', 'gtk', 'cef', 'mshtml', 'edgechromium', 'android', 'cocoa']
```

### 1.2 平台选择逻辑（guilib.py，不传 gui 时的默认链）

| 平台 | 默认后端选取顺序（实测源码） | 恒定宿主 |
|------|------------------------------|----------|
| Darwin (macOS) | `[cocoa, qt]`（先 cocoa；失败回退 qt） | cocoa（WebKit/WKWebView） |
| Linux / OpenBSD | `[gtk, qt]`（KDE_FULL_SESSION 时 `[qt, gtk]`） | gtk（WebKit2） |
| Windows | `[winforms]`（恒定，winforms 内部再选 renderer） | winforms |
| Android | `[android]` | android |

> **关键**：**不要**硬编码 `gui='edgechromium'`（旧 Windows-only 写法）。跨平台应用应传 `gui=None` 信任官方默认链，业务代码三端通用。

### 1.3 Windows renderer 选择（winforms.py 内部）

```
is_cef      = forced_gui == 'cef'
is_chromium = (not is_cef) and _is_chromium() and forced_gui != 'mshtml'
renderer    = 'cef'      if is_cef
            = 'edgechromium'  if is_chromium   # WebView2 运行时可用时
            = 'mshtml'                        # 兜底（Trident/IE 内核）
```

### 1.4 各后端外部依赖矩阵（T1 I4）

| 后端 | 外部依赖（顶层 import） | 适用平台 | 备注 |
|------|--------------------------|----------|------|
| `cocoa` | AppKit, Foundation, PyObjCTools, WebKit, objc | macOS | pyobjc 系 |
| `gtk` | gi | Linux | PyGObject；`gi.repository.Gtk` / `gi.repository.WebKit2` |
| `qt` | qtpy | 跨平台 | 回退链；需 `pip install qtpy` + Qt 绑定 |
| `edgechromium` | Microsoft, System, winreg | Windows | WebView2 运行时（系统自带/可分发） |
| `mshtml` | System, WebBrowserInterop | Windows | IE/Trident 兜底 |
| `cef` | cefpython3, webbrowser | 跨平台 | ⚠ **仅 Python ≤3.9**（cefpython3 限制） |
| `winforms` | Microsoft, System, winreg | Windows | 宿主（恒定） |
| `android` | android, jnius | Android | 移动端 |

---

## 2. 业务代码三端通用（T2 实证）

> 证据来源：`main_multi.py`（后端无关壳），开发态实跑 **27 项断言 ALL_PASS，EXIT=0**。
> 关键修复点：业务层与单端 demo 完全相同；`select_backend()` 返回 `None`（信任官方默认链）；
> 新增 M 组断言验证「GUI_TYPES 白名单 / winforms 非合法 gui / 实际宿主模块 == 平台预期 / renderer 实证」。

- **入口壳 `main.py` 三端共用同一份**（仅 `start()` 的 `gui=None`）。
- **FastHTML 路由、页面、组件、HTMX、js_api 三端完全相同**。
- 跨平台 demo 断言示例（`main_multi.py`）：
  - `M1`：本机 `GUI_TYPES` == `['qt','gtk','cef','mshtml','edgechromium','android','cocoa']`
  - `M1b`：`'winforms' not in GUI_TYPES`（纠正"硬编码 winforms 为 gui"的常见错误）
  - `M2`：实际宿主模块 == 平台预期（`webview.platforms.winforms` on Windows / `cocoa` on macOS / `gtk` on Linux）
  - `M3`：`renderer` 实证（Windows + WebView2 → `edgechromium`）

**含义**：你写一次 Web 应用，换台机器（mac/linux）打包即可分发，**无需改业务代码**。

---

## 3. 跨平台构建矩阵（T3 实证）

> 证据来源：`build_cross_platform.py` 三端 MATRIX（基于 §1.4 依赖矩阵），Windows 目标在最小 venv 实跑
> 产出 `MultiDemo.exe` 17.9 MB，EXE 自跑冒烟 **ALL_PASS / exit=0**；macos/linux 目标在本 Windows 环境
> 只做 **DRY-RUN 命令预演**（PyInstaller 不支持交叉编译），命令生成正确。

| 目标 | hidden-import（后端平台子模块） | collect | extra | 产物 |
|------|----------------------------------|---------|-------|------|
| **windows** | `webview.platforms.winforms` `webview.platforms.edgechromium` `webview.platforms.mshtml` `clr` | `--collect-submodules fasthtml` `--collect-data certifi` | `--noupx` | `dist/<App>.exe`（onefile, console） |
| **macos** | `webview.platforms.cocoa` `webview.platforms.qt` `AppKit` `Foundation` `WebKit` `objc` `PyObjCTools.AppHelper` | `--collect-submodules fasthtml` `--collect-data certifi` | （GUI 可加 `--windowed` 出 .app） | `dist/<App>`（onefile） |
| **linux** | `webview.platforms.gtk` `webview.platforms.qt` `gi` `gi.repository.Gtk` `gi.repository.WebKit2` | `--collect-submodules fasthtml` `--collect-data certifi` | `--noupx` | `dist/<App>`（onefile）→ AppImage |

### 3.1 pywebview 自带 PyInstaller hook（重要：无需手动 webview hidden-import）

`webview/__pyinstaller/hook-webview.py` 通过 `entry_points.txt` 的 `[pyinstaller40] hook-dirs` **被 PyInstaller 自动发现**：
- 全平台：`--collect-data-files webview/js`
- Windows：`--collect-data-files webview/lib` + `--collect-dynamic-libs webview`（含 WebView2 互操作 DLL）

→ **技能层不需手动 `--hidden-import webview`**；只需补"目标平台实际会用的后端平台子模块"（上表）。

### 3.2 DRY-RUN 铁律（跨平台不可交叉编译）

- PyInstaller / py2app **不支持交叉编译**。在 **非目标 OS** 上构建（如 Windows 构建 macOS dmg）只能生成**命令预演**，**严禁伪造运行结果**。
- `build_cross_platform.py` 实现：`target != CURRENT` 时 `build()` 返回 `None`（**不返回 `Path()`**，否则 `Path()` 即 `.` 会 truthy 误入冒烟）、`clean()` 跳过（避免删并行真实构建的 `build/`）。
- 真实打包**必须在对应 OS 上执行**。

---

## 4. macOS 打包（py2app 路线，T4 实证模板）

> 证据来源：`setup_py2app.py` + `build_macos_py2app.py`，在 Windows 环境做 `py_compile` 语法核验通过 +
> 平台守卫分支验证（`sys.platform != "darwin"` → exit 1，正确）；真实 GUI 构建**仅能在 macOS 执行**（诚实边界）。
> 另可走 PyInstaller onefile（§3 macos 行）。

### 4.1 前置（macOS）

```bash
python3 -m venv venv && source venv/bin/activate
pip install python-fasthtml pywebview pyobjc py2app
```

### 4.2 构建（build_macos_py2app.py）

```bash
python build_macos_py2app.py --entry main.py --app-name MyApp [--icon assets/icon.icns]
# 产物：dist/MyApp.app
# 校验：./dist/MyApp.app/Contents/MacOS/MyApp   # demo 自跑断言 ALL_PASS
```

### 4.3 setup 关键参数（py2app）

```python
OPTIONS = {
    "argv_emulation": False,   # True 会与 Cocoa 事件循环冲突
    "strip": True,
    "packages": ["fasthtml", "webview", "uvicorn", "starlette"],  # 动态 import 重的包整包收集
    "includes": ["webview.platforms.cocoa"],
    "plist": {
        "CFBundleName": "MyApp",
        "CFBundleIdentifier": "com.example.myapp",
        "NSHighResolutionCapable": True,
    },
}
# FastHTML 是纯 SSR，无静态资源目录 → DATA_FILES = []（如有 assets/ 再加）
```

### 4.4 签名与公证（macOS 分发必需）

```bash
codesign --deep --force --options runtime \
  --sign "Developer ID Application: <name>" dist/MyApp.app
xcrun notarytool submit <zip> --keychain-profile <profile> --wait \
  && xcrun stapler staple dist/MyApp.app
```

---

## 5. Linux 打包（AppImage 路线，T4 实证模板）

> 证据来源：`build_linux_appimage.py`，Windows 环境 `py_compile` + 平台守卫（`sys.platform != "linux"` → exit 1）通过；真实构建仅能在 Linux 执行（诚实边界）。

### 5.1 前置（Debian/Ubuntu）

```bash
sudo apt install python3-venv libgirepository1.0-dev gir1.2-webkit2-4.1 libgtk-3-dev
python3 -m venv venv && . venv/bin/activate
pip install python-fasthtml pywebview PyGObject pyinstaller
# appimagetool: https://github.com/AppImage/appimagetool/releases （chmod +x，加入 PATH）
```

### 5.2 构建（build_linux_appimage.py）

```bash
python build_linux_appimage.py --entry main.py --app-name MyApp [--icon assets/icon.png]
# 流程：PyInstaller onefile → AppDir(usr/bin + AppRun + .desktop + icon) → appimagetool
# 产物：dist/MyApp-x86_64.AppImage
# 校验：./dist/MyApp-x86_64.AppImage   # demo 自跑断言 ALL_PASS
```

---

## 6. CEF 后端（cefpython3）限制 —— P1 谨慎项

- `cefpython3` **仅支持到 Python 3.9**（实测：Python 3.13.14 导入即报 `Exception: Python version not supported: 3.13.14`）。
- 因此：**现代 Python（≥3.10）下不能把 CEF 当作跨平台一致后端**。
- 若确实需要在 Python 3.9 环境用 CEF（`gui='cef'`），须：
  1. 单独建 Python 3.9 最小 venv 并 `pip install cefpython3`；
  2. 打包 hidden-import 追加 `webview.platforms.cef` + `cefpython3`；
  3. 在目标平台实跑验证（本技能未覆盖该路径的实跑证据）。
- 默认推荐：各平台用官方默认后端（Windows=WebView2 / macOS=cocoa / Linux=gtk），无需 cefpython3。

### 6.1 Qt 后端限制（QtWebKit vs QtWebEngine）

pywebview 的 Qt 后端（`gui='qt'`）依赖 `qtpy` + Qt 绑定（PyQt5/PyQt6/PySide2/PySide6）。Qt Web 渲染层有两种实现：

| 渲染层 | 来源 | DevTools 调试 | 备注 |
|--------|------|--------------|------|
| **QtWebEngine**（Chromium 内核） | `pip install PyQtWebEngine` / `PySide6-Addons` | ✅ 支持 | 现代默认；`debug=True` 可开 DevTools |
| **QtWebKit**（旧 WebKit 内核） | 部分旧系统/轻量发行版自带 | ❌ **不支持** | "Debugging is not supported" |

> ⚠️ **QtWebKit 下 `debug=True` 无效**：pywebview 官方文档明确标注 QtWebKit "Debugging is not supported"。若在 Linux 轻量环境（如仅装 `python3-pyqt5` 未装 `python3-pyqt5.qtwebengine`）下回退到 QtWebKit，DevTools 无法打开，`evaluate_js` 仍可用但无法断点调试。
> **对策**：确保安装 QtWebEngine 组件（`pip install PyQtWebEngine` 或 `PySide6-Addons`），或优先使用 GTK 后端（`gui='gtk'`，WebKit2 原生支持调试）。

---

## 7. 各 OS 打包 + 签名矩阵（速查）

| 维度 | Windows | macOS | Linux |
|------|---------|-------|-------|
| 打包器 | PyInstaller onefile | py2app（或 PyInstaller onefile） | PyInstaller onefile → AppImage |
| 主后端 | WinForms + WebView2 | cocoa | gtk |
| 隐藏导入 | winforms/edgechromium/mshtml/clr | cocoa(+pyobjc) | gtk(+gi) |
| 原生运行时 | webview/lib（自动 hook 收集） | pyobjc（pip） | PyGObject（系统 apt + pip） |
| 控制台 | `console=True`（Web 应用铁律） | 调试 console / 分发 `--windowed` | console |
| 签名 | signtool（可选） | codesign + notarytool（分发必需） | 无强制（可 GPG） |
| 交叉编译 | ❌ 不可 | ❌ 不可 | ❌ 不可 |
| 编码注意 | **GBK 控制台限制（Windows-only）**：UTF-8 中文在控制台乱码但不影响逻辑；日志 `encoding='utf-8'` | UTF-8 正常 | UTF-8 正常 |

---

## 8. 诚实边界声明（实证范围）

- **已实跑证据（本环境 Windows）**：T1 后端矩阵内省、T2 开发态 27 项 ALL_PASS、T3 Windows 打包态 `MultiDemo.exe` 17.9MB + 冒烟 ALL_PASS、T4 模板 `py_compile` + 平台守卫分支。
- **未实跑（诚实不伪造）**：macOS py2app GUI 构建、Linux AppImage 构建——二者**仅能在对应 OS 执行**，本 Windows 环境只做了命令预演与语法/守卫核验。请在这些 OS 上首次构建时实跑验证（建议产出内自带 ALL_PASS 自跑断言，如 demo 模式）。
- **未覆盖**：cefpython3 路径（Python 3.9 专属）、Android 后端——按需单独验证，不在本技能默认交付范围。
