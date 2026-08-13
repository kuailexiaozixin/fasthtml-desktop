# 构建加固（高级陷阱与实战经验）

> 来源：`python-pyinstaller-build` 技能「高级陷阱与实战经验」章节。经与 `08-packaging.md` + `packaging/01~06` 逐条核对，下列三项为该技能有、fasthtml-desktop **尚未吸收** 的进阶内容，补入此处。
> 适用范围：均为**依赖/环境相关**的进阶坑。日常「最小 venv + fasthtml/webview/uvicorn」栈较少触发，但一旦遇到会导致构建直接失败，故收录为加固知识。
> 诚实边界：条目 1（stdhook 覆盖法）、条目 2（裁剪优于全量收集）为**模式镜像**（来自上游权威技能），需在受限 CI / 含不稳定 stdhook 的第三方包环境下实测；**条目 3（`.spec` 时 CLI flag 非法）已于 2026-07-30 本机 PyInstaller 6.21.0 实跑验证**（`--onefile`/`--windowed`/`--console`/`--hidden-import`/`--collect-submodules`/`--add-data`/`--noupx` 被拒、`--upx` 歧义报错、裸 `.spec` 正常构建），并据此**推翻了上游「`--collect-submodules`/`--hidden-import` 可在 CLI 用」的错误说法**。

---

## 1. 不稳定 stdhook 覆盖法（避开 Windows 隔离子进程崩溃）

某些标准 hook（`_pyinstaller_hooks_contrib` 中的 `hook-markdown.py` 等）会在**隔离子进程**里跑 `collect_submodules(...)`，在 Windows 上**间歇性崩溃**（`SubprocessDiedError: Child process died calling _is_package()`），直接中止整个构建。被影响的包通常不能排除（是真实依赖）。

**解法**：在 `hookspath=['pyinstaller_hooks']` 指向的目录里放**同名** `hook-<pkg>.py` 覆盖 stdhook，改为在**主进程**里 import 该包后直接遍历文件系统收集子模块：

```python
# pyinstaller_hooks/hook-markdown.py
import os, markdown
hiddenimports = ["markdown"]
base = os.path.dirname(markdown.__file__)
for root, _d, files in os.walk(base):
    rel = os.path.relpath(root, base)
    for f in files:
        if not f.endswith(".py"):
            continue
        if f == "__init__.py":
            mod = "markdown" if rel == "." else "markdown." + rel.replace(os.sep, ".")
        else:
            dotted = f[:-3] if rel == "." else rel + os.sep + f[:-3]
            mod = "markdown." + dotted.replace(os.sep, ".")
        hiddenimports.append(mod)
```

此法稳定且产出完整子模块列表，避免隔离子进程崩溃。

---

## 2. 裁剪优于全量收集（体积与速度）

对含大量子模块的大包（如 `*_cli`、`*_agent`），**不要用 `collect_submodules("big_pkg")`**——它会递归强导所有 submodule（含用不到的 provider SDK / TUI），既膨胀体积又可能触发沙箱资源上限被杀死。

**做法**：从入口追踪 + 仅加真正用到的 `hiddenimports` + `excludes` 掉 TUI 与未用 provider。对纯 Python 小包（如 `fasthtml`）则 `collect_submodules` 成本低且安全——本技能构建命令中的 `--collect-submodules fasthtml` 即此理。

| 包类型 | 推荐方式 |
|--------|----------|
| 小、纯 Python（fasthtml） | `--collect-submodules fasthtml`（安全、低成本） |
| 大、含大量可选 provider（*_cli/*_agent） | 手动列 `hiddenimports` + `excludes` 未用部分，**禁止** blanket collect |

---

## 3. 传入 `.spec` 时绝大多数 CLI flag 非法（PyInstaller 6.21.0 实测）

当构建命令传入一个 `.spec` 文件路径时，PyInstaller 把所有「会写进 spec **内容**」的 CLI 参数当作非法并**直接报错**（不是静默忽略）：

    ERROR: option(s) not allowed:
      --onedir/--onefile
    makespec options not valid when a .spec file is given

**本机实测（2026-07-30，PyInstaller 6.21.0）被拒清单**：

| 传入的 CLI flag | 结果 |
|----------------|------|
| `--onefile`(`-F`)/`--onedir`(`-D`) | ❌ 报错 `makespec options not valid` |
| `--windowed`(`-w`)/`--console`(`-c`) | ❌ 报错 |
| `--specpath` | ❌ 报错 |
| `--add-data`/`--add-binary` | ❌ 报错 |
| `--hidden-import`(`--hiddenimport`) | ❌ 报错 |
| `--collect-submodules`/`--collect-data`/`--collect-all` | ❌ 报错 |
| `--noupx`（禁用 UPX 的开关） | ❌ 报错（UPX 属 EXE 内容） |

> ⚠️ **重要纠正（推翻上游「可在 CLI 用」的说法）**：上游 python-pyinstaller-build 原表述「`--collect-submodules` / `--hidden-import` 等**可以**在 CLI 用、只是无需重复」**不成立**——这两个同样是 makespec 选项，传 `.spec` 时一并被拒。所有收集指令必须写进 `.spec` 的 `hiddenimports` / `Analysis(collect_submodules=[...], collect_data=[...])`，不能靠 CLI 补。

**关于 `--upx`**：它**根本不是合法 CLI flag**（会报 `error: ambiguous option: --upx could match --upx-exclude, --upx-dir`）。UPX 开关只能在 `.spec` 内用 `EXE(..., upx=False)` 控制；`--upx-dir` / `--upx-exclude` 是**合法** CLI flag（可与 `.spec` 同用，属进程级）。

**可与 `.spec` 同用的合法 CLI flag**：
- **实测可用**：`--noconfirm`/`-y`（裸 `pyinstaller xxx.spec --noconfirm` 构建成功，`BUILD_EXIT=0`，产出 `dist/hello.exe`）。
- **usage 中属进程级、不参与 spec 生成**（按同一 makespec 规则应被允许）：`--clean`、`--workpath`、`--distpath`、`--log-level`、`--upx-dir`、`--upx-exclude`、`--python-option`。

**正确做法**：用 `.spec` 驱动构建时，命令行只保留 `--clean --noconfirm --workpath <dir> --distpath <dir> <spec文件>`；`onefile` / `console` / `upx` / `hidden-import` / `collect-submodules` 全部在 spec 内设定：

```python
# xxx.spec
a = Analysis([...],
             hiddenimports=['clr', 'webview.platforms.winforms', ...],
             collect_submodules=['fasthtml'],
             collect_data=['certifi'])
exe = EXE(a, name='MyApp', console=True, upx=False)   # 这些都在 spec 内
coll = COLLECT(exe, ...)
```

> fasthtml-desktop 默认走 CLI 直调（`build_exe.py` / `build_gap_exe.py` 模式），不传 `.spec`；本条仅在你切换到 spec 文件驱动构建时适用。裸 `.spec` 构建已实测可正常产出 EXE。
