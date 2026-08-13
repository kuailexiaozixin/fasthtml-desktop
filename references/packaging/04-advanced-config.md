# 高级配置：版本信息、图标、构建元数据与排除策略

> 本文档覆盖 Windows 版本信息注入、EXE 图标、构建元数据管理、
> PyInstaller excludes 最佳实践等高级配置。

---

## version_info.txt（Windows 文件属性）

`version_info.txt` 用于在 Windows 文件管理器中显示详细版本信息
（右键 EXE → 属性 → 详细信息）。

### 格式说明

`version_info.txt` 不是 JSON 或 YAML，而是 PyInstaller 专用的 **VSVersionInfo** 格式：

```python
# version_info.txt
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [StringStruct('CompanyName', 'My Company'),
          StringStruct('FileDescription', 'My Application'),
          StringStruct('FileVersion', '1.0.0'),
          StringStruct('InternalName', 'MyApp'),
          StringStruct('LegalCopyright', 'Copyright 2025 My Company'),
          StringStruct('OriginalFilename', 'MyApp.exe'),
          StringStruct('ProductName', 'MyApp'),
          StringStruct('ProductVersion', '1.0.0')])
      ]),
    VarFileInfo([VarStruct('Translation', 1033, 1200)])
  ]
)
```

### 必需字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `CompanyName` | 公司名称 | `My Company` |
| `FileDescription` | 文件描述（用户看到的程序名） | `Financial Analyzer` |
| `FileVersion` | 文件版本号 | `1.0.0` |
| `InternalName` | 内部名称 | `FinancialAnalyzer` |
| `LegalCopyright` | 版权声明 | `Copyright 2025 My Company` |
| `OriginalFilename` | 原始文件名（含 .exe） | `FinancialAnalyzer.exe` |
| `ProductName` | 产品名称 | `Financial Analyzer` |
| `ProductVersion` | 产品版本号 | `1.0.0` |

### 生成工具

使用 PyInstaller 自带的工具生成模板：

```bash
python -m PyInstaller.utils.cli.grab_version > version_info.txt
```

然后用文本编辑器修改字段值。也可以从已有的 EXE 提取：

```bash
# 从一个已知好的 EXE 提取版本信息模板
python -m PyInstaller.utils.cli.grab_version existing_app.exe
```

### 注入方式

```bash
# 命令行方式
python -m PyInstaller --onefile --version-file version_info.txt main.py

# .spec 文件方式
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='MyApp',
    version='version_info.txt',  # 指定路径
    ...
)
```

---

## build_info.json（程序内部构建元数据）

`build_info.json` 应在打包前动态生成，并包含在程序的静态资源中。
应用启动时可读取此文件在关于页面显示构建信息。

### 标准字段结构

```json
{
  "version": "1.0.0",
  "build_datetime": "2025-11-13T10:00:00",
  "build_platform": "Windows-10",
  "python_version": "3.11.0"
}
```

### 自动生成脚本

保存为 `scripts/generate_build_info.py`：

```python
import json
import platform
from datetime import datetime
from pathlib import Path

def generate_build_info(version: str = "1.0.0", output_dir: str = "src/config") -> None:
    """生成 build_info.json，打包前运行。"""
    info = {
        "version": version,
        "build_datetime": datetime.now().isoformat(),
        "build_platform": platform.platform(),
        "python_version": platform.python_version(),
    }

    output_path = Path(output_dir) / "build_info.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)

    print(f"[OK] build_info.json -> {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--output-dir", default="src/config")
    args = parser.parse_args()
    generate_build_info(args.version, args.output_dir)
```

### 集成到 build 脚本

在打包命令前运行：

```bash
python scripts/generate_build_info.py --version 1.0.0 --output-dir src/config

python -m PyInstaller --onefile --console ^
  --add-data "src/config/build_info.json;config" ^
  ...
```

### 在应用中读取

```python
import json
from pathlib import Path

# 使用路径适配模板获取 build_info.json
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

build_info_path = BASE_DIR / "config" / "build_info.json"
if build_info_path.exists():
    with open(build_info_path, encoding="utf-8") as f:
        build_info = json.load(f)
    # build_info["version"], build_info["build_datetime"] 等
```

---

## EXE 图标（--icon）

### 图标文件要求

| 要求 | 说明 |
|------|------|
| 格式 | `.ico` 文件（Windows 图标格式） |
| 推荐尺寸 | 至少包含 256x256 像素（高 DPI 显示） |
| 多尺寸含 | 16x16、32x32、48x48、64x64、256x256 |

### 生成图标

**使用 Python 生成简单图标**（需要 `Pillow`）：

```python
from PIL import Image

def create_icon(png_path: str, ico_path: str):
    img = Image.open(png_path)
    # 生成多分辨率图标
    img.save(ico_path, format='ICO',
             sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])

create_icon("assets/icon.png", "assets/icon.ico")
```

### 注入方式

```bash
python -m PyInstaller --onefile --icon assets/icon.ico main.py
```

### 注意事项

- 如果 `assets/icon.ico` 不存在，PyInstaller 使用默认 Python 图标
- 图标路径中使用正斜杠 `assets/icon.ico`，避免 Windows 反斜杠转义问题
- 打包前确认图标文件存在：`if not os.path.exists("assets/icon.ico"): print("[WARN] 图标文件缺失")`

---

## excludes 配置详解（Analysis 排除策略）

### 核心原则：不要排除 pip 和 wheel

在 `Analysis` 的 `excludes` 列表中：

```python
a = Analysis(
    ['src/main.py'],
    excludes=[
        # ✅ 可以安全排除
        'unittest',
        'tkinter',
        'pydoc',
        'test',
        'distutils',
        'email',
        'http.server',
        'xmlrpc',
        'pdb',
        'inspect',
    ],
    ...
)
```

**`pip` 和 `wheel` 绝对不能排除**，原因：

| 排除的包 | 后果 |
|---------|------|
| `pip` | `setuptools` 钩子冲突，某些包的元数据读取失败 |
| `wheel` | 同上，间接依赖 `setuptools` 的包会报 `PackageNotFoundError` |
| `setuptools` | 大量第三方包（含 pkg_resources）无法工作 |

### 命令行 --exclude-module 写法

```bash
python -m PyInstaller --onefile --console ^
  --exclude-module unittest ^
  --exclude-module tkinter ^
  --exclude-module pydoc ^
  main.py
```

### 可安全排除的模块清单

| 模块 | 大小节省 | 说明 |
|------|---------|------|
| `unittest` | ~1.5 MB | 测试框架，生产环境不需要 |
| `tkinter` | ~3 MB | 不使用 tkinter 的 GUI 项目 |
| `pydoc` | ~0.5 MB | 文档生成，生产不需要 |
| `test` | ~5 MB | Python 标准库测试套件 |
| `distutils` | ~1 MB | 仅构建时需要 |
| `email` | ~1 MB | 如果不涉及邮件处理 |
| `http.server` | ~0.3 MB | 简单 HTTP 服务器 |
| `xmlrpc` | ~0.3 MB | XML-RPC 协议 |
| `pdb` | ~0.2 MB | Python 调试器 |
| `inspect` | ~0.2 MB | 检查存活对象 |

---

## 版本一致性原则

- **`version_info.txt`**（Windows 属性）、**`build_info.json`**（程序内部）与程序的 **`__version__`** 变量应始终保持同步
- 遵循 **SemVer**（语义化版本号）规范：`MAJOR.MINOR.PATCH`
- 每次发布新版本时，同步更新 `CHANGELOG.md`（Keep a Changelog 标准）
