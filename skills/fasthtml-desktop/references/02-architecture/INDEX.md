# 架构设计（目录）— ②

> 对应工作流 ② 架构设计：定骨架（几层/哪几个业务域/域间依赖方向）+ 定域内细节（每域功能清单/接口契约/数据流）+ 数据模型与状态机前置 + 界面设计活动。

## 模块设计

| 文件 | 内容 |
|------|------|
| `module-design.md` | 功能-模块矩阵 / 模块接口契约（即测试契约，落 pytest 骨架）/ 依赖图 / 数据流图 / 业务域优先命名模板 |

## 架构参考（18 章）

| # | 文件 | 章节 |
|---|------|------|
| 01 | `01-system-context.md` | 系统上下文与边界 |
| 02 | `02-business-flow.md` | 核心业务流 |
| 03 | `03-module-decomposition.md` | 模块分解 |
| 04 | `04-data-architecture.md` | 数据架构 |
| 05 | `05-interface-design.md` | 接口设计 |
| 06 | `06-unified-framework.md` | 统一架构框架 |
| 07 | `07-scenario-driven.md` | 场景驱动的架构类型选择 |
| 08 | `08-adr.md` | 架构决策记录 |
| 09 | `09-common-mistakes.md` | 常见架构错误 |
| 10 | `10-checklist.md` | 设计检查清单 |
| 11 | `11-pattern-selection.md` | 架构模式选型 |
| 12 | `12-state-machine.md` | 状态机设计 |
| 13 | `13-storage-selection.md` | 存储选择表 |
| 14 | `14-tech-debt.md` | 技术债记录 |
| 15 | `15-error-handling.md` | 统一错误处理 |
| 16 | `16-non-functional.md` | 非功能设计 |
| 17 | `17-mvp-boundary.md` | MVP 边界表 |
| 18 | `18-diagram-guide.md` | 图生成指南 |

---

### 使用指引

- **简单项目**：重点阅读 01（系统上下文）、10（检查清单）、17（MVP 边界）
- **中等复杂度**：增加 03（模块分解）、05（接口设计）、07（场景驱动）
- **复杂企业应用**：全部章节均需阅读

详细内容请打开对应章节文件。
