# 变更记录

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
