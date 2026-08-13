# 核心工作流：前置检查 → 打包 → 验证

> 本文档是 fasthtml-desktop 打包的**核心操作流程**。
> 所有桌面 EXE 项目必须按此流程执行，不可跳过任何步骤。

---

## 前置检查：环境审计

在开始打包前，先对当前环境做一次依赖审计，避免打包后因版本/路径问题崩溃：

```bash
# 1. 确认当前在项目虚拟环境
where python | findstr .venv

# 2. 列出项目实际依赖（排除系统包）
pip list --format=columns

# 3. 检查关键 DLL 是否可达（pywebview + pythonnet 场景）
python -c "import ctypes; print(ctypes.CDLL('libffi-8.dll'))"
python -c "import ssl; print(ssl.OPENSSL_VERSION)"
python -c "import clr; print('clr OK')"

# 4. 确认打包工具版本
python -m PyInstaller --version
```

## 依赖审计命令

打包前运行以下命令确认依赖状态：

```bash
# 列出全部已安装包
pip list

# 只列出项目核心依赖（从 requirements.txt 中筛选）
pip list --not-required

# 检查是否存在 torch/scipy 等无关大包
pip list | findstr /i "torch scipy tensorflow pandas numpy pillow matplotlib"
# 如果上述包存在，说明环境不纯，应使用最小 venv 打包
```

---

## 核心工作流（9 步）

打包过程必须按以下顺序执行：

### 步骤 1：环境准备

确认当前在项目 `.venv` 中。如果使用最小 venv（推荐），先创建：

```bash
python -m venv .build-venv
.build-venv\Scripts\pip install python-fasthtml pywebview pythonnet uvicorn
```

### 步骤 2：依赖检查

自动扫描并安装缺失依赖：

```bash
pip check
```

### 步骤 3：更新构建信息

生成 `build_info.json`（参见 [04-advanced-config.md](04-advanced-config.md)）：

```bash
python scripts/generate_build_info.py
```

### 步骤 4：清理环境

移除旧的构建残留：

```bash
rm -rf build/ dist/ *.spec
```

### 步骤 5：生成配置

创建或更新 PyInstaller `.spec` 文件（通常由命令行自动生成）。

### 步骤 6：执行打包

运行 PyInstaller（完整命令详见 [02-build-commands.md](02-build-commands.md)）：

```bash
python -m PyInstaller --onefile --console --name MyApp ...
```

### 步骤 7：验证产物

确认 `.exe` 已生成，数据文件完整：

```bash
ls -lh dist/*.exe
```

### 步骤 8：冒烟测试

启动 EXE 验证 HTTP 200 和窗口句柄（详见 [05-smoke-test.md](05-smoke-test.md)）。

### 步骤 9：最终清理

删除临时文件和缓存：

```bash
rm -rf build/ *.spec __pycache__/
```

---

## 体积控制：最小虚拟环境策略

打包膨胀的根本原因是 PyInstaller 扫描当前环境所有可导入包。如果系统环境装了 torch、scipy，它们会被递归追踪打包。

### 正确做法

```bash
# 1. 创建最小 venv
python -m venv .build-venv

# 2. 仅安装项目实际依赖
.build-venv\Scripts\pip install python-fasthtml pywebview pythonnet uvicorn

# 3. 在该 venv 中打包
.build-venv\Scripts\python -m PyInstaller --clean --noconfirm main.py

# 4. 清理
rmdir /s /q .build-venv
```

### 效果对比

| 方式 | 体积 | 问题 |
|------|------|------|
| 系统环境直接打包 | 154 MB | 包含 torch/PySide6/scipy 等无关包 |
| 最小 venv 打包 | 16 MB | 仅包含实际依赖 |

### 还原构建环境

```bash
# 如果打包后需要调试，记录最小依赖清单
pip freeze > requirements-build.txt
# 之后可以用这个文件重建环境
pip install -r requirements-build.txt
```
