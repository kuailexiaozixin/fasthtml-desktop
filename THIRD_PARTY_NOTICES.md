# Third-Party Notices

本仓库（`fasthtml-desktop`）主仓库代码以 **MIT License** 发布（见根目录 `LICENSE`）。

`examples/` 目录下的参考实现部分**源自第三方开源项目**（克隆或概念移植）。各 example 保留其自身许可证与版权声明；对本仓库 MIT 许可而言，这些构成 **aggregate（聚合分发）**，不改变第三方代码自身许可证。

> ⚠️ **合规提示**：个别 example 的上游项目**未声明许可证**（GitHub 显示 `license: null`）。根据版权法，未声明许可证即默认 **保留所有权利（All Rights Reserved）**，他人无权再分发。此类内容详见下方「⚠️ 无许可证」标记，存在合规风险，请谨慎使用。

---

## `examples/` 中的第三方来源

### 1. Frappe 生态「服务器端 + HTMX 移植版」（本仓库以 MIT 发布，独立重写）

以下 example 在功能与界面上**移植自 Frappe 生态开源项目**，但为**独立重写的纯 Python + HTMX 实现**（未直接使用上游代码），故各 example 自带 **MIT License**。为尊重上游来源，如实标注移植关系如下：

| example | 移植自 | 上游许可证 | 说明 |
|---------|--------|-----------|------|
| `03-FastCRM` | [frappe/crm](https://github.com/frappe/crm) | AGPL-3.0 | 线索、交易管道、联系人、组织、任务、活动流 |
| `04-FastERP` | [frappe/erpnext](https://github.com/frappe/erpnext) | GPL-3.0 | Order-to-Cash、Procure-to-Stock、库存与会计 |
| `05-FastHRM` | [frappe/hrms](https://github.com/frappe/hrms) | AGPL-3.0 | 员工、考勤、请假、工资单 |
| `06-FastInsights` | [frappe/insights](https://github.com/frappe/insights) | AGPL-3.0 | 数据仓库、查询、仪表盘、AI 文本转 SQL |
| `09-FastSheets` | [frappe/sheets](https://github.com/frappe/sheets) | AGPL-3.0 | 电子表格 |
| `10-FastSlides` | [frappe/slides](https://github.com/frappe/slides) | AGPL-3.0 | 幻灯片 |
| `11-FastDrive` | [frappe/drive](https://github.com/frappe/drive) | AGPL-3.0 | 文件/网盘 |
| `14-FastMeet` | [frappe/meet](https://github.com/frappe/meet) | AGPL-3.0 | 日程与会议室 |
| `15-FastMail` | [frappe/mail](https://github.com/frappe/mail) | AGPL-3.0 | 邮件 |
| `16-FastDocs` | [frappe/writer](https://github.com/frappe/writer) | AGPL-3.0 | 文档编辑器 |
| `20-FastHelpdesk` | [frappe/helpdesk](https://github.com/frappe/helpdesk) | AGPL-3.0 | 帮助台工单 |

> 因这些为独立重写实现，各 example 以 **MIT** 授权。若你需直接使用上游 Frappe 代码，请遵循上游 **AGPL-3.0 / GPL-3.0** 许可证。

### 2. 完整克隆 / 改编（⚠️ 含无许可证项目）

| example | 上游来源 | 作者 / 版权 | 上游许可证 | 本地状态 |
|---------|---------|------------|-----------|---------|
| `02-TrafficData` | 基于 Vodafone 数据（重力模型校准） | — | **Apache-2.0** | 自带 LICENSE |
| `12-FastLegal` | — | — | **AGPL-3.0** | 自带 LICENSE |
| `17-FastESM` | FastGov suite | Predictive Labs Ltd | **MIT** | 自带 LICENSE |
| `18-FastMSR` | FastGov suite | Predictive Labs Ltd | **MIT** | 自带 LICENSE |
| `19-open-docflow` | — | — | **MIT** | 自带 LICENSE |
| `13-FastLMS` | 基于 [AnswerDotAI/fasthtml](https://github.com/AnswerDotAI/fasthtml) | — | **MIT** | 自带 LICENSE |
| `01-Bricksmith` | 改编自 upstream Bricksmith（目标 PostgreSQL） | — | 未在本目录保留 | ⚠️ 无本地 LICENSE |
| `07-genui-weather` | [kafkasl/genUI](https://github.com/kafkasl/genUI) | kafkasl | **无许可证** | ⚠️ 无 LICENSE，存在合规风险 |
| `08-code-assistant` | [phact/code-assistant](https://github.com/phact/code-assistant) | phact | **无许可证** | ⚠️ 无 LICENSE，存在合规风险 |

---

## 各项目许可证全文

- `02-TrafficData` → `examples/02-TrafficData/LICENSE`（Apache-2.0）
- `12-FastLegal` → `examples/12-FastLegal/LICENSE`（AGPL-3.0）
- `17/18/13/19` 等 → 各 example 根目录 `LICENSE`

## 使用注意

- **copyleft 项目**（`02-TrafficData` Apache、`12-FastLegal` AGPL）：如需基于其代码二次开发，须遵循对应 copyleft 许可证要求。
- **无许可证项目**（`07-genui-weather`、`08-code-assistant`）：上游默认「保留所有权利」，**不建议再分发或并入商业/开源项目**；如确需使用，请先联系上游作者获取许可，或仅作为个人学习参考。
- **Frappe 移植版**：本仓库的 MIT 版本为独立重写；直接使用上游 Frappe 代码时请遵循其 AGPL/GPL 许可。

如有疑问，欢迎在 Issues 中指出，我们会及时修正标注。
