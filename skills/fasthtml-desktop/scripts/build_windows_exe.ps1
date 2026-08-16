# build_windows_exe.ps1 — 构建 fasthtml-desktop 项目的 Windows EXE
# fasthtml-desktop 通用 Windows EXE 构建脚本（PyInstaller 最佳实践）
# UTF-8 with BOM + CRLF

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectDir,           # 项目根目录（含 src/pyproject.toml）
    [string]$AppName,              # EXE 名称
    [string]$EntryPoint = "src/main.py",  # 入口文件
    [string]$BuildVenv,            # 可选：独立打包 venv 的 python.exe（默认用 .venv）
    [string[]]$ExtraHiddenImports = @(),  # 项目特有隐藏导入（如第三方常驻网关模块）
    [string[]]$HealthCheckUrls = @(),     # 关键业务健康端点（如 http://127.0.0.1:8642/health）
    [string[]]$Excludes = @(),           # 额外排除模块（体积优化）
    [string]$HookDir,              # 可选：自定义 hook 目录
    [switch]$NoAutoInstall,        # 跳过自动安装依赖
    [switch]$SkipSmokeTest,        # 跳过冒烟测试
    [switch]$NoCleanup             # 保留临时文件
)

$ErrorActionPreference = "Continue"

function Write-Log {
    param([string]$Level, [string]$Message)
    $timestamp = Get-Date -Format "HH:mm:ss"
    $prefix = switch ($Level) {
        "OK"    { "[OK]" }
        "MISS"  { "[MISS]" }
        "FAIL"  { "[FAIL]" }
        "INFO"  { "[INFO]" }
        "WARN"  { "[WARN]" }
    }
    Write-Host "$timestamp $prefix $Message"
}

# 1. 环境检查
$ProjectDir = Resolve-Path $ProjectDir

# 打包 venv：默认用项目 .venv（须为"最小 venv"，仅含运行时依赖 + PyInstaller）。
# 也可用 -BuildVenv 指定独立 .build-venv（体积优化，见 08-packaging.md）。
# 二者均满足"最小 venv 打包"铁律；脚本默认用 .venv（与 SKILL.md 主铁律一致）。
if ($BuildVenv) {
    $venvPython = $BuildVenv
    Write-Log "INFO" "使用独立打包 venv：$venvPython"
} else {
    $venvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
}
if (-not (Test-Path $venvPython)) {
    Write-Log "FAIL" "未找到 Python 环境：$venvPython"
    Write-Log "INFO" "请先创建虚拟环境：python -m venv .venv（或传入 -BuildVenv <path>）"
    exit 1
}

Write-Log "INFO" "项目目录：$ProjectDir"
Write-Log "INFO" "Python 环境：$venvPython"

# 检测路径是否含空格
if ($ProjectDir -match ' ') {
    Write-Log "WARN" "项目路径含空格！--add-data 在 Git Bash 中可能静默失效"
    Write-Log "INFO" "建议：在 PowerShell 中直接运行 build_windows_exe.ps1"
    Write-Log "INFO" "      或用 Python subprocess 调用 PyInstaller（见 08-packaging.md 路径空格章节）"
}

# 2. 依赖检查
if (-not $NoAutoInstall) {
    $required = @("python-fasthtml", "pywebview", "pythonnet", "uvicorn", "pyinstaller")
    $missing = @()

    foreach ($pkg in $required) {
        $check = & $venvPython -c "import importlib.metadata; importlib.metadata.version('$pkg')" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Log "MISS" "$pkg"
            $missing += $pkg
        } else {
            Write-Log "OK" "$pkg"
        }
    }

    if ($missing.Count -gt 0) {
        Write-Log "INFO" "正在安装缺失依赖：$($missing -join ', ')"
        & $venvPython -m pip install $missing --quiet
        if ($LASTEXITCODE -ne 0) {
            Write-Log "FAIL" "依赖安装失败"
            exit 1
        }
        Write-Log "OK" "依赖安装完成"
    }
} else {
    Write-Log "WARN" "跳过自动安装依赖"
}

# 2.5 读取项目声明文件（零 fork 机制，见 08-packaging.md）
$hiddenImportsFile = Join-Path $ProjectDir "src\pyinstaller_hidden_imports.txt"
if (Test-Path $hiddenImportsFile) {
    Write-Log "INFO" "读取项目隐藏导入清单：$hiddenImportsFile"
    foreach ($line in (Get-Content $hiddenImportsFile)) {
        $line = $line.Trim()
        if ($line -and -not $line.StartsWith("#")) {
            $ExtraHiddenImports += $line
            Write-Log "INFO" "  + hidden-import: $line"
        }
    }
}

$healthFile = Join-Path $ProjectDir "src\health_endpoints.txt"
if (Test-Path $healthFile) {
    Write-Log "INFO" "读取业务健康端点清单：$healthFile"
    foreach ($line in (Get-Content $healthFile)) {
        $line = $line.Trim()
        if ($line -and -not $line.StartsWith("#")) {
            $HealthCheckUrls += $line
            Write-Log "INFO" "  + health endpoint: $line"
        }
    }
}

$excludesFile = Join-Path $ProjectDir "src\pyinstaller_excludes.txt"
if (Test-Path $excludesFile) {
    Write-Log "INFO" "读取排除模块清单：$excludesFile"
    foreach ($line in (Get-Content $excludesFile)) {
        $line = $line.Trim()
        if ($line -and -not $line.StartsWith("#")) {
            $Excludes += $line
            Write-Log "INFO" "  + exclude: $line"
        }
    }
}

# 3. 清理旧构建
# 铁律#9：清理前先终止可能仍持有 dist/ 句柄的残留进程（冒烟测试 Kill() 后
# pywebview 子进程句柄释放可能有竞态，或锁住 dist/<AppName>.exe），否则后续 PyInstaller
# 覆盖该文件时可能抛 PermissionError（WinError 5，理论风险，本项目未复现）。干净失败比带病进打包更安全。
if ($AppName) {
    # 安全性：仅终止「主模块路径位于本项目 dist/ 下」的残留进程（即上一轮构建产物），
    # 不误杀用户从其他位置运行的同名实例（如已安装副本），避免破坏性影响。
    $distRoot = Join-Path $ProjectDir "dist"
    $stale = Get-Process -Name $AppName -ErrorAction SilentlyContinue
    $targets = @()
    foreach ($p in $stale) {
        $exePath = $null
        try { $exePath = $p.MainModule.FileName } catch { $exePath = $null }
        if ($exePath -and $exePath.StartsWith($distRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
            $targets += $p
        }
    }
    if ($targets.Count -gt 0) {
        Write-Log "INFO" "清理前终止 dist/ 下残留进程：$($targets.Id -join ',') （释放 dist 句柄）"
        $targets | ForEach-Object { try { $_.Kill() } catch {} }
        $targets | ForEach-Object { try { $_.WaitForExit(2000) } catch {} }
        Start-Sleep -Seconds 1
    }
}

Write-Log "INFO" "清理旧构建产物..."
function Remove-WithRetry($target) {
    # 最多重试 3 次，间隔 1s，容忍句柄释放竞态；仍失败则显式报错退出。
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            Remove-Item -Path $target -Recurse -Force -ErrorAction Stop
            return $true
        } catch {
            if ($attempt -eq 3) {
                Write-Log "FAIL" "无法删除：$target （句柄可能被占用：$_）"
                Write-Log "INFO" "可能被其他进程占用，请手动关闭后重试"
                exit 1
            }
            Start-Sleep -Seconds 1
        }
    }
    return $true
}
foreach ($d in @("build", "dist")) {
    $path = Join-Path $ProjectDir $d
    if (Test-Path $path) {
        Remove-WithRetry $path
        Write-Log "INFO" "  删除：$path"
    }
}
Get-ChildItem $ProjectDir -Filter "*.spec" | ForEach-Object {
    Remove-WithRetry $_.FullName
    Write-Log "INFO" "  删除：$($_.Name)"
}

# 4. 打包
Write-Log "INFO" "开始打包..."

# 铁律检查：禁止 --onedir 模式
if ($Env:PYINSTALLER_MODE -and $Env:PYINSTALLER_MODE -eq "onedir") {
    Write-Log "FAIL" "禁止使用 --onedir 模式！fasthtml-desktop 技能仅允许 --onefile 单文件模式"
    Write-Log "INFO" "设置环境变量 PYINSTALLER_MODE=onefile 或取消设置后重试"
    exit 1
}

$entryPath = Join-Path $ProjectDir $EntryPoint

$pyinstallerArgs = @(
    "--onefile",  # 强制单文件模式，禁止改为 --onedir
    "--console",
    "--noupx",    # 铁律#8：禁用 UPX，回避杀毒误报
    "--noconfirm", # 防御：dist 已存在（如 -NoCleanup 重跑）时避免 PyInstaller 交互式询问导致挂起
    "--name", $AppName,
    "--collect-submodules", "fasthtml",
    "--hidden-import", "clr",
    "--hidden-import", "webview.platforms.winforms",
    "--hidden-import", "webview.platforms.edgechromium",
    "--paths", "$ProjectDir\src",
    "--add-data", "$ProjectDir\src;src",
    "--distpath", "$ProjectDir\dist",
    "--workpath", "$ProjectDir\build"
)

# 项目特有隐藏导入（函数内懒加载模块，如第三方常驻网关；PyInstaller 静态分析抓不到）
foreach ($hi in $ExtraHiddenImports) {
    $pyinstallerArgs += "--hidden-import"
    $pyinstallerArgs += $hi
}

# 排除模块（体积优化）
foreach ($ex in $Excludes) {
    $pyinstallerArgs += "--exclude-module"
    $pyinstallerArgs += $ex
}

# pywebview 原生运行时（edgechromium 后端依赖的 WebView2 互操作 DLL）
try {
    $webviewLib = & $venvPython -c "import webview, os; print(os.path.join(os.path.dirname(webview.__file__), 'lib'))" 2>&1 | Out-String | ForEach-Object { $_.Trim() }
    if (Test-Path $webviewLib) {
        $pyinstallerArgs += "--add-data"
        $pyinstallerArgs += "$webviewLib;webview/lib"
        Write-Log "INFO" "包含 pywebview 原生运行时：$webviewLib"
    } else {
        Write-Log "WARN" "未找到 pywebview lib 目录（WebView2 后端可能缺 DLL）：$webviewLib"
    }
} catch {
    Write-Log "WARN" "无法确定 pywebview lib 路径：$_"
}

# hook 目录：项目自定义（scripts/hooks）+ 技能默认（src/pyinstaller_hooks）+ 显式指定
$hookDirs = @()
if ($HookDir) { $hookDirs += $HookDir }
foreach ($cand in @((Join-Path $ProjectDir "scripts\hooks"), (Join-Path $ProjectDir "src\pyinstaller_hooks"))) {
    if (Test-Path $cand) { $hookDirs += $cand }
}
foreach ($hd in $hookDirs) {
    $pyinstallerArgs += "--additional-hooks-dir"
    $pyinstallerArgs += $hd
    Write-Log "INFO" "包含 hook 目录：$hd"
}

# 自动添加 pythonnet 依赖的系统 DLL（ctypes.CDLL 动态加载，PyInstaller 不会自动追踪）。
# 注意：不同 Python 发行版的 DLL 位置/命名不一致：
#   - 标准安装：<base>/Library/bin/ffi-8.dll / libcrypto-3-x64.dll / libssl-3-x64.dll
#   - 便携/嵌入式(如 cpython-3.13-windows-x86_64-none)：<base>/DLLs/libffi-8.dll / libcrypto-3-x64.dll / libssl-3-x64.dll
#   pythonnet 3.1/pywebview 6 实际依赖 libffi-8.dll（旧文档写的 ffi-8.dll 已不成立）。
$pythonBase = & $venvPython -c "import sys; print(sys.base_prefix)" 2>&1 | Out-String | ForEach-Object { $_.Trim() }
$dllCandidates = @($pythonBase, (Join-Path $pythonBase "DLLs"), (Join-Path $pythonBase "Library\bin"))
$dlls = @("libffi-8.dll", "ffi-8.dll", "libcrypto-3-x64.dll", "libssl-3-x64.dll")
$addedDlls = @()
foreach ($dll in $dlls) {
    $dllPath = $null
    foreach ($dir in $dllCandidates) {
        $cand = Join-Path $dir $dll
        if (Test-Path $cand) { $dllPath = $cand; break }
    }
    if (-not $dllPath) {
        $hits = Get-ChildItem $pythonBase -Recurse -Filter $dll -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($hits) { $dllPath = $hits.FullName }
    }
    if ($dllPath) {
        if ($dll -notin $addedDlls) {
            $pyinstallerArgs += "--add-binary"
            $pyinstallerArgs += "$dllPath;."
            $addedDlls += $dll
            Write-Log "INFO" "  包含系统 DLL：$dll ($(Split-Path $dllPath -Parent))"
        }
    } else {
        if ($dll -eq "libffi-8.dll") { Write-Log "WARN" "  未找到 $dll（pythonnet 互操作可能依赖，建议排查）" }
    }
}

$pyinstallerArgs += $entryPath

# 关键：PowerShell 5.1 在 $ErrorActionPreference="Stop" 下，原生命令向 stderr 写任何内容（含 PyInstaller 的版本横幅）
# 都会立即抛出 NativeCommandError 并中断进程。因此不能让 stderr 触发异常。
# 做法：临时把错误偏好改为 Continue，并把全部输出（含 stderr）重定向到日志文件后读取。
$tmpLog = Join-Path $ProjectDir "build_pyinstaller.log"
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    & $venvPython -m PyInstaller $pyinstallerArgs *> "$tmpLog"
} finally {
    $ErrorActionPreference = $prevEAP
}
$piExit = $LASTEXITCODE
$result = Get-Content "$tmpLog" -ErrorAction SilentlyContinue
Write-Log "INFO" "PyInstaller 输出（末 10 行）："
if ($result) { $result[-10..-1] | ForEach-Object { Write-Host "  $_" } }

if ($piExit -ne 0) {
    Write-Log "FAIL" "打包失败（PyInstaller 退出码：$piExit）"
    exit 1
}

if ($LASTEXITCODE -ne 0) {
    Write-Log "FAIL" "打包失败（退出码：$LASTEXITCODE）"
    exit 1
}

$exePath = Join-Path $ProjectDir "dist\$AppName.exe"
if (-not (Test-Path $exePath)) {
    Write-Log "FAIL" "未找到打包产物：$exePath"
    exit 1
}

$sizeBytes = (Get-Item $exePath).Length
$sizeMB = [math]::Round($sizeBytes / 1MB, 1)
Write-Log "OK" "打包完成：$exePath ($sizeMB MB)"

# 5. 冒烟测试
if (-not $SkipSmokeTest) {
    Write-Log "INFO" "开始冒烟测试..."

    try {
        # 启动 EXE。使用 -WindowStyle Normal（而非 -NoNewWindow）可避免子进程继承父控制台，
        # 从而 uvicorn 日志不会泄漏到脚本的输出流、触发外层 NativeCommandError。
        $proc = Start-Process -FilePath $exePath -WindowStyle Normal -PassThru

        # 等待 HTTP 200（扫描 5001-5050，兼容端口自增）
        $ready = $false
        $foundPort = $null
        for ($i = 0; $i -lt 25; $i++) {
            Start-Sleep -Seconds 1
            for ($p = 5001; $p -le 5050; $p++) {
                try {
                    $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$p" -TimeoutSec 1 -UseBasicParsing
                    if ($resp.StatusCode -eq 200) {
                        $ready = $true
                        $foundPort = $p
                        break
                    }
                } catch {}
            }
            if ($ready) { break }
        }

        if ($ready) {
            Write-Log "OK" "HTTP 服务就绪 (端口 $foundPort)"
        } else {
            Write-Log "WARN" "HTTP 服务未在 25 秒内就绪"
        }

        # 窗口进程检测
        try {
            $found = $false
            for ($i = 0; $i -lt 10; $i++) {
                $windows = [System.Diagnostics.Process]::GetProcessesByName($AppName)
                if ($windows.Count -gt 0) {
                    $found = $true
                    Write-Log "OK" "窗口进程已创建"
                    break
                }
                Start-Sleep -Seconds 1
            }
            if (-not $found) {
                Write-Log "WARN" "未检测到窗口进程"
            }
        } catch {
            Write-Log "WARN" "窗口进程检测异常：$_"
        }

        # 关键业务健康端点验证（防假绿）：HTTP 200 + 窗口就绪，但后台业务子进程（如第三方常驻网关）可能已崩溃。
        # 任一端点不可达 → 阻断交付（exit 1）。
        $healthAllOk = $true
        if ($HealthCheckUrls.Count -gt 0) {
            Write-Log "INFO" "验证关键业务健康端点（最多 45s/个）..."
            foreach ($url in $HealthCheckUrls) {
                $healthy = $false
                for ($i = 0; $i -lt 45; $i++) {
                    try {
                        $resp = Invoke-WebRequest -Uri $url -TimeoutSec 2 -UseBasicParsing
                        if ($resp.StatusCode -eq 200) { $healthy = $true; break }
                    } catch {}
                    Start-Sleep -Seconds 1
                }
                if ($healthy) {
                    Write-Log "OK" "业务健康端点正常：$url"
                } else {
                    Write-Log "FAIL" "业务健康端点不可达（后台子进程可能已崩溃）：$url"
                    $healthAllOk = $false
                }
            }
        }

        # 尝试关闭
        if (-not $proc.HasExited) {
            $proc.Kill()
            Write-Log "OK" "进程已关闭"
        }

        # 业务健康端点未全部就绪 → 阻断交付（防假绿）
        if (-not $healthAllOk) {
            Write-Log "FAIL" "冒烟测试失败：关键业务端点未就绪，禁止交付（详见 src/health_endpoints.txt）"
            exit 1
        }

    } catch {
        Write-Log "WARN" "冒烟测试异常：$_"
    }
} else {
    Write-Log "WARN" "跳过冒烟测试"
}

# 6. 清理（可选）
if (-not $NoCleanup) {
    Write-Log "INFO" "清理构建临时文件..."
    foreach ($d in @("build")) {
        $path = Join-Path $ProjectDir $d
        if (Test-Path $path) {
            Remove-Item -Path $path -Recurse -Force
        }
    }
    Get-ChildItem $ProjectDir -Filter "*.spec" | ForEach-Object {
        Remove-Item $_.FullName -Force
    }
    Write-Log "OK" "清理完成"
}

Write-Log "OK" "构建完成：$exePath"
