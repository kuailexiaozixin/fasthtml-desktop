# 编码与执行规范

> 对应工作流 ⑤ 编码。写任何代码前先读本文件：执行环境红线、源码编码铁律、命令执行与超时。

## PowerShell 5.1 红线

- 所有 `.ps1` 与 `.ps1.tmpl` 默认视在 `Windows PowerShell 5.1` 下执行，禁止使用仅 PowerShell 7+ 支持的参数
- 只要创建、修改、复制、分发 `.ps1` 或 `.ps1.tmpl`，一律使用 `UTF-8 with BOM + CRLF`
- 严禁使用 `UTF-8 without BOM` 保存 PowerShell 文件

## AI 生成源码的编码铁律（防止中文源码乱码）

- **`.py` / 纯 Python 源码**：一律 UTF-8 无 BOM（PEP 3120）。禁止用 PowerShell `Set-Content` 写入任何 `.py` 文件——`Set-Content` 在 Windows PowerShell 5.1 下默认编码非 UTF-8，会把中文写成乱码（实战中曾导致测试文件列名损坏、整批测试失败）。
- **写入 .py 的正确方式**：① 用支持显式 UTF-8 的工具整体写入；② `Out-File -Encoding utf8`（PowerShell 5.1 的 utf8 不带 BOM，符合 PEP）；③ `python -c "open(f,'rb').read(3)"` 核对头部无 BOM 标记。
- **`.ps1`**：维持 UTF-8 with BOM + CRLF（见上）。两者不可混淆：BOM 对 .ps1 必需，对 .py 必须无 BOM。
- **核对方法**：写入后用 `python -c "open(f,'rb').read(3)"` 确认 .py 头部无 EF BB BF、.ps1 头部有。

## 命令执行与超时

- `run_command` 默认超时 120s。
- **禁止单条 shell 命令批量造文件**：源码/配置/资源文件**逐文件 Write/Edit**，严禁 `cat <<'EOF' > file` 连写多文件。
- **可能 >120s 的操作必须显式传 `timeout=600` 或后台运行**：构建（PyInstaller `--onefile` 常 >120s）尤其如此。
- **失败即拆步**：超时则拆成更小步骤，每步独立可验证。

## 每次修改后的验证纪律

- **每次 `file(action=edit)` 修改代码后，必须执行验证**：`py_compile.compile()` 语法检查 + `python -c "from app import app"` 导入测试。这是防止精确替换导致断裂引用的最后防线。
