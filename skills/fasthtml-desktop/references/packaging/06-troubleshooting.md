# 打包故障排除指南

> 本文档覆盖 PyInstaller 打包后的常见问题及其解决方案。

> **⚠️ 铁律：本技能只用 `--onefile` 单文件模式。** 任何 `--onedir` 产物（`dist/_internal/` 与 EXE 捆绑不可分离）、或「复制到 `dist/_internal/`」式修复，均视为**过时指引**，一律改为 `--add-binary` / `--collect-submodules` / 自带 `build_windows_exe` 脚本。参见 [02-build-commands.md](02-build-commands.md) 与 [03-path-and-meta.md](03-path-and-meta.md)。

---

## 打包成功但程序无法运行

### 现象

可执行文件生成成功，但双击运行时闪退或报错。

### 原因与对策

#### 1. 缺失 DLL / 依赖库

**原因**：PyInstaller 未能自动收集某些动态库（如 C++ 运行时），或者 `ctypes.CDLL()` 动态加载的 DLL 未通过 `--add-binary` 显式打包。

**对策**：
- 运行 DLL 诊断脚本（参见 [02-build-commands.md](02-build-commands.md#dll-依赖诊断与修复)）
- 使用 `--add-binary` 显式打包缺失 DLL
- 在虚拟机或纯净环境中测试 EXE

#### 2. 静态资源路径错误

**原因**：程序仍尝试从 `src/` 目录加载资源，打包后路径变化导致找不到文件。

**对策**：
- 使用 `sys._MEIPASS` 进行路径兼容性处理（参见 [03-path-and-meta.md](03-path-and-meta.md#路径适配sysfrozen-检测)）
- 确认 `--add-data` 的参数格式正确（`源路径;目标路径`）

#### 3. 环境差异

**原因**：打包环境（如 Windows 11）与运行环境（如 Windows 7）版本跨度过大，或架构不一致（x86 vs x64）。

**对策**：
- 尽量在与目标运行环境一致或更低版本的系统中进行打包
- 使用 `--target-arch 64bit` 明确指定架构
- 避免使用仅在较新 Windows 版本上可用的 API

#### 4. 导入失败（ImportError）

**原因**：动态导入或某些第三方库的复杂导入逻辑导致 PyInstaller 未能发现依赖。

**对策**：
- 在命令中添加 `--hidden-import <模块名>`
- 使用 `--collect-submodules <包名>` 收集子模块
- 检查是否有条件导入（`try: import X; except: pass`）

---

## 程序运行慢或内存占用高

### 1. 单文件（--onefile）启动延迟

**原因**：`--onefile` 模式每次启动需将整个包解压到临时目录（`%TEMP%\_MEIxxxxx`），
大型应用解压时间可能达到 3-10 秒。

**缓解措施**：

| 方法 | 效果 | 代价 |
|------|------|------|
| 排除不必要的模块 | 减少解压量 | 需要配置 excludes |
| 使用最小 venv 打包 | 减少依赖体积 | 额外环境管理 |
| 压缩资源文件 | 减少解压时间 | 运行时解压额外开销 |
| 显示启动画面 | 用户体验提升 | 需额外编码 |

**启动日志提示**（在 console 中显示）：

```python
# 在 main.py 入口处
import sys
print(f"[INFO] 正在启动 {getattr(sys, 'frozen', False) and '打包模式' or '源码模式'}")
print("[INFO] 解压完成，正在初始化服务...")
```

### 2. 导入了大量不必要的库

**原因**：`excludes` 列表过空，PyInstaller 将许多运行时不用的模块也打包了。

**对策**：
- 在 excludes 中排除 `unittest`、`tkinter`、`pydoc` 等
- 使用最小 venv 打包（参见 [01-core-workflow.md](01-core-workflow.md#体积控制最小虚拟环境策略)）
- **注意**：不要排除 `pip` 和 `wheel`（详见 [04-advanced-config.md](04-advanced-config.md#核心原则不要排除-pip-和-wheel)）

---

## 杀毒软件误报

### 1. 启用 UPX 压缩

**原因**：UPX 压缩后的文件常被杀毒软件标记为可疑（特征码匹配）。

**对策**：
- **严禁启用 UPX**：在命令或 `.spec` 中设置 `upx=False`
- 已在 [03-path-and-meta.md](03-path-and-meta.md#禁用-upx) 中强制规定

### 2. 程序未签名

**原因**：Windows Defender 和 SmartScreen 对未签名的 `.exe` 文件会触发警告。

**对策**：使用 `signtool` 进行数字签名。

### 使用 signtool 进行数字签名

#### 前提条件

- 购买代码签名证书（OV 或 EV 证书）
- 安装 Windows SDK（包含 `signtool.exe`）

#### 签名命令

```bash
# 基本签名
signtool sign /fd SHA256 /a /f "certificate.pfx" /p "password" MyApp.exe

# 时间戳签名（推荐：证书过期后签名仍然有效）
signtool sign /fd SHA256 /tr "http://timestamp.digicert.com" /td SHA256 ^
  /a /f "certificate.pfx" /p "password" MyApp.exe

# 双重签名（SHA1 + SHA256，兼容旧系统）
signtool sign /fd SHA1 /f "certificate.pfx" /p "password" MyApp.exe
signtool sign /as /fd SHA256 /tr "http://timestamp.digicert.com" /td SHA256 ^
  /a /f "certificate.pfx" /p "password" MyApp.exe
```

#### 验证签名

```bash
signtool verify /a /pa MyApp.exe
# 输出: Successfully verified: MyApp.exe
```

#### 在构建脚本中集成

```powershell
# build.ps1（打包 + 签名）
python -m PyInstaller --onefile --console --name MyApp main.py

if ($LASTEXITCODE -eq 0) {
    & "C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe" `
        sign /fd SHA256 /tr "http://timestamp.digicert.com" /td SHA256 `
        /a /f "$env:USERPROFILE\certs\mycert.pfx" /p "$env:CERT_PASSWORD" `
        "dist\MyApp.exe"
    Write-Host "[OK] 签名完成"
}
```

---

## 常见的构建错误

### 错误信息：`Fatal error: Cannot get executable path`

**原因**：路径中包含特殊字符（中文、空格、`&`、`#` 等）或权限不足。

**对策**：
- 将项目移至简单的英文路径（如 `C:\projects\my-app\`）
- 以管理员权限运行构建脚本
- 指定纯英文的 `--workpath` 和 `--distpath`

详细处理参见 [03-path-and-meta.md](03-path-and-meta.md#路径含特殊字符)。

### 错误信息：`AttributeError: module 'xxx' has no attribute 'yyy'`

**原因**：通常是由于 `setuptools` 钩子冲突或包版本不兼容。

**对策**：
- **不要在 excludes 中排除 `pip` 或 `wheel`**
- 升级 / 降级冲突的包
- 使用 `--additional-hooks-dir` 提供自定义钩子

### 错误信息：`Failed to execute script 'main'`

**原因**：通用错误，表示 Python 运行时在 EXE 内部启动时出错。

**诊断步骤**：

```bash
# 1. 带终端运行以查看错误详情
.\dist\MyApp.exe

# 2. 如果闪退，重定向输出
.\dist\MyApp.exe 2>error.log
type error.log

# 3. 临时启用更详细的日志
set PYI_DEBUG=1
.\dist\MyApp.exe
```

### 错误信息：`ModuleNotFoundError: No module named 'xxx'`

**原因**：PyInstaller 的模块分析器未正确扫描到该模块。

**对策**：
- 添加 `--hidden-import xxx` 到打包命令
- 如果是包内子模块，使用 `--collect-submodules xxx`
- 检查模块是否通过 `__import__()` 或 `importlib` 动态导入

---

## 日志排查通用流程

如果打包后的程序无法查看错误信息：

```powershell
# 1. 临时将 console=True（如果是 GUI 程序）
# 2. 在命令行中直接运行 EXE
.\dist\MyApp.exe

# 3. 捕获并保存控制台输出
.\dist\MyApp.exe > output.log 2>&1
type output.log

# 4. 使用进程监视器（Procmon）跟踪文件访问
# 下载：https://learn.microsoft.com/en-us/sysinternals/downloads/procmon
```

### 常见返回码速查

| 退出码 | 含义 | 常见原因 |
|-------|------|---------|
| 0 | 正常退出 | 程序执行完毕 |
| 1 | 一般错误 | ImportError、启动参数错误 |
| -1 | 信号终止 | 被外部进程关闭（如 taskkill） |
| 3221225781 | STATUS_DLL_NOT_FOUND | DLL 缺失 |
| 3221225794 | STATUS_ACCESS_VIOLATION | 内存访问冲突（C 扩展崩溃） |

---

## 在 Agent / 编排环境下运行打包构建

> AI 代跑构建时，若把构建进程挂到「任务计划程序（schtasks）/ 会被回收进程树的调度方式」下，计划程序在任务「完成后」会回收其进程树，**把仍在跑的 PyInstaller 一并杀死**——表现为日志卡在 `Performing binary vs. data reclassification`、任务 `LastTaskResult` 为 `4294770688`（异常终止）、进程数归零但 `dist/` 下未产出 EXE。

**正确做法（前台运行 + 日志轮询）**：

1. **禁止**通过会被回收进程树的调度方式（schtasks 等）运行 `build_windows_exe.ps1` / `build_windows_exe.sh`。
2. **前台**执行构建脚本，输出重定向到日志（`build_windows_exe.ps1` 已内置写入 `build_pyinstaller.log`）：
   ```powershell
   & ".\scripts\build_windows_exe.ps1" 2>&1 | Tee-Object -FilePath build_run.log -Append
   ```
3. **轮询日志** 判断完成，而非依赖外层任务状态：
   - 完成判据 = 日志出现 `Building EXE ... completed successfully` **且** `dist/<ExeName>.exe` 存在；
   - 失败判据 = 日志出现 `PyInstaller failed` / `PermissionError` / `WinError` / `Traceback`。
4. **耗时基线**：实际观测 fasthtml + pywebview + Hermes 精简核心（≈50MB）单次 `--onefile` 构建通常 **2–4 分钟**（与机器性能相关）。既不要假设「必须 < 1 分钟」，也不要误以为需 15+ 分钟——后者往往意味着构建进程被中途杀死，应先排查上述调度问题。
