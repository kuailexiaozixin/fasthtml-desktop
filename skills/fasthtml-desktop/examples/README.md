# 示例 / Examples

> **定位**：FastHTML 重型应用范例库——FastOffice 套件 23 个可运行的企业级应用。每个项目都是参考语料，**可借鉴要点**指向真实源码位置，做自己的 FastHTML 应用时可直接抠走对应零件。

> **运行**：双击项目根目录 `启动-<项目>.bat`，浏览器打开 `http://127.0.0.1:<端口>`（端口见总览表）；共享环境 `examples\.venv`（Python 3.13.14）。无启动脚本项目（FastCal / FastLegal / liquidround，PostgreSQL）按各自 README 配置后启动。

## 可借鉴要点（逐项目）

### FastAccounts

> 财务总账：凭证、分录、复式记账与银行对账。

- **复式记账引擎** `ledger.py`：账套→凭证→分录→科目余额，借贷平衡校验——把会计恒等式变成代码的完整范例。
- **银行连接器** `connectors/`（base/providers/stubs）：适配器模式，同一接口下真实银行、模拟银行可切换，对接外部 API 的通用模板。
- **税务模块** `tax.py` 与 **文档导出** `documents.py`：财务域里税费计算、单据导出的落点。
- **双入口** `web_app.py` + `api_app.py`：同一业务同时服务页面与 API，分离部署的参照。

### FastBI

> BI 分析平台：多数据源、看板图表与检索问答。

- **RAG 检索问答** `rag.py` + `web/rag_views.py`：向量检索 + 生成，问答视图与数据看板并列的完整实现。
- **SSE 流式输出** `web/sse.py`：问答结果流式推送到页面的做法。
- **图表渲染层** `web/charts.py`：看板图表统一封装。
- **认证并存** `web/suite_auth.py` / `account_auth.py` / `google_auth.py`：同一应用同时挂多种登录方式的骨架。
- **图数据库可选** `graph_db.py` + `web/graph_ai.py`：图谱能力作为可选增强而非硬依赖的设计。

### FastBot

> AI 机器人：多轮 agent、工具调用与浏览器自动化。

- **agent 循环** `fastbot/agent.py`：消息→工具→再推理的循环，无框架实现 agent 的最小内核。
- **工具注册** `fastbot/tools.py`：工具按名字注册、供模型调用的契约设计。
- **浏览器自动化** `fastbot/computers.py` + `computer_service.py`：把浏览器当工具交给 agent 操作。
- **人机协作** `fastbot/agui.py` + `supervisor_service.py`：agent 请求人工接管（human-in-the-loop）的交接协议。
- **凭据管理** `fastbot/credentials.py`：第三方凭据的存取与校验，不落明文。

### FastCLM

> 合同生命周期管理：起草、审批、签署、归档、提醒。

- **服务化业务域** `fastclm/services/`（22 个服务）：contracts/drafting/review/signatures/approvals/reminders/notifications/retention/audit/backups——超大业务域按职责拆服务的组织范本。
- **合同生命周期** `fastclm/lifecycle.py`：状态流转集中管理，界面与业务函数都是它的投影。
- **存储抽象** `fastclm/storage.py`：本地 / S3 可切换，上传下载与存储后端解耦。
- **提醒引擎** `fastclm/reminders.py` + **审计日志** `services/audit.py`：到期提醒、全量审计的通用实现。
- **安全纵深** `services/malware.py`（附件恶意扫描）+ `services/retention.py`（保留策略）+ `security.py`。
- **SCIM 与 SSO** `services/scim.py` + `auth.py`：企业身份目录对接的参考。

### FastCal

> 团队日历：轮询调度、时区安全、冲突预防。

- **调度算法** `fastcal/domain/slots.py`（时段领域）+ `services/scheduling.py`：候选人忙闲轮询、时区换算与冲突检测的领域建模。
- **日历提供商适配** `fastcal/providers/`（google_calendar/fastmeet/postmark）：外部日历/邮件服务统一适配。
- **数据库迁移** `alembic/`：SQLAlchemy + Alembic 管理表结构演进。
- **预约链接** `fastcal/auth/provision.py`：访客预约的签发与校验。

### FastDPS

> 文档处理服务：上传、转换、分发、审批管道。

- **文档生命周期** `fastdps/domain/lifecycle.py`：文档从创建到归档的状态机。
- **RBAC 权限** `fastdps/rbac/service.py`：角色-权限-资源的权限模型。
- **工作流引擎** `fastdps/services/workflows.py`：审批流步骤编排。
- **开放标准** `fastdps/services/ocds.py`：对接开放合同数据标准（OCDS）的实践。

### FastDocs

> 文档编辑器：文档库、块编辑、模板、版本历史、AI 写作。

- **套件同构骨架** `db.py` + `web/`（views/api/api_core/landing/layout/developer/seo/auth）：FastDocs/FastDrive/FastMail/FastMeet/FastSheets/FastSlides 六件套共用同一工程骨架，新建同型产品直接复制改业务。
- **AI 写作助手** `web/ai.py`：生成、续写、改写功能与页面集成的落点。
- **认证矩阵** `web/account_auth.py` / `google_auth.py` / `suite_auth.py`：账号体系、Google 登录、套件统一登录并存。

### FastDrive

> 文件管理：文件树、分享链接、权限、AI 助手。

- **套件同构骨架**：与 FastDocs 同构（见上），业务换成文件域。
- **分享令牌** `web/views.py`：分享链接的令牌签发与权限校验。
- **AI 助手** `web/ai.py`：文件检索、总结等助手能力。

### FastERP

> ERP：订单到收款、采购到付款、库存、会计引擎。

- **业务域包 + 分层模块化** `FastERP/fasterp/`（sales/purchasing/inventory/accounting/preorders）+ `FastERP/web/` + `FastERP/db.py`：依赖单向自上而下，界面、业务、数据三层分离的完整参照。
- **数据模型 + 状态机前置**：订单（Draft→Confirmed→Delivered→Invoiced→Closed）、发票（Unpaid→Partly Paid→Paid→Overdue）状态流转在 `fasterp/` 各域内定义。
- **会计引擎** `fasterp/accounting.py`：过账、冲销、期间校验、借贷平衡校验。
- **库存 FIFO** `fasterp/inventory.py`：数量与价值双轨消耗。
- **SAP 迁移管道** `FastERP/migration/`（staging→mapping→apply→reconcile→validation→tracking）：老系统数据迁入的结构化全链路，含对账与追溯。
- **双应用** `web_app.py` + `api_app.py`：业务域同时供给页面与 API。

### FastFPA

> 财务规划与分析：预算、滚动预测、现金流、差异归因。

- **预算与预测数据模型** `FastFPA/db.py` + `seed.py`：版本化预算、滚动预测的存储设计。
- **分析视图** `FastFPA/web/views.py`：预算 vs 实际差异、现金流预测的页面呈现。
- **数据集成** `FastFPA/web/integrations.py`：外部财务数据接入的适配层。
- **AI 分析** `FastFPA/web/ai.py`：自然语言问数、差异解读。

### FastHRM

> 人力资源：员工、考勤、薪酬、招聘 ATS、人才平台。

- **大域顶层拆包**：`benefits.py` / `people.py` / `talent.py` / `learning.py` / `recruitment*.py`（6 个招聘模块）——人力资源这一超大业务域按子域拆文件的组织方式。
- **ATS 招聘流程** `web/ats.py` + `web/cv_extract.py`（简历解析）+ `web/ranking.py`（候选人排序）+ `web/recruiting_platform.py`。
- **员工生命周期** `web/lifecycle.py`：入职到离职的状态视图。
- **绩效与福利** `web/performance.py` + `benefits.py`。
- **LLM 抽象** `web/llm.py`：AI 功能统一走这一层，换厂商不动业务。
- **多语言** `web/i18n.py`：界面国际化。

### FastLegal

> 法务 AI：项目、文档审阅、可复用工作流。

- **LLM 厂商抽象** `llm.py`：基于 LangChain 的 OpenAI/Anthropic/Google 多厂商适配，自带 Key 配置——AI 应用的极简抽象样板。
- **可复用审阅组件** `components.py`：表格化审阅、工作流拆成可组装组件。
- **单入口极简** `main.py` + `web/landing.py`：轻量 AI 应用的最小可运行结构。

### FastMail

> 邮件客户端：收发、标签、联系人、AI 摘要。

- **套件同构骨架**：与 FastDocs 同构（见上），业务换成邮件域。
- **邮件域模型** `web/views.py`：文件夹/标签、会话列表、联系人。
- **AI 摘要** `web/ai.py`：邮件摘要与起草。

### FastMeet

> 会议协作：日程、会议室、纪要、AI 议程。

- **套件同构骨架**：与 FastDocs 同构（见上）。
- **媒体模块** `web/media.py`：会议相关音视频素材处理。
- **会议对象模型** `db.py`：会议、日程、纪要与参会人关系。

### FastOffice

> 办公套件门户：应用注册表、统一入口。

- **应用注册表** `products.py`：套件成员应用登记与发现——门户聚合的核心数据模型。
- **适配器衔接** `adapters.py`：各套件登录态、跳转、徽标的统一适配。
- **门户安全** `security.py` + `account_email.py`：统一认证与账号邮件。
- **门户 AI** `ai.py`：跨应用助手入口。

### FastPE

> 私募股权工作台：项目管道、估值、备忘录、数据室。

- **agent 体系** `agents/`（40+ agent）+ `agents/registry.py` + `agents/router.py` + `agents/base.py`：注册表登记、路由器分发、基类统一行为。
- **投资全周期五域** `agents/sourcing/`（寻源）→ `diligence/`（尽调）→ `underwriting/`（承销估值）→ `asset_mgmt/`（资产管理）→ `capital/`（募资）——按业务阶段组织 agent。
- **通用兜底** `agents/generalist.py`：无专属 agent 时降级路由。
- **文档多格式导出** `chat/exports.py`：PDF/XLSX/PPTX 统一定义层（PE/VC 同构）。

### FastSheets

> 电子表格：公式引擎、多工作表、单元格寻址。

- **公式引擎** `engine.py`：前端公式解析、依赖重算——把 Excel 公式引擎做进 FastHTML 的核心文件。
- **工作表模型** `db.py`：工作簿→工作表→单元格的存储设计。
- **套件同构骨架**：同 FastDocs（见上）。

### FastShop

> 电商：商品、购物车、订单、店铺构建器、AI copilot。

- **订单链路** `app/commerce.py` + `checkout_services.py` + `checkout_payments.py`：商品→购物车→结算→支付的状态机。
- **支付与平台适配** `app/integrations/`（stripe_paypal/woocommerce/carrier/fasterp）：支付、物流、外部电商平台、ERP 的集成层。
- **店铺构建器** `app/site_builder_*`：模板 + AI 生成整站。
- **Webhooks** `app/commerce_webhooks.py`：外部事件回调解耦。
- **合规与调度** `app/compliance.py` + `app/scheduler.py`。
- **与 FastERP 集成** `app/integrations/fasterp.py`：电商订单同步进 ERP 的桥接。

### FastSlides

> 演示文稿：幻灯片编辑器、演示模式、AI 生成。

- **套件同构骨架**：同 FastDocs（见上）。
- **幻灯片对象模型** `db.py`：页、元素、主题的序列化。
- **AI 生成** `web/ai.py`：大纲→成片的生成流程。

### FastSurvey

> 问卷：创建、发布、回收、统计分析。

- **极简全栈** `main.py` / `ui.py` / `auth.py` / `ai.py` / `db.py` / `web_app.py`：6 个文件撑起一个完整问卷应用——小应用的体积参照。
- **三阶段** `ui.py`：问卷定义→作答→统计的界面流转。
- **AI 分析** `ai.py`：开放题归类、趋势解读。

### FastVC

> 风投工作台：项目管道、估值、备忘录、数据室。

- **agent 体系**：与 FastPE 同构（registry/router/base），可对比 PE 与 VC 的 agent 划分差异。
- **专属 agent** `agents/diligence/super_analyst.py`、`agents/underwriting/t12_normalizer.py`（T12 归一）。
- **数据室交互** `chat/dataroom.py` + `chat/companies.py`：尽调数据室的多轮问答。
- **导出层** `chat/exports.py`：估值报告、备忘录导出。

### FastWiki

> 知识库：空间、页面、权限、附件、AI 问答。

- **极简知识库** `fastwiki/` 7 文件（api/assistant/db/pdf/security/storage/version/views）：小型知识库的完整参考。
- **PDF 解析** `fastwiki/pdf.py`：附件入库前的解析与分块。
- **存储抽象** `fastwiki/storage.py`：本地/S3 切换。
- **AI 问答** `fastwiki/assistant.py`：基于库内内容的问答。
- **版本追踪** `fastwiki/version.py`。

### liquidround

> AI ECM Agent Squad：多智能体编排、金融数据管道。

- **多 agent 编排** `agents/orchestrator.py` + `agents/router.py` + `agents/registry.py` + `agents/state.py`（共享状态）：32 专业 agent 的调度内核。
- **七域组织** `agents/`（capital/diligence/investor_relations/portfolio/public_markets/sourcing/underwriting）：按金融业务全景组织 agent 群。
- **文档/渲染/研究/评分代理** `document_agent.py` / `render_agent.py`（报告渲染）/ `research_agent.py` / `scoring_agent.py`：横切能力独立成 agent。
- **LLM 工厂** `utils/llm_factory.py`：多厂商按需切换。
- **SSE 流式 + 导出层**：问答流式输出，报告多格式导出。

## 总览

| 项目 | 业务路线 | 入口（端口） | 依赖 / Key |
|------|---------|------------|-----------|
| `FastAccounts/` | 财务总账：凭证、分录、复式记账与银行对账。 | 启动-FastAccounts.bat（5026） | SQLite/PG 双模式（psycopg） |
| `FastBI/` | BI 分析平台：多数据源、看板图表与检索问答。 | 启动-FastBI.bat（5027） | PostgreSQL（pgvector/neo4j）；AI 问答需 LLM Key |
| `FastBot/` | AI 机器人：多轮 agent、工具调用与浏览器自动化。 | 启动-FastBot.bat（5028） | AI 需 LLM Key；浏览器自动化需 playwright |
| `FastCLM/` | 合同生命周期管理：起草、审批、签署、归档、提醒。 | 启动-FastCLM.bat（5029） | PostgreSQL；S3 可选 |
| `FastCal/` | 团队日历：轮询调度、时区安全、冲突预防。 | 无启动脚本，见项目 README | PostgreSQL（SQLAlchemy）；Google 日历集成 |
| `FastDPS/` | 文档处理服务：上传、转换、分发、审批管道。 | 启动-FastDPS.bat（5030） | PostgreSQL |
| `FastDocs/` | 文档编辑器：文档库、块编辑、模板、版本历史、AI 写作。 | 启动-FastDocs.bat（5016） | 离线可用；AI 写作需 LLM Key |
| `FastDrive/` | 文件管理：文件树、分享链接、权限、AI 助手。 | 启动-FastDrive.bat（5012） | 离线可用；AI 助手需 LLM Key |
| `FastERP/` | ERP：订单到收款、采购到付款、库存、会计引擎。 | 启动-FastERP.bat（5011） | 离线可用（SQLite）；PG 可选 |
| `FastFPA/` | 财务规划与分析：预算、滚动预测、现金流、差异归因。 | 启动-FastFPA.bat（5031） | 离线可用 |
| `FastHRM/` | 人力资源：员工、考勤、薪酬、招聘 ATS、人才平台。 | 启动-FastHRM.bat（5032） | AI 功能需 LLM Key |
| `FastLegal/` | 法务 AI：项目、文档审阅、可复用工作流。 | 无启动脚本，见项目 README | AI 审阅需任一 LLM Key；PostgreSQL |
| `FastMail/` | 邮件客户端：收发、标签、联系人、AI 摘要。 | 启动-FastMail.bat（5009） | 收发需邮件账号；AI 摘要需 LLM Key |
| `FastMeet/` | 会议协作：日程、会议室、纪要、AI 议程。 | 启动-FastMeet.bat（5015） | 离线可用；AI 议程需 LLM Key |
| `FastOffice/` | 办公套件门户：应用注册表、统一入口。 | 启动-FastOffice.bat（5020） | 离线可用 |
| `FastPE/` | 私募股权工作台：项目管道、估值、备忘录、数据室。 | 启动-FastPE.bat（5034） | AI 需 LLM Key（BYOK）；PostgreSQL |
| `FastSheets/` | 电子表格：公式引擎、多工作表、单元格寻址。 | 启动-FastSheets.bat（5014） | 离线可用；AI 助手需 LLM Key |
| `FastShop/` | 电商：商品、购物车、订单、店铺构建器、AI copilot。 | 启动-FastShop.bat（5025） | PostgreSQL（无服务回落 SQLite）；AI 需 LLM Key |
| `FastSlides/` | 演示文稿：幻灯片编辑器、演示模式、AI 生成。 | 启动-FastSlides.bat（5013） | 离线可用；AI 生成需 LLM Key |
| `FastSurvey/` | 问卷：创建、发布、回收、统计分析。 | 启动-FastSurvey.bat（5035） | 离线可用 |
| `FastVC/` | 风投工作台：项目管道、估值、备忘录、数据室。 | 启动-FastVC.bat（5036） | AI 需 LLM Key（BYOK）；PostgreSQL |
| `FastWiki/` | 知识库：空间、页面、权限、附件、AI 问答。 | 启动-FastWiki.bat（5022） | AI 问答需 LLM Key |
| `liquidround/` | AI ECM Agent Squad：多智能体编排、金融数据管道。 | 无启动脚本，见项目 README | 需 LLM Key（XAI/OpenAI 至少其一）；PostgreSQL |

## 验证状态（2026-09-29 实测）

- 全量 import **20/20**；FastERP / FastShop / FastBot / FastWiki 真实启动 **HTTP 200**；`启动-FastERP.bat` 完整链路 HTTP 200
- 各项目与 FastOffice 仓库**逐文件一致**（含演示数据与 `.sesskey`）；缺 LLM Key 时页面可开、对应 AI 功能报错（非缺陷）

## 启动器现状与目标

> **当前（过渡态）**：`启动-<项目>.bat` + 共享 `examples\.venv`（浏览器模式）。**目标**：接入 examples 规范启动器（`scripts/gen_launchers.py` 统一分发 launcher.py、launcher.json 管差异）、目录编号化、补 pywebview 桌面壳、PG 项目 SQLite 化。过渡态与目标策略相反，改造完成前勿复制为最终范式。

> 变更历史见技能根 `CHANGELOG.md`。