# 质量检查与验证

## 代码检查流程

每次代码写入后按顺序执行：

### 1. 语法检查（语法门禁）

任何 `file(action=write)` 大段代码写入后，必须立即做语法验证：

```bash
python -c "import py_compile; py_compile.compile('src/app.py', doraise=True, encoding='utf-8')"
```

确认无语法错误再进入下一步。

### 1b. 修改后导入测试（防止精确替换导致的断裂引用）

每次使用 `file(action=edit)` 修改代码后，除语法检查外，还需验证模块能否正常导入：

```bash
python -c "import sys; sys.path.insert(0, 'src'); from app import app; print('✅ 模块导入成功')"
```

如果使用嵌套包结构（如 `src/<pkg>/app.py`），改为：

```bash
python -c "import sys; sys.path.insert(0, 'src'); from <pkg>.app import app; print('✅ 模块导入成功')"
```

此步骤可以捕获变量名引用断裂（如移除 `from datetime import date as _today` 但未更新 `_today.today()` 调用）等语法检查发现不了的运行时错误。

### 1.5 测试门禁（pytest，逻辑层，不可跳过）

业务逻辑正确性由 `pytest` 守护——这是工作流 ⑥-β 测试驱动（详见 `09-test-driven-development.md`）的落地门禁，**与本文的 UI/视觉门禁互补、不重叠**。

```bash
uv run pytest          # 单元 + 集成 + 数据驱动全绿；非零退出禁止进入 ⑧ 打包
```

- **覆盖范围**：纯逻辑（validator / organizer / excel 变换 / config 解析）、跨边界路由（用 `starlette.testclient.TestClient`，无需端口/浏览器）、数据驱动参数化。
- **分层边界**：pytest 管「逻辑对不对」；UI/视觉正确性交给 §4 `ui_audit.py` 与测试项五 `ui_window_verify.py`，**pytest 绝不写脆弱的 DOM/渲染单测**。
- **回归纪律**：任何代码改动（新增/修 bug/重构）后必须重跑全量；详见 `09-test-driven-development.md` §9。

### 2. Ruff 代码检查

```bash
ruff check src/
```

修复所有 lint 错误后再继续。

### 3. 运行验证

```bash
uv run myapp
```

确认程序正常启动、页面可访问。

---

### 4. UI 反模式检查（设计质量门禁）

> 适用于 FastHTML 桌面应用的所有 UI 页面。
>
> **执行方式**：纯 Python 审计（无需 Node.js）：`python scripts/ui_audit.py http://127.0.0.1:PORT`；有窗口环境时再叠加 pywebview 原生窗口视觉质检（见 `04-smoke-and-delivery.md` 测试项五）。

每次 UI 代码写入后，按顺序执行以下检查。

#### 4.1 绝对禁令检查（必须通过）

**任何一项命中即需修复后才能进入下一步。**

可通过 `python scripts/ui_audit.py http://127.0.0.1:PORT` 自动检测（推荐），或逐项核对下方表格。

> **禁止跳过门禁**：`ui_audit.py` 是纯 `requests` + `bs4` 的**无头审计**，不依赖 Node.js / Playwright / 浏览器 GUI（项目 venv 已具备依赖）。**任何环境下都没有"环境不支持"的借口跳过它。** 脚本对纯黑白文字、页面不可达等「禁令」级问题返回**非零退出码**，打包前必须运行且通过（exit 0）。
>
> **新增（P0 可访问性审计）**：`ui_audit.py` 现额外做轻量 a11y lint（信息级 SEV_UX，不阻断）：`<img>` 缺 `alt`、`<input>` 缺可访问名（无 `label[for]` / `aria-label` / 包裹 label）、`<label for>` 悬空、`<button>` 缺可访问名、标题层级跳跃（h1→h3）。纯 HTML 解析，不引 axe / Playwright。

```python
