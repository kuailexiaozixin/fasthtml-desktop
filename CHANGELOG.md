# 变更记录

## 1.12.0 (2026-09-17)

### 重构
- **「架构约束（选型前必读）」并入 ② 架构设计**：删除 SKILL.md 独立章节，内容内联为「铁律（架构选型：服务端渲染约束，选型前必读）」，置于 ② 架构分层铁律之前——FastHTML 服务端渲染本质（磁盘无静态 HTML 入口）、禁用依赖静态 HTML 入口的工具（注入式质检 / /live 热重载 / SSR 预渲染）、正确路径是真实渲染引擎驱动（ui_window_verify / ui_automate / ui_audit）。至此 SKILL.md 全部规则并入工作流①→⑨，无任何独立规则章节。

### 修改
- **SKILL.md frontmatter 补 `license: MIT`**：对齐 Agent Skills 开放规范（agentskills.io）与 `gh skill publish` 校验项（license 为推荐字段），version 升至 1.12.0。
- **README 安装章节新增 `gh skill install` 方式**：本仓库为 root-level 单技能仓库（`*/SKILL.md`），符合 `gh skill` 发现约定（`skills/*/SKILL.md`、`skills/{scope}/*/SKILL.md`、`*/SKILL.md`、`plugins/{scope}/skills/*/SKILL.md`），支持 `gh skill install / list / preview / update --pin`。

### 验证
- gh skill 发布合规逐项核验通过：name `fasthtml-desktop` 符合 kebab-case 命名规则且与目录名（仓库名）匹配；description 存在；license 已补；无 allowed-tools 数组问题；无 metadata.github-* 安装元数据残留；SKILL.md 261 行 < 500 行建议上限。
## 1.11.0 (2026-09-17)

### 重构
- **SKILL.md 铁律融入工作流**：删除独立章节「必须遵守的铁律（最高优先级）」「命令代执行规则」「代码与结构原则（架构分层铁律 / TDD 铁律）」，全部内容内联到对应工作流步骤——② 架构设计（架构分层/模块化业务域优先/数据模型状态机前置/接口契约落 pytest）、③ 环境准备（环境先行/venv/依赖管理分级/命令代执行/命令超时）、④ 项目初始化（bootstrap 铁律/一键启动器全规则）、⑤ 编码（编码铁律/TDD 红绿重构/修改后验证纪律）、⑥ 界面完善（机器视觉质检门禁）、⑦ 质量门禁（pytest 非零阻断/冒烟健康端点）、⑧ 打包（onefile/hidden-import/DRY-RUN/服务启动时序）。SKILL.md 成为纯工作流驱动文档：读到哪步执行哪步规则，无分散章节。
- **references 按工作流①→⑨编号重组**：
  - ① `01-need-discovery.md`（不变）
  - ② `02-architecture/`（原 architecture/ 18 章 + module-design.md）
  - ③ `03-environment.md`（新建：从原 04-agent-execution-and-env.md 拆出环境部分）
  - ④ `04-project-init.md`（原 launch-standard-deliverable.md + 项目初始化流程）
  - ⑤ `05-coding/`（project-structure / ui-design / pywebview-shell / integration-patterns / ft-handlers-typing / fasthtml-fastapi / execution-and-env / fasthtml-refs / pywebview-examples）
  - ⑥ `06-ui-polish.md`（新建：界面完善流程 + 机器视觉质检分工）
  - ⑦ `07-quality-gate/`（原 09-Check&Test&Debug/）
  - ⑧ `08-packaging/`（deep-dive + cross-platform + 原 packaging/ 7 章）
  - ⑨ `09-delivery.md`（新建：交付清单要点 + 双用途 README）

### 修改
- 全部文件引用路径更新为重组后路径（references 内部、SKILL.md、docs/troubleshooting.md、scripts/build_cross_platform.py、README.md、contributing.md、templates/shared/launcher.py、examples/*/launcher.py、pywebview-examples 注释）。
- `02-architecture/INDEX.md` 新增模块设计导航；`08-packaging/INDEX.md` 新增 deep-dive/cross-platform 总览。

### 清理
- 删除 `references/04-agent-execution-and-env.md`（拆分为 03-environment.md 与 05-coding/execution-and-env.md）。
- 删除空的 `references/packaging/` 目录（文件已并入 08-packaging/）。
## 1.10.0 (2026-09-17)

### 重构
- **SKILL.md 工作流重构**：② 架构设计合并原 ②-α 功能模块设计（删除 ②-α 独立步骤），任务扩展为「定骨架（几层/哪几个业务域/域间依赖方向）+ 定域内细节（每域功能清单/接口契约/数据流）+ 数据模型与状态机前置 + 界面设计活动（信息架构/布局决策/设计系统选型）」，产出物首位为表结构清单 + 状态机定义，接口契约直接落 pytest 骨架文件（契约/测试/实现同步演进）。
- **步骤⑤⑥ 语义与顺序调整**：原 ⑤ 界面设计（纯界面原型）→ 新 ⑤ 编码（界面与业务一体，按 ② 分层骨架与页面结构清单编码，不制作独立原型文件）；原 ⑥ 编码 → 新 ⑥ 界面完善与视觉质检（逐页打磨观感 + ui_window_verify / ui_automate / ui_audit 机器质检）。
- **不制作原型**：删除「先原型后业务」两段式工作流——服务端渲染下界面即路由函数返回的 HTML 片段，设计活动并入 ②，界面与业务同步演进（参照 examples/04-FastERP/）。

### 修改
- `references/05-project-structure.md`：标准项目结构改为**分层模块化**（`web/` 表示层 + `services/` 业务域包 + `db.py` 数据层），不再提及扁平包；模块划分改为**业务域优先**（sales/purchasing/inventory/accounting 第一维度，auth/config/errors 技术横切第二维度）。
- `references/02-module-design.md`：定位改为「② 架构设计阶段内使用」；新增**业务域优先命名模板**（业务域视角示例表，与技术视角示例并存）。
- `references/03-ui-design.md`：整体重写——由「原型驱动」改为「界面设计」方法论：设计活动（信息架构/布局决策/设计系统选型）在 ② 完成；界面实现与完善（⑤/⑥）；保留 frontend-design 五步方法论、图标处理、布局模板、反模式校准全部内容；新增设计系统收敛到 `layout.py`（参照 FastERP `web/layout.py`）。
- `SKILL.md` 架构分层铁律：模块化表述升级为**业务域优先**，显式引用 `examples/04-FastERP/fasterp/`。

### 清理
- 删除 `templates/prototype-app.py.tmpl`（UI 原型模板，工作流不再制作原型；无脚本引用）。

## 1.9.1 (2026-09-17)

### 清理
- 清除文档中的历史演进残留（技能修改/文档变动/文件迁移类表述）：
eferences/07-integration-patterns.md 删除「原四个技能」指代；
eferences/launch-standard-deliverable.md 删除「旧 sync_launchers.py 已废弃」「旧版 启动.bat」历史叙事；
eferences/fasthtml-refs/genui-hypermedia-reference.md 的「现状（2026-08 修正）/早期方案/本技能后期」改为现状描述；
eferences/09-Check&Test&Debug/Check/02-ui-audit.md 的「旧版漏检」改为中性能力表述。历史变更统一只在本文件记录。
- 删除根目录历史快照 SKILL.md.bak.20260901-152817（对应 1.9.0 重构，已在本文件记录）。

### 修改
- 
eferences/launch-standard-deliverable.md 章节与条目统一编号：顶层章节改为「一、场景分叉铁律 / 二、通用规则 / 三、启动器 A / 四、启动器 B / 五、方法论小结」，通用规则 9 条、启动器 A 4 条条目顺序编号。

## 1.9.0 (2026-09-01)

### 重构
- **SKILL.md「完整工作流」与「分步执行详解」合并为单一连续章节**：解决 LLM 读完工作流清单后略过详解的问题。每步（①→⑨）统一正文段落呈现，内联必读参考/复用要点/产出物/验收标准，须读完整步再执行，不得跳过任一字段。

## 1.8.0 (2026-08-31)

### 新增
- **代码与结构原则新增「TDD 铁律（测试驱动开发，必须）」章节**：红-绿-重构循环、核心原则（测试先行/小步快跑/测试即文档/回归保障）、好处，并与工作流衔接（test-first、Prove-It、pytest 只管逻辑、全量 pytest+HTML 审计非零即阻断）。

### 重构
- **SKILL.md「工作流融合」重构**：删除独立路由章节与产出物清单表，五目录参考文件及产出物/验收标准全部内联到工作流 ①→⑨ 步骤（新增「分步执行详解」小节），以工作流为唯一可靠主线。

## 1.7.0 (2026-08-30)

### 新增
- **架构分层铁律（表示层-业务层-数据层）**：SKILL.md 新增"代码与结构原则 > 架构分层"章节，明确三层分层、依赖单向自上而下、禁止跨层调用；强调模块化、关注点分离、高内聚低耦合。
- `references/05-project-structure.md` 新增"架构分层与模块化"章节：三层职责、模块化拆包、数据访问收敛 Repository 模式。
- 强化 `references/architecture/INDEX.md` 与各架构章节，统一架构分层表达。

### 清理
- 移除 `references/fasthtml-refs/` 下无许可证声明的第三方 llms 上下文文件（`faststrap-llms.txt`、`monsterui-llms-ctx.txt`），保持合规。

## 1.6.0 (2026-08-24)

### 新增
- `references/03-ui-design.md` **完整内联 frontend-design 设计方法论**（fasthtml 上游捆绑方法论，Apache 2.0 授权）：锚定主题、设计原则（Hero 是论点 / 排版承载个性 / 结构即信息 / 刻意动效 / 复杂度匹配愿景 / 慎重文案）、两遍流程（token 系统 → 评审 → build）、克制与自我批评、文案写作五步，产出直接映射 FastHTML `Style()` 与组件，技术栈无关。
### 修改
- `SKILL.md` 路由表：移除独立 frontend-design 引用，审美方法论并入 `references/03-ui-design.md`（自包含章节）。
- 同步本地定制：`references/07-integration-patterns.md`、`references/fasthtml-refs/genui-hypermedia-reference.md` 修订版。
### 清理
- 移除 `references/fasthtml-refs/` 下无许可证声明的第三方 llms 上下文文件（`faststrap-llms.txt`、`monsterui-llms-ctx.txt`），保持合规。

## 1.5.1 (2026-08-16)

### 修复
- 新增 `.gitattributes` 强制 `.bat` 以 CRLF 分发（`*.bat -text`），修复 release 源码 zip 下载后 `.bat` 因 LF 行尾无法在 Windows cmd 运行的问题。

## 1.5.0 (2026-08-16)

### 重构
- 重组为 `skills/fasthtml-desktop/` 结构以符合 `gh skill publish` 规范（root 结构 → skills/ 嵌套，技能自包含）。
### 新增
- CI workflow：`gh skill publish --dry-run` + 目录结构检查（`.github/workflows/ci.yml`）。

## 1.4.0 (2026-08-13)

### 新增
- 打包为可分发 dsh 插件 `dsh-fasthtml-desktop` 并发布 npm，在 DeepSeek Harness 中一键安装：`dsh plugin --profile web add dsh-fasthtml-desktop`
- npm 包根 = 技能仓库根，SKILL.md 及 references/examples 等资源全部随包自包含，不依赖发布者机器
- 形态：Cordis Bundle（Host 侧）；skill 插件（嵌入式提供方，参照官方 `dsh-skill-badge`）
### 文档
- README 安装章节补充 dsh 插件一键安装方式、GitHub Release 源码归档下载安装说明
### 合规
- 移除第三方上游未声明许可证的合规风险警告说明

## 1.3.0

### 说明
- 未单独发布：版本号策略变更，1.4.0 起与 dsh 插件版本号对齐（跳过 1.3.0），技能内容迭代并入 1.4.0。

## 1.2.0 (2026-07-19)
### 同日深度复核补（二次校验，万无一失）
- `scripts/check_routes_linkage.py` **修复路由发现盲区**：原实现只识别 `@rt/@ar/@app.route/@router.route`，漏掉 fasthtml 常规写法 `router = APIRouter()` 后 `@router("/path")` —— 此类项目会被误判"未检测到任何后端路由"并错误 exit 2 / 误报 404。改为先扫描 `APIRouter(...)` 赋值建立`变量名→prefix`映射，再对 `@<变量名>`（含 `.route`）装饰器套用对应 prefix。已用三类合成用例验证：prefix 路由匹配(0) / 无 prefix 路由匹配(0) / 真实 404(1)，真实项目回归 0。
- `scripts/check_refs.sh` **修复退出码异常**：原脚本在 `while read` 管道 subshell 中累加 `ERR` 导致计数丢失且偶发退出码 `-1`。改为临时文件累加器，现稳定退出 0/1（0=全部通过，1=死链/模板不一致），已用真实技能树验证通过。
- `references/12-fixture-alignment.md` **修正事实错误**：原"Organization 真实字段 unit_code/is_rd"描述不实（真实列为 id/level/name/parent_id）。改为如实列举臆造字段（code/is_rd_unit/district 等）与真实列对照，避免误导。

### 修订（同日补）
- `scripts/release_gate.py` 修复 **路径解析依赖 cwd** 的缺陷：原实现把 `--src` 直接传给 pytest 和 linkage 扫描，当从非项目目录调用或 `--src` 相对路径时，会误判为「无 .py 文件 / 无测试」而错误阻断或错误放行。改为引入 `--root`（所有相对路径基准，默认 cwd），`--src`/`--tests` 均相对 `--root` 解析；pytest 目标与路由扫描目标彻底分离。已用真实项目（workspace cwd + 绝对 --root）、合成 404 故障、空 src 三种场景验证：正确项目 exit 0、故障项目 exit 1、空 src 优雅拒绝。


fasthtml-desktop 质量门禁与防回归加固（实战复盘：夹具对齐与统一发布门禁）

### 新增（门禁 / 防回归）
- `scripts/release_gate.py` — 统一发布门禁编排器：把 pytest / check_routes / check_routes_linkage /（可选 UI 视觉质检 `ui_window_verify.py`）/ verify_imports / check_refs 串成一条流水线，**全绿才放行**（required 步骤非零即整体非零，CI 可直接用）。UI 质检为 pywebview 原生窗口（零额外浏览器、零浏览器授权），不卡强拦。
- `scripts/fixture_schema_helper.py` — 测试夹具与 db schema 对齐助手（根治「fixture rot」：insert 字典引用不存在的列导致整批测试静默失败）；自带自测，兼容 fastlite/dbc4/dataclass/pydantic。
- `references/12-fixture-alignment.md` — 夹具对齐强制规则与落地指南。

### 修改（红线补全）
- `references/04-agent-execution-and-env.md` — 新增「AI 生成源码编码铁律」：`.py` 一律 UTF-8 无 BOM，禁止用 PowerShell `Set-Content` 写源码（实战中曾因编码损坏致整批测试失败）。

### 关联（本轮先于本条目落地的技能脚本改进）
- `scripts/check_routes_linkage.py`（前端→后端链路 404 死链校验，与 check_routes.py 互补）
- `scripts/build_windows_exe.ps1` 构建铁律 #9：清理前先 kill 残留进程 + Remove-WithRetry，防 dist 句柄锁（WinError 5）
- 路由卫生 §4.5 / a11y §4.4.1 / 统一门禁合约（P6）已写入 quality-check 拆分后的子文件


## 1.1.0 (2026-07-17)

fasthtml-desktop 技能全量审计与改进（第二轮）。

### 清理
- 移除 `SKILL_IMPROVEMENT_REPORT.md`（108KB 审计工作文档，改进已全部落地）

### 新增（第二轮审计补全 — 2026-07-17）
- `templates/project-blueprints/web-desktop-exe/src/dev_main.py.tmpl` — 开发模式入口（热重载+浏览器预览）
- `references/05-project-structure.md` 增加嵌套包方案 B + 约束例外 + 验证方法
- `references/06-pywebview-shell.md` 增加使用场景速查表 + 常用组合 + v5/v6 版本差异

### 新增
- `docs/delivery-checklist.md` — 标准化交付清单模板（R-12）
- `references/02-module-design.md` — 功能模块设计模板（R-17）
- `examples/05-announcement-downloader/` — API 查询型桌面工具示例（嵌套包结构）
- `examples/06-financial-analyzer/` — 综合型桌面工具示例：网络采集+Excel处理+文件整理+系统监控，融合四种模式
- `templates/prototype-app.py.tmpl` — UI 原型模板
- `scripts/ensure_uv_env.sh` / `bootstrap_project.sh` / `build_windows_exe.sh` — .ps1 的 bash 包装脚本，通过 dash 间接调用（R-01）
- `scripts/check_refs.sh` — 文件引用完整性检查（R-13）
- `scripts/ui_audit.py` — Python UI 设计质量审计（R-20）
- `scripts/ui_headless_verify.py` — 无头 UI 验证（R-19）
- `scripts/sync_examples.sh` — 示例同步脚本（R-14）
- `templates/shared/main.py` — 共享入口模板（R-14）
- `templates/inline-css/picocss.py` — PicoCSS 内联样式模板（R-06）
- `.gitignore.tmpl` / `.env.example.tmpl` — 标准项目文件（R-05）

### 修改
- **SKILL.md**：工作流增加已有项目分支（R-07）；步骤⑨引用交付清单（R-12）；最低执行清单重写为 16 项×工作流步骤映射表（F-SKILL-05）；产出物清单表（R-16）；CSS 内联铁律改为分层策略（R-02）
- **08-quality-check.md**：语法检查增加 UTF-8 编码（R-03）；增加修改后导入测试 §1b（R-21）；冒烟测试增加业务路径验证和 CDN 可用性检测（诊断模式，非阻断条件）（R-18）；增加方案 D HTML 结构验证（R-19）
- **03-ui-design.md**：CSS 框架选型增加离线可用维度（R-02）
- **04-agent-execution-and-env.md**：依赖清单补全 requests/pydantic + 常用业务依赖表（R-11）；新增 pywebview 版本验证和功能对照表（F-SKILL-06）
- **01-need-discovery.md**：场景路由表增加 API 查询型路由 + MoSCoW 优先级（R-08）
- **02-architecture.md**：新增架构设计产出物章节（含路径表+检查清单）（F-02-02）；业务流示例增加通用场景映射参考（F-02-03）；图生成指南改为"所有图类型强制交付物"（F-02-04）
- **main.py.tmpl**：支持嵌套包路径 + wait_for_server + 优雅退出（R-04）
- **pyproject.patch.toml.tmpl**：Python ≥3.10 + requests/pydantic 依赖（R-10）
- 所有示例 `pyproject.toml`：依赖格式统一（独立行）、Python 版本统一为 ≥3.10（R-14/3.3）

### 修复
- 搜索 Bug：stock 参数从 `""` 改为实际值，增加市场-代码前缀校验
- 日期验证运行时错误：修复 `_today` 变量引用断裂
- .ps1 脚本 bash 不可执行：创建 .sh 包装脚本（dash -c 间接调用）

## 1.0.0 (2026-07-16)

fasthtml-desktop 技能初始版本。整合 FastHTML + pywebview + PyInstaller 技术栈，提供完整的桌面 EXE 开发全生命周期技能。覆盖从需求澄清、架构设计、环境准备、项目初始化、界面设计、编码、验证到打包交付的 9 步工作流。

### 核心文件
- `SKILL.md` — 技能主文件（工作流 + 铁律 + 命令规则）
- 10 个 references 参考文件（需求澄清、架构设计、UI 设计、环境规范、项目结构等）
- 3 个自动化脚本（环境准备、项目初始化、打包）
- 4 个业务示例模板
- 项目蓝图骨架
