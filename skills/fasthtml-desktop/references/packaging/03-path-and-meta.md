# 路径适配与元数据处理

> 本文档覆盖 PyInstaller 打包后的路径适配、资源路径处理、
> 元数据依赖包、控制台编码与沙箱环境构建。

---

## 路径适配（sys.frozen 检测）

打包后 `__file__` 指向临时解压目录 `_MEIxxxx`，所有基于 `Path(__file__)` 的路径计算都指向错误的临时目录。

### `--onefile` 与 `--onedir` 的路径差异

| 模式 | `sys.executable` 指向 | `sys._MEIPASS` 指向 | 业务代码位置 |
|------|---------------------|-------------------|------------|
| `--onefile`（单文件） | EXE 所在目录（如 `dist/`） | **临时解压目录**（`%TEMP%\_MEIxxxxx`） | `_MEIPASS/src/` |
| `--onedir`（目录模式） | EXE 所在目录（如 `dist/MyApp/`） | 同 `sys.executable.parent` | `exe同级/src/` |

> **关键**：`--onefile` 模式下，`--add-data` 打包的资源位于 `sys._MEIPASS` 下，**而非** `sys.executable.parent`。

### 标准模板

> **关键区分**：冻结后存在两类基目录，用途不同，**绝不能混用**：
> - **资源基目录 `RESOURCE_DIR`**（只读）：`--add-data` 解包的资源/代码都在 `_MEIPASS` 下（`_MEIPASS` 是 onefile 解压的临时目录，**只读**）。
> - **数据基目录 `DATA_DIR`**（可写）：DB / 日志 / 下载等需要写入的位置，必须用 `sys.executable.parent`（EXE 同级目录）。
>
> 把可写数据放到 `_MEIPASS` 会触发 `sqlite3.OperationalError: unable to open database file`，且关程序即丢失。

```python
if getattr(sys, 'frozen', False):
    # 只读资源基目录（onefile: _MEIPASS 临时目录）
    RESOURCE_DIR = Path(sys._MEIPASS)
    # 可写数据基目录（EXE 同级目录，onefile 下 _MEIPASS 只读，必须写这里）
    DATA_DIR = Path(sys.executable).parent
else:
    RESOURCE_DIR = Path(__file__).parent
    DATA_DIR = Path(__file__).parent

# 可写数据一律用 DATA_DIR
DB_PATH = DATA_DIR / "data" / "app.db"
DOWNLOAD_DIR = DATA_DIR / "downloads"
LOG_DIR = DATA_DIR / "logs"
# 只读资源用 RESOURCE_DIR，例如：RESOURCE_DIR / "src" / "assets" / "logo.png"
```

### dev vs frozen 目录树对照

同一个 `src/` 在「开发态」和「onefile 打包态」下解析出的基目录**完全不同**，路径代码必须按 `sys.frozen` 分支：

**开发态**（直接 `python src/main.py`）：

```text
project/
├── src/
│   ├── main.py            # __file__ 指向这里
│   ├── app.py
│   └── <pkg>/
│       ├── static/        # RESOURCE_DIR = __file__.parent（可读可写）
│       └── data/          # 开发期可写
└── .venv/
```

**onefile 打包态**（双击 `dist/MyApp.exe`）：

```text
dist/
└── MyApp.exe              # sys.executable 指向这里
    ↓ 运行时解包到临时目录 %TEMP%\_MEIxxxx\
    ├── src/               # RESOURCE_DIR = _MEIPASS（只读！）
    │   ├── main.py
    │   └── <pkg>/static/
    └── （python + 依赖）

data/                      # DATA_DIR = sys.executable.parent（可写，EXE 同级）
```

> **口诀：只读找 `_MEIPASS`，要写找 `sys.executable.parent`。** 把 DB / 日志 / downloads 写进
> `_MEIPASS` 会触发 `sqlite3.OperationalError: unable to open database file`，且关闭程序即丢失。

### 跨平台资源路径获取函数

```python
import sys
from pathlib import Path

def get_resource_path(relative_path: str) -> Path:
    """获取静态资源路径，兼容打包前和打包后。"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent
    return base_path / relative_path
```

### 常见故障

| 症状 | 根因 | 修复 |
|------|------|------|
| `sqlite3.OperationalError: unable to open database file` | 在 _MEI 临时目录无写权限 | 改用 `sys.executable.parent` |
| 文件下载后关闭程序丢失 | 下载到了临时目录 | 改用 `sys.executable.parent` |
| 配置文件读取正常但无法保存 | 读写路径不一致 | 统一 `sys.frozen` 检测 |
| `FileNotFoundError: dist\\src`（onefile 模式） | `BASE_DIR` 错用 `sys.executable.parent`（指向 dist），实际在 `_MEIPASS` | 改用 `sys._MEIPASS` |

---

## 路径含空格的处理

Windows 用户名或安装路径含空格时（如 `C:\Users\John Doe\`），PyInstaller 的 `--add-data` 和 `--workpath` 参数在 Git Bash 中可能静默失效。

### 症状

- 打包后 EXE 运行显示 `ModuleNotFoundError: No module named 'app'`
- `dist/_internal/` 目录下缺少业务代码文件（如 `app.py`）
- PyInstaller 输出中无错误，但 --add-data 实际未生效

### 根因

Git Bash 中空格被拆分参数，`--add-data "src;src"` 被解析为两个参数 `src;src` 和路径剩余部分。
PyInstaller 静默跳过无法识别的参数，不报错。

### 方案 A（推荐）：在 CMD 或 PowerShell 中执行打包

```powershell
# PowerShell（推荐）
python -m PyInstaller --onefile --console `
  --name MyApp `
  --add-data "src;src" `
  main.py
```

### 方案 B：用 Python subprocess 调用 PyInstaller

当 Bash 路径空格无法规避时，改用 Python 脚本启动打包：

```python
# scripts/build_exe.py
import subprocess, sys

subprocess.run([
    sys.executable, "-m", "PyInstaller",
    "--onefile", "--console",
    "--name", "MyApp",
    "--add-data", "src;src",
    "main.py"
], check=True)
```

然后运行 `python scripts/build_exe.py`。

### 方案 C：使用 8.3 短路径名

```bash
# 查看短路径名
dir /x "C:\Program Files\My Project"
# 输出：PROGRA~1  MY_PRO~1
# 然后用短路径名替换
```

### 检测脚本

```bash
# 打包前检测路径中是否含空格
if echo "$PWD" | grep -q " "; then
    echo "[WARN] 当前路径含空格，建议在 PowerShell 中打包"
    echo "       PowerShell：python -m PyInstaller ..."
fi
```

---

## 路径含特殊字符

除了空格外，路径中的中文、Unicode 字符、`&`、`(`、`)`、`#`、`%` 等也可能导致 PyInstaller 解析失败。

### 症状

```
Fatal error: Cannot get executable path
```

或打包后 EXE 启动时报错 `Failed to execute script`。

### 根因

PyInstaller 的 bootloader 在解析路径时对某些特殊字符处理不完善，尤其是在 Windows 环境下。

### 推荐做法

1. **项目路径只使用英文、数字、下划线、连字符**
2. 将项目放在简单英文路径下（如 `C:\projects\my-app\`）
3. 输出路径（`--distpath`、`--workpath`）也使用纯英文路径

### 如果无法避免特殊字符

```powershell
# 方案 A：显式指定 workpath 和 distpath 为纯英文路径
python -m PyInstaller --onefile --console ^
  --workpath "C:\temp\pyi_build" ^
  --distpath "C:\temp\pyi_dist" ^
  --specpath "C:\temp\pyi_spec" ^
  main.py
```

```python
# 方案 B：使用 Python 脚本，路径通过变量传递
# scripts/build_exe.py
import subprocess, tempfile
from pathlib import Path

build_dir = Path(tempfile.gettempdir()) / "pyi_build"
dist_dir = Path(tempfile.gettempdir()) / "pyi_dist"

subprocess.run([
    "python", "-m", "PyInstaller",
    "--onefile", "--console",
    "--workpath", str(build_dir),
    "--distpath", str(dist_dir),
    "main.py"
], check=True)
```

---

## 元数据依赖包处理（copy_metadata）

某些包仅含元数据不含模块代码。PyInstaller 不会自动收集它们，但运行时 `importlib.metadata.version()` 会抛 `PackageNotFoundError`。

### 钩子文件示例

```python
# pyinstaller_hooks/hook-genai_prices.py
from PyInstaller.utils.hooks import copy_metadata
datas = copy_metadata("genai_prices")
```

### 判断哪些包需要

```python
import importlib.metadata, pathlib

for dist in importlib.metadata.distributions():
    dist_dir = pathlib.Path(str(dist.locate_file('.')))
    py_files = list(dist_dir.rglob('*.py'))
    if not py_files:
        top = (dist.locate_file('') / 'top_level.txt')
        top_levels = top.read_text().split() if top.exists() else ['(no modules)']
        print(f"[META] {dist.metadata['Name']} -> {', '.join(top_levels)}")
```

输出中 `[META]` 标记的包需要编写对应钩子。

---

## 控制台编码（Windows）

`console=True` 时，Windows 控制台使用 GBK 编码，以下字符会报错：

### 禁止

- Emoji（✅ ❌ 🚀 ⚠️）
- 数学符号（∑ ∞ π）
- 装饰性符号

### 安全替代

| 禁止 | 替代 |
|------|------|
| ✅ / ❌ | `[OK]` / `[FAIL]` |
| ⚠️ | `[!]` 或 `[WARN]` |
| 🚀 | `[INFO]` |
| 📂 | 直接写路径字符串 |

### 高级方案

```python
import sys
sys.stdout.reconfigure(encoding='utf-8')  # 仅 Windows 10 1903+
```

---

## 沙箱环境构建

企业安全沙箱会劫持文件删除操作，导致 PyInstaller 构建中止。

### 解决方案

```python
import tempfile
from pathlib import Path

tmp = Path(tempfile.gettempdir()) / "pyinstaller_build"
tmp.mkdir(exist_ok=True)

PyInstaller.__main__.run([
    "main.py",
    "--onefile", "--console",
    "--workpath", str(tmp / "work"),
    "--distpath", str(tmp / "dist"),
    "--specpath", str(tmp / "spec"),
    "--additional-hooks-dir=pyinstaller_hooks",
])
```

---

## 禁用 UPX

- **严禁启用 UPX 压缩**
- 原因：杀毒软件误报 + 对 Python 应用优化有限
- 在 `.spec` 中设置 `EXE(upx=False)`
