# Check —— 静态关卡（不运行完整应用）

回答「有没有违背规约」。静态解析、快、可重复、零 GUI 依赖，写入/改动后立即执行。

| 文件 | 职责 | 触发时机 |
|------|------|----------|
| `01-static-code-checks.md` | 语法检查、修改后导入测试、Ruff、运行验证、UI 反模式检查 | 每次代码写入后 |
| `02-ui-audit.md` | `ui_audit.py` 13 条禁令、产品 UI 专用检查、AI Slop、通用设计自检、a11y | 每次 UI 代码写入后 |
| `03-route-hygiene.md` | 路由显式化（`check_routes.py`）、前端→后端链路校验（`check_routes_linkage.py`） | 打包前 |

> 逻辑测试（pytest）属 Test 层，见 `../Test/01-test-driven-development.md`；Check 只做静态关卡，不重复 pytest 内容。

回到 [`../INDEX.md`](../INDEX.md) 总入口。
