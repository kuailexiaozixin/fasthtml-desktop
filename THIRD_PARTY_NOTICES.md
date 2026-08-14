# Third-Party Notices

本仓库（`fasthtml-desktop`）主仓库代码以 **MIT License** 发布（见根目录 `LICENSE`）。

`examples/` 目录下的参考实现**均源自第三方 GitHub 项目**（克隆、移植或改编），各自保留原始许可证与版权声明。对本仓库 MIT 许可而言，这些构成 **aggregate（聚合分发）**，不改变第三方代码自身许可证。

> ⚠️ **合规提示**：个别 example 的上游项目**未声明许可证**（GitHub 显示 `license: null`）。根据版权法，未声明许可证即默认 **保留所有权利（All Rights Reserved）**，他人无权再分发。此类内容见下方「⚠️ 无许可证」标记，存在合规风险，请谨慎使用。

---

## 完整来源清单（全部 20 个 example）

### 1. Frappe 生态「服务器端 + HTMX 移植版」（本仓库以 MIT 发布，独立重写）

以下 example 在功能与界面上**移植自 Frappe 生态开源项目**，但为**独立重写的纯 Python + HTMX 实现**（未直接使用上游代码），故各 example 自带 **MIT License**。如实标注移植关系如下：

| example | 移植自 | 上游许可证 | 本地许可证 |
|---------|--------|-----------|-----------|
| `03-FastCRM` | [frappe/crm](https://github.com/frappe/crm) | AGPL-3.0 | MIT |
| `04-FastERP` | [frappe/erpnext](https://github.com/frappe/erpnext) | GPL-3.0 | MIT |
| `05-FastHRM` | [frappe/hrms](https://github.com/frappe/hrms) | AGPL-3.0 | MIT |
| `06-FastInsights` | [frappe/insights](https://github.com/frappe/insights) | AGPL-3.0 | MIT |
| `09-FastSheets` | [frappe/sheets](https://github.com/frappe/sheets) | AGPL-3.0 | MIT |
| `10-FastSlides` | [frappe/slides](https://github.com/frappe/slides) | AGPL-3.0 | MIT |
| `11-FastDrive` | [frappe/drive](https://github.com/frappe/drive) | AGPL-3.0 | MIT |
| `14-FastMeet` | [frappe/meet](https://github.com/frappe/meet) | AGPL-3.0 | MIT |
| `15-FastMail` | [frappe/mail](https://github.com/frappe/mail) | AGPL-3.0 | MIT |
| `16-FastDocs` | [frappe/writer](https://github.com/frappe/writer) | AGPL-3.0 | MIT |
| `20-FastHelpdesk` | [frappe/helpdesk](https://github.com/frappe/helpdesk) | AGPL-3.0 | MIT |

> 因这些为独立重写实现，各 example 以 **MIT** 授权。若需直接使用上游 Frappe 代码，请遵循上游 **AGPL-3.0 / GPL-3.0** 许可证。

### 2. Predictive Labs（Fast\* 家族）原创系列

以下 example 为 **Predictive Labs Ltd** 原创开源项目（MIT），本仓库收载其源码：

| example | 来源 | 许可证 | 本地状态 |
|---------|------|--------|---------|
| `13-FastLMS` | Predictive Labs Fast\* 家族 | **MIT** | 自带 LICENSE（© 2026 Predictive Labs Ltd） |
| `17-FastESM` | Predictive Labs Fast\* 家族 | **MIT** | 自带 LICENSE（© 2026 Predictive Labs Ltd） |
| `18-FastMSR` | Predictive Labs Fast\* 家族 | **MIT** | 自带 LICENSE（© 2026 Predictive Labs Ltd） |
| `19-open-docflow` | [predictivelabsai/open-docflow](https://github.com/predictivelabsai/open-docflow) | **MIT** | 自带 LICENSE |

### 3. 独立项目 / 改编（含无本地许可证项）

| example | 性质 | 上游来源 | 上游许可证 | 本地状态 |
|---------|------|---------|-----------|---------|
| `01-Bricksmith` | 改编自 upstream Bricksmith（CRE AI 交易助手） | — | 未在本目录保留 | ⚠️ 无本地 LICENSE |
| `02-TrafficData` | 独立演示（基于 Vodafone 数据，重力模型校准） | — | **Apache-2.0** | 自带 LICENSE |
| `12-FastLegal` | 原名 **OpenHarvey**，AI 法律文档分析 | — | **AGPL-3.0** | 自带 LICENSE |

### 4. 完整克隆（⚠️ 无许可证）

| example | 上游来源 | 作者 / 版权 | 上游许可证 | 本地状态 |
|---------|---------|------------|-----------|---------|
| `07-genui-weather` | [kafkasl/genUI](https://github.com/kafkasl/genUI) | kafkasl | **无许可证** | ⚠️ 无 LICENSE，存在合规风险 |
| `08-code-assistant` | [phact/code-assistant](https://github.com/phact/code-assistant) | phact | **无许可证** | ⚠️ 无 LICENSE，存在合规风险 |

---

## 各项目许可证全文

- `02-TrafficData` → `examples/02-TrafficData/LICENSE`（Apache-2.0）
- `12-FastLegal` → `examples/12-FastLegal/LICENSE`（AGPL-3.0）
- `13/17/18/19` 等 → 各 example 根目录 `LICENSE`（MIT）

## 使用注意

- **copyleft 项目**（`02-TrafficData` Apache、`12-FastLegal` AGPL）：如需基于其代码二次开发，须遵循对应 copyleft 许可证要求。
- **无许可证项目**（`07-genui-weather`、`08-code-assistant`）：上游默认「保留所有权利」，**不建议再分发或并入商业/开源项目**；如确需使用，请先联系上游作者获取许可，或仅作为个人学习参考。
- **Frappe 移植版**：本仓库的 MIT 版本为独立重写；直接使用上游 Frappe 代码时请遵循其 AGPL/GPL 许可。
- **01-Bricksmith**：改编自 upstream，本地未保留上游 LICENSE，建议联系上游确认许可后使用。

如有疑问，欢迎在 Issues 中指出，我们会及时修正标注。
