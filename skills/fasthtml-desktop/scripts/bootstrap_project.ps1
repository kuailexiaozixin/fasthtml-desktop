# bootstrap_project.ps1 — 初始化 fasthtml-desktop 项目骨架
# 生成 web-desktop-exe 蓝图
# UTF-8 with BOM + CRLF

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectDir,
    [Parameter(Mandatory=$true)]
    [string]$AppName,
    [string]$BlueprintDir = "",
    [switch]$DevMode,
    [string]$PackageName = ""
)

$ErrorActionPreference = "Stop"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Write-Log {
    param([string]$Message)
    Write-Host "[INFO] $Message"
}

function Write-File {
    param([string]$Path, [string]$Content)
    $parent = Split-Path $Path -Parent
    if (-not (Test-Path $parent)) { New-Item -Path $parent -ItemType Directory -Force | Out-Null }
    [System.IO.File]::WriteAllText($Path, $Content, $Utf8NoBom)
    Write-Log "  创建：$Path"
}

function Read-Template {
    param([string]$Path)
    if (-not (Test-Path $Path)) { throw "缺少模板：$Path" }
    return [System.IO.File]::ReadAllText($Path, $Utf8NoBom)
}

function Expand-Template {
    param([string]$Path, [hashtable]$Values)
    $content = Read-Template $Path
    foreach ($key in $Values.Keys) {
        $content = $content.Replace("{{$key}}", [string]$Values[$key])
    }
    return $content
}

if ($AppName -notmatch '^[A-Za-z0-9][A-Za-z0-9 _.-]*$') {
    throw "AppName 含不安全字符：$AppName"
}
if ($PackageName -and $PackageName -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') {
    throw "PackageName 必须是合法 Python 标识符：$PackageName"
}

$scriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent
if (-not $BlueprintDir) {
    $BlueprintDir = Join-Path $scriptDir "..\templates\project-blueprints\web-desktop-exe"
}
$BlueprintDir = Resolve-Path $BlueprintDir

$AppSlug = ($AppName.ToLower() -replace '[^a-z0-9]+', '-').Trim('-')
if (-not $AppSlug) { $AppSlug = "app" }

$srcDir = Join-Path $ProjectDir "src"
$dataDir = Join-Path $ProjectDir "data"
$testsDir = Join-Path $ProjectDir "tests"
foreach ($dir in @($ProjectDir, $srcDir, $dataDir, $testsDir)) {
    if (-not (Test-Path $dir)) { New-Item -Path $dir -ItemType Directory -Force | Out-Null }
}
Write-File (Join-Path $dataDir ".gitkeep") ""

$blueprintValues = @{
    APP_NAME = $AppName
    PROJECT_NAME = $AppSlug
}

Write-File (Join-Path $ProjectDir "pyproject.toml") (Expand-Template `
    (Join-Path $BlueprintDir "pyproject.patch.toml.tmpl") $blueprintValues)
Write-File (Join-Path $ProjectDir "requirements.txt") (Read-Template `
    (Join-Path $BlueprintDir "requirements.txt.tmpl"))
Write-File (Join-Path $ProjectDir ".env.example") (Expand-Template `
    (Join-Path $BlueprintDir ".env.example.tmpl") $blueprintValues)
Write-File (Join-Path $ProjectDir ".gitignore") (Read-Template `
    (Join-Path $BlueprintDir ".gitignore.tmpl"))

Write-File (Join-Path $srcDir "main.py") (Expand-Template `
    (Join-Path $BlueprintDir "src\main.py.tmpl") $blueprintValues)

$appTargetDir = $srcDir
if ($PackageName) {
    $appTargetDir = Join-Path $srcDir $PackageName
    Write-File (Join-Path $appTargetDir "__init__.py") ""
}
Write-File (Join-Path $appTargetDir "app.py") (Expand-Template `
    (Join-Path $BlueprintDir "src\app.py.tmpl") $blueprintValues)

Write-File (Join-Path $srcDir "__init__.py") ""
Write-File (Join-Path $testsDir "__init__.py") ""

$hooksDir = Join-Path $srcDir "pyinstaller_hooks"
New-Item -Path $hooksDir -ItemType Directory -Force | Out-Null
Write-File (Join-Path $hooksDir "__init__.py") ""
$hookSrc = Join-Path $BlueprintDir "pyinstaller_hooks\hook-genai_prices.py"
if (-not (Test-Path $hookSrc)) { throw "缺少模板：$hookSrc" }
Copy-Item -Path $hookSrc -Destination (Join-Path $hooksDir "hook-genai_prices.py") -Force
Write-Log "  创建：$(Join-Path $hooksDir 'hook-genai_prices.py')"

$launchTmpl = Join-Path $BlueprintDir "启动.bat.tmpl"
if (-not (Test-Path $launchTmpl)) { throw "缺少模板：$launchTmpl" }
$gbk = [System.Text.Encoding]::GetEncoding('GBK')
$content = [System.IO.File]::ReadAllText($launchTmpl, $gbk)
$content = $content.Replace('{{APP_NAME}}', $AppName)
$content = $content -replace "\r?\n", "`r`n"
[System.IO.File]::WriteAllText((Join-Path $ProjectDir "启动.bat"), $content, $gbk)
Write-Log "  创建：$(Join-Path $ProjectDir '启动.bat')"

$engineSrc = Join-Path $scriptDir "..\templates\shared\launcher.py"
if (-not (Test-Path $engineSrc)) { throw "缺少模板：$engineSrc" }
Copy-Item -Path $engineSrc -Destination (Join-Path $ProjectDir "launcher.py") -Force
Write-Log "  创建：$(Join-Path $ProjectDir 'launcher.py')（与 templates/shared/launcher.py 逐字节一致）"

$jsonContent = @"
{
  "app_name": "$AppName",
  "use_venv": true,
  "auto_install": true,
  "pip_index": "https://mirrors.aliyun.com/pypi/simple/"
}
"@
Write-File (Join-Path $ProjectDir "launcher.json") $jsonContent

Write-File (Join-Path $ProjectDir "README.md") (Expand-Template `
    (Join-Path $BlueprintDir "README.md.tmpl") $blueprintValues)

if ($DevMode) {
    Write-File (Join-Path $srcDir "dev_main.py") (Read-Template `
        (Join-Path $BlueprintDir "src\dev_main.py.tmpl"))
}

Write-Log "项目骨架生成完成：$ProjectDir"
Write-Log "下一步：cd $ProjectDir && uv sync"