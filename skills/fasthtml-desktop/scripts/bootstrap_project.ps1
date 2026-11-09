# bootstrap_project.ps1 — 初始化 fasthtml-desktop 项目骨架
# 生成 web-desktop-exe 蓝图
# UTF-8 with BOM + CRLF

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectDir,
    [Parameter(Mandatory=$true)]
    [string]$AppName,
    [string]$BlueprintDir = "",  # 默认用 web-desktop-exe 蓝图
    [switch]$DevMode,  # 同时生成 dev_main.py（开发用热重载入口）
    [string]$PackageName = ""  # 嵌套包包名（如 "myapp"），留空表示扁平结构
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    Write-Host "[INFO] $Message"
}

function Write-File {
    param([string]$Path, [string]$Content)
    $parent = Split-Path $Path -Parent
    if (-not (Test-Path $parent)) { New-Item -Path $parent -ItemType Directory -Force | Out-Null }
    Set-Content -Path $Path -Value $Content -Encoding UTF8
    Write-Log "  创建：$Path"
}

# 确定蓝图路径
$scriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
if (-not $BlueprintDir) {
    $BlueprintDir = Join-Path $scriptDir "..\templates\project-blueprints\web-desktop-exe"
}
$BlueprintDir = Resolve-Path $BlueprintDir

# 创建目录结构
$srcDir = Join-Path $ProjectDir "src"
$dataDir = Join-Path $ProjectDir "data"
$testsDir = Join-Path $ProjectDir "tests"

@($ProjectDir, $srcDir, $dataDir, $testsDir) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -Path $_ -ItemType Directory -Force | Out-Null
    }
}

# 创建 .gitkeep
Set-Content -Path (Join-Path $dataDir ".gitkeep") -Value "" -NoNewline

# 创建 pyproject.toml（patch + 共享模板合并逻辑，这里直接生成完整文件）
Write-File (Join-Path $ProjectDir "pyproject.toml") @"
[project]
name = "$AppName"
version = "0.1.0"
description = "$AppName — FastHTML Desktop Application"
requires-python = ">=3.11"
dependencies = [
    "python-fasthtml>=0.6.0",
    "pywebview>=5.0",
    "pythonnet>=3.0",
    "uvicorn>=0.30",
]

[project.scripts]
$($AppName.ToLower()) = "main:start"

[tool.ruff]
line-length = 120
target-version = "py311"
"@

# 创建 .env.example
Write-File (Join-Path $ProjectDir ".env.example") @"
# 应用配置
PORT=5001
"@

# 创建 .gitignore
Write-File (Join-Path $ProjectDir ".gitignore") @"
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
.build-venv/
dist/
build/
*.spec

# IDE
.idea/
.vscode/
*.swp

# OS
Thumbs.db
.DS_Store

# 运行时数据（SQLite 等）
data/*.db
data/*.sqlite

# 日志
logs/
"@

# 创建 requirements.txt（启动.bat 自动 pip 安装的运行依赖）
Write-File (Join-Path $ProjectDir "requirements.txt") @"
python-fasthtml>=0.6.0
pywebview>=5.0
pythonnet>=3.0
uvicorn>=0.30
"@

# 创建 main.py（从蓝图模板生成）
$mainTmpl = Join-Path $BlueprintDir "src\main.py.tmpl"
if (Test-Path $mainTmpl) {
    $content = Get-Content $mainTmpl -Raw
    $content = $content.Replace('{{APP_NAME}}', $AppName)
    Write-File (Join-Path $srcDir "main.py") $content
} else {
    Write-Log "[WARN] 未找到 main.py.tmpl，生成默认入口"
    Write-File (Join-Path $srcDir "main.py") @"
import sys, uvicorn, webview, threading, socket
from pathlib import Path

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

PORT = int(__import__('os').environ.get('PORT', 5001))

def start():
    from app import app
    threading.Thread(target=lambda: uvicorn.run(app, host='127.0.0.1', port=PORT, reload=False), daemon=True).start()
    webview.create_window('$AppName', f'http://127.0.0.1:{PORT}')
    webview.start()

if __name__ == '__main__':
    start()
"@
}

# 创建 app.py（从蓝图模板生成）
# 如果指定了 PackageName，使用嵌套包结构
$appTargetDir = $srcDir
if ($PackageName) {
    $appTargetDir = Join-Path $srcDir $PackageName
    if (-not (Test-Path $appTargetDir)) { New-Item $appTargetDir -ItemType Directory -Force | Out-Null }
    # 创建包声明
    Write-File (Join-Path $appTargetDir "__init__.py") ""
}
$appTmpl = Join-Path $BlueprintDir "src\app.py.tmpl"
if (Test-Path $appTmpl) {
    $content = Get-Content $appTmpl -Raw
    $content = $content.Replace('{{APP_NAME}}', $AppName)
    Write-File (Join-Path $appTargetDir "app.py") $content
} else {
    # 生成默认 app.py
    Write-File (Join-Path $srcDir "app.py") @"
from fasthtml.common import *

app, rt = fast_app(hdrs=(
    Style('''
        * { margin:0; padding:0; box-sizing:border-box; }
        body { font-family:-apple-system,sans-serif; padding:20px; background:#f5f5f5; }
        .container { max-width:800px; margin:auto; }
    '''),
))

@rt
def index():
    return Titled('$AppName',
        Div(H1('欢迎使用 $AppName'), P('在此处编写业务逻辑。'), cls='container')
    )
"@
}

# 创建 src/__init__.py
Write-File (Join-Path $srcDir "__init__.py") ""

# 创建 tests/__init__.py
Write-File (Join-Path $testsDir "__init__.py") ""

# 创建 pyinstaller_hooks
$hooksDir = Join-Path $srcDir "pyinstaller_hooks"
if (-not (Test-Path $hooksDir)) { New-Item $hooksDir -ItemType Directory -Force | Out-Null }
Write-File (Join-Path $hooksDir "__init__.py") ""
Write-File (Join-Path $hooksDir "hook-genai_prices.py") @"
from PyInstaller.utils.hooks import copy_metadata
datas = copy_metadata("genai_prices")
"@

# 创建 启动.bat（一键启动器，用户入口：双击即用）
# 关键：cmd.exe 默认按系统 ANSI 编码（中文 Windows 为 GBK/CP936）读取 .bat，
# 且只认 CRLF 行尾。若保存为 UTF-8 或 LF 行尾，中文/命令会被拆碎。因此：
# 1) 模板与输出都必须是 GBK；2) 输出前必须把行尾规范化为 CRLF。
$launchTmpl = Join-Path $BlueprintDir "启动.bat.tmpl"
if (Test-Path $launchTmpl) {
    $gbk = [System.Text.Encoding]::GetEncoding('GBK')
    $content = [System.IO.File]::ReadAllText($launchTmpl, $gbk)
    $content = $content.Replace('{{APP_NAME}}', $AppName)
    # 规范化为 CRLF（防止模板被 Git/编辑器改成 LF 后 cmd 解析错乱）
    $content = $content -replace "\r?\n", "`r`n"
    $outBat = Join-Path $ProjectDir "启动.bat"
    [System.IO.File]::WriteAllText($outBat, $content, $gbk)
    Write-Log "  创建：$outBat"
} else {
    Write-Log "[WARN] 未找到 启动.bat.tmpl，跳过 启动.bat 生成"
}

# 创建 launcher.py（决策层引擎，逐字节拷贝自 templates/shared/launcher.py）
# 与 20 个 examples 共用同一份引擎；真实项目经 launcher.json 设 use_venv=true（建最小 .venv）。
# 注意：.py 源码必须 UTF-8 无 BOM（见 SKILL.md 编码铁律），故用 Copy-Item 保真拷贝。
$engineSrc = Join-Path $scriptDir "..\templates\shared\launcher.py"
$engineDst = Join-Path $ProjectDir "launcher.py"
if (Test-Path $engineSrc) {
    Copy-Item -Path $engineSrc -Destination $engineDst -Force
    Write-Log "  创建：$engineDst（决策层引擎，与 templates/shared/launcher.py 逐字节一致）"
} else {
    Write-Log "[WARN] 未找到 templates/shared/launcher.py，跳过 launcher.py 生成"
}

# 创建 launcher.json（真实项目启动配置：use_venv=true 建最小 .venv，隔离优先）
# 配置键名与引擎 _DEFAULTS 一致（app_name/use_venv/auto_install/pip_index...）。
$jsonPath = Join-Path $ProjectDir "launcher.json"
$jsonContent = @"
{
  "app_name": "$AppName",
  "use_venv": true,
  "auto_install": true,
  "pip_index": "https://pypi.tuna.tsinghua.edu.cn/simple"
}
"@
Set-Content -Path $jsonPath -Value $jsonContent -Encoding UTF8
Write-Log "  创建：$jsonPath（启动配置：use_venv=true 建最小 .venv）"

# 创建 README.md（双用途：用户使用说明书 + LLM 克隆说明书）
# README 是 Markdown，保持 UTF-8（编辑器/LLM 均按 UTF-8 读），因此显式按 UTF-8 读取模板。
$readmeTmpl = Join-Path $BlueprintDir "README.md.tmpl"
if (Test-Path $readmeTmpl) {
    $content = [System.IO.File]::ReadAllText($readmeTmpl, [System.Text.Encoding]::UTF8)
    $content = $content.Replace('{{APP_NAME}}', $AppName)
    Write-File (Join-Path $ProjectDir "README.md") $content
} else {
    Write-Log "[WARN] 未找到 README.md.tmpl，跳过 README 生成"
}

# 如果启用 DevMode，生成 dev_main.py
if ($DevMode) {
    Write-File (Join-Path $srcDir "dev_main.py") @"
import uvicorn
print('[DEV] 开发模式启动：http://127.0.0.1:5001')
uvicorn.run('app:app', host='127.0.0.1', port=5001, reload=True)
"@
}

Write-Log "项目骨架生成完成：$ProjectDir"
Write-Log "下一步：cd $ProjectDir && uv sync"
