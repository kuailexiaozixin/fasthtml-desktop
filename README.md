# fasthtml-desktop

**FastHTML + pywebview** 桌面应用的全生命周期 AI 技能（Agent Skill）。从需求澄清、FastHTML Web 开发、pywebview 桌面壳包装到 PyInstaller 打包交付，最终交付物是包含 **pywebview 原生窗口**的 FastHTML 桌面 EXE（WebView2 渲染，本地 HTTP 服务）。

> 本技能以 `SKILL.md` 为入口，面向 AI Agent（如 Claude / 灵犀等支持 AgentSkills 规范的助手）。AI 读取后即可按标准化流程辅助开发 FastHTML 桌面应用。

---

## 技术栈

| 层 | 选型 | 说明 |
|----|------|------|
| Web 框架 | **FastHTML** | 基于 Starlette + HTMX 的 Python Web 框架 |
| 桌面壳 | **pywebview** | 原生窗口内嵌 WebView2 渲染 |
| 交互 | **HTMX** | 服务端驱动的前端交互 |
| 打包 | **PyInstaller** | 产出含原生窗口的 Windows EXE |
| 跨平台 | 辅助脚本 | macOS (py2app) / Linux (AppImage) |

---

## 特性

- **Web 技术栈做桌面**：用 HTML/FastHTML/HTMX 构建界面，pywebview 提供原生窗口
- **HARD-GATE 权威文档**：`references/fasthtml-refs/fasthtml-llms-ctx.txt`（约 1 万行官方上下文）为写代码前必读
- **20+ 参考实现**：`examples/` 覆盖 CRM、ERP、HRM、财务、进销存、法律、文档、表单等真实业务场景
- **完整质量门禁**：路由联动检查（`check_routes_linkage.py`）、引用检查（`check_refs.sh`）、无头 UI 验证、release gate
- **统一脚手架**：`templates/` 一键生成项目（含 `启动.bat` 双用途 README 启动器）
- **跨平台构建**：Windows / macOS / Linux 构建脚本齐全

---

## 目录结构

```
fasthtml-desktop/
├── SKILL.md              # 技能主入口（工作流 + 铁律）
├── CHANGELOG.md          # 版本变更记录
├── references/           # 深度参考（架构、模块设计、打包、TDD、集成模式等）
│   └── fasthtml-refs/    # FastHTML 官方上下文转档（写码前必读）
├── examples/             # 20+ 参考实现（优先参考）
│   ├── 03-FastCRM        # 客户关系管理
│   ├── 04-FastERP        # 企业资源计划
│   ├── 05-FastHRM        # 人事管理
│   ├── 06-FastInsights   # 数据洞察
│   ├── 09-FastSheets     # 电子表格
│   ├── 12-FastLegal      # 法律服务
│   └── ...               # 完整列表见 examples/README.md
├── templates/            # 项目脚手架模板
├── scripts/              # 构建、校验、门禁自动化脚本
├── docs/                 # 交付清单、术语表、排障
└── examples/README.md
```

---

## 快速开始（给 Agent）

1. **读取入口**：`SKILL.md` 定义完整工作流与铁律。
2. **写 FastHTML 代码前**：必读 `references/fasthtml-refs/fasthtml-llms-ctx.txt`（HARD-GATE），注意与 FastAPI 的语法差异。
3. **生成项目**：用 `templates/` 脚手架（`bootstrap_project.sh` / `ensure_uv_env`）初始化。
4. **开发迭代**：FastHTML 路由 + HTMX 交互，参考 `examples/` 中与业务最接近的项目。
5. **质量门禁**：路由联动检查 + 引用检查 + 无头 UI 验证 + `release_gate.py`。
6. **打包**：`scripts/build_windows_exe` 产出 EXE，跨平台用 `build_cross_platform.py`。

---

## 许可与来源

- 由 AI Agent 按 AgentSkills 规范创建并维护，`author: agent`
- 开源用于学习与二次开发，欢迎提交 Issue / PR 完善工作流

---

**相关**：同系列的 [tkinter-desktop](https://github.com/kuailexiaozixin/tkinter-desktop)（原生 Tkinter 方案，技术栈互斥，可作对比）。
