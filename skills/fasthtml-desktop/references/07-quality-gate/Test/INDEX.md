# Test —— 动态验证（运行真实代码路径）

回答「行为符不符合预期」。运行真实代码，构造输入断言输出，编码完成后执行。

| 文件 | 职责 | 触发时机 |
|------|------|----------|
| `01-test-driven-development.md` | TDD 核心：Red-Green-Refactor、测试金字塔、TestClient、数据驱动、Mock、回归纪律 | 编码 ⑥ 步骤（每新增模块先写失败测试） |
| `02-e2e.md` | 端到端测试：业务路径 E2E（真实 EXE + HTTP）+ 视觉 E2E（pywebview 原生窗口） | 关键用户流 |
| `03-smoke-and-delivery.md` | 冒烟门禁（HTTP / EXE 窗口 / HTML 结构 / 视觉质检 / 进程退出 / CI 编排）；打包前检查清单；发布前自检（release_gate） | 打包前 / 发布前 |
| `04-ui-tools.md` | 四个 UI 工具（`ui_audit` / `ui_headless_verify` / `ui_window_verify` / `ui_automate`）分工边界与用法 | 有窗口 / 无 GUI 环境 |

> pytest 管「逻辑对不对」，绝不写脆弱的 DOM 单测；UI / 视觉交给 `ui_window_verify.py`（见 `02-e2e.md`、`04-ui-tools.md`）。

回到 [`../INDEX.md`](../INDEX.md) 总入口。
