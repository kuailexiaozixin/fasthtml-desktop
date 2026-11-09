# 编码（目录）— ⑤

> 对应工作流 ⑤ 编码。界面与业务一体实现：按 ② 的分层骨架与接口契约编码，服务端渲染下"界面"即路由函数返回的 HTML 片段（如 `views.order_detail(oid)` 同时是界面与业务出口）。不制作独立纯界面原型文件。

## 必读（前置）

| 文件 | 内容 |
|------|------|
| `fasthtml-refs/fasthtml-llms-ctx-full.txt` | FastHTML 官方 LLMs 上下文，**写任何代码前必读** |
| `execution-and-env.md` | 编码与执行规范：PowerShell 5.1 红线 / 源码编码铁律 / 命令执行与超时 / 修改后验证纪律 |
| `ft-handlers-typing.md` | FastHTML 参数绑定规则 |
| `integration-patterns.md` | fasthtml + pywebview + PyInstaller 协同模式 |

## 必读（按需）

| 文件 | 内容 |
|------|------|
| `project-structure.md` | 分层模块化标准结构（web/ + 业务域包 + db.py） |
| `ui-design.md` | 界面实现：布局模板、CSS 框架选型、交互位置标注、图标处理（②设计活动/⑤实现/⑥完善） |
| `pywebview-shell.md` | pywebview 桌面壳：后端矩阵 / 窗口控制 / JS 桥接 / 对话框 / 菜单 / DOM / 拖拽 / 系统托盘 |
| `fasthtml-fastapi.md` | FastAPI 集成 |
| `fasthtml-refs/picocss-reference.md` | PicoCSS 参考 |
| `fasthtml-refs/fastlite-llms.txt` | 数据库操作时 |
| `fasthtml-refs/genui-hypermedia-reference.md` | GenUI 超媒体 |
| `pywebview-examples/` | 59 个已验证示例脚本（按能力域查阅） |

## 测试驱动

`references/07-quality-gate/Test/01-test-driven-development.md`（Red-Green-Refactor / 测试金字塔 / TestClient / 数据驱动 / Mock / 回归纪律）。每新增业务模块先写失败测试；修 bug 走 Prove-It；禁止「先实现后补测」。
