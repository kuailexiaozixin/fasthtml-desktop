# Third-Party Notices

本仓库（`fasthtml-desktop`）主仓库代码以 **MIT License** 发布（见根目录 `LICENSE`）。

`examples/` 目录下的参考实现**绝大多数克隆自 Predictive Labs（`predictivelabsai` 组织）**，仅少数源自其他项目。各 example 保留原始版权与许可证声明。对本仓库 MIT 许可而言，这些构成 **aggregate（聚合分发）**，不改变第三方代码自身许可证。

> ⚠️ **合规提示**：个别 example 的上游**未声明许可证**（GitHub 显示 `license: null`）。根据版权法，未声明许可证即默认 **保留所有权利（All Rights Reserved）**，他人无权再分发。此类内容见「⚠️ 无许可证」标记，存在合规风险。

---

## 1. Predictive Labs（`predictivelabsai` 组织）系列 —— 绝大多数

以下 example **克隆自 Predictive Labs Ltd 的 GitHub 组织 `predictivelabsai`**，代码版权归 **Predictive Labs Ltd**。其中多数为 `fasthtml-oss-migrations` 计划（将 **Frappe** 生态应用移植到 FastHTML）的产物——即**功能/概念移植自 Frappe 应用（上游 AGPL/GPL），但代码由 Predictive Labs 编写并持有版权**。

| example | 上游仓库（predictivelabsai） | 许可证 | 版权 |
|---------|------------------------------|--------|------|
| `01-Bricksmith` | [bricksmith](https://github.com/predictivelabsai/bricksmith) | ⚠️ 无许可证 | Predictive Labs Ltd |
| `03-FastCRM` | [FastCRM](https://github.com/predictivelabsai/FastCRM) | MIT | Predictive Labs Ltd |
| `04-FastERP` | [FastERP](https://github.com/predictivelabsai/FastERP)（精简定制版） | MIT | Predictive Labs Ltd |
| `04-FastERP-latest` | [FastERP](https://github.com/predictivelabsai/FastERP)（上游完整版，含 fasterp 业务包 + SAP 迁移模块） | MIT | Predictive Labs Ltd |
| `05-FastHRM` | [FastHRM](https://github.com/predictivelabsai/FastHRM)（精简定制版） | MIT | Predictive Labs Ltd |
| `05-FastHRM-latest` | [FastHRM](https://github.com/predictivelabsai/FastHRM)（上游完整版，含 ATS 招聘/人才模块） | MIT | Predictive Labs Ltd |
| `06-FastInsights` | [FastBI](https://github.com/predictivelabsai/FastBI)（本地为精简桌面版，见下） | MIT | Predictive Labs Ltd |
| `09-FastSheets` | [FastSheets](https://github.com/predictivelabsai/FastSheets) | MIT | Predictive Labs Ltd |
| `10-FastSlides` | [FastSlides](https://github.com/predictivelabsai/FastSlides) | MIT | Predictive Labs Ltd |
| `11-FastDrive` | [FastDrive](https://github.com/predictivelabsai/FastDrive) | MIT | Predictive Labs Ltd |
| `12-FastLegal` | [FastLegal](https://github.com/predictivelabsai/FastLegal) | **AGPL-3.0** | Predictive Labs Ltd |
| `13-FastLMS` | [FastLMS](https://github.com/predictivelabsai/FastLMS) | MIT | Predictive Labs Ltd |
| `14-FastMeet` | [FastMeet](https://github.com/predictivelabsai/FastMeet) | MIT | Predictive Labs Ltd |
| `15-FastMail` | [FastMail](https://github.com/predictivelabsai/FastMail) | MIT | Predictive Labs Ltd |
| `16-FastDocs` | [FastDocs](https://github.com/predictivelabsai/FastDocs) | MIT | Predictive Labs Ltd |
| `17-FastESM` | [FastESM](https://github.com/predictivelabsai/FastESM) | MIT | Predictive Labs Ltd |
| `18-FastMSR` | [FastMSR](https://github.com/predictivelabsai/FastMSR) | MIT | Predictive Labs Ltd |
| `19-open-docflow` | [open-docflow](https://github.com/predictivelabsai/open-docflow) | MIT | Predictive Labs Ltd |
| `20-FastHelpdesk` | [FastHelpdesk](https://github.com/predictivelabsai/FastHelpdesk) | MIT | Predictive Labs Ltd |

> 说明：上述 Fast\* 项目的**功能/概念**移植自 Frappe 生态（Frappe CRM、ERPNext、Frappe HR 等，上游为 AGPL/GPL），但**代码版权归 Predictive Labs Ltd**（以各自仓库许可证授权）。直接使用 Frappe 上游代码时须遵循其 AGPL/GPL 许可。
>
> **06-FastInsights 备注**：本地为 `FastBI` 的**精简桌面版**——移除了上游 Neo4j 图数据库功能（`graph_db.py`、`web/graph_ai.py`、`web/graph_views.py`、`tests/`、`Dockerfile.neo4j`），精简了 `db.py`/`web_app.py`，并新增桌面壳包装（`launcher.py`、`启动.bat`、`main.py`、`start.py`）。与上游 FastBI 非逐字节相同。

## 2. 非 Predictive Labs（少数）

| example | 性质 | 上游来源 | 许可证 | 本地状态 |
|---------|------|---------|--------|---------|
| `02-TrafficData` | 独立演示（Devon 交通分析，基于 Vodafone 数据） | — | **Apache-2.0** | 自带 LICENSE |
| `07-genui-weather` | 完整克隆 | [kafkasl/genUI](https://github.com/kafkasl/genUI) | ⚠️ **无许可证** | 无 LICENSE，合规风险 |
| `08-code-assistant` | 完整克隆 | [phact/code-assistant](https://github.com/phact/code-assistant) | ⚠️ **无许可证** | 无 LICENSE，合规风险 |

---

## 各项目许可证全文

- 各 example 根目录 `LICENSE`（Predictive Labs 系列多为 MIT；`12-FastLegal` 为 AGPL-3.0；`02-TrafficData` 为 Apache-2.0）
- `01-Bricksmith`、`07-genui-weather`、`08-code-assistant`：无本地 LICENSE

## 使用注意

- **Predictive Labs 系列（MIT）**：可自由使用、修改、再分发，需保留版权声明；`12-FastLegal` 为 **AGPL-3.0（copyleft）**，衍生作品须以 AGPL 发布。
- **01-Bricksmith / 07 / 08（无许可证）**：上游默认「保留所有权利」，**不建议再分发或并入商业/开源项目**；如确需使用，请先联系上游作者（Predictive Labs / kafkasl / phact）获取许可。
- **02-TrafficData（Apache-2.0）**：使用须遵循 Apache 2.0 条款。

如有疑问，欢迎在 Issues 中指出，我们会及时修正标注。
