# fasthtml-desktop

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![skills.sh](https://skills.sh/b/kuailexiaozixin/fasthtml-desktop)](https://skills.sh/kuailexiaozixin/fasthtml-desktop)

**FastHTML + pywebview** 桌面应用的全生命周期 **Agent Skill**——从需求澄清、FastHTML Web 开发、pywebview 桌面壳包装到 PyInstaller 打包交付，最终交付物是包含 **pywebview 原生窗口**的 FastHTML 桌面 EXE（WebView2 渲染，本地 HTTP 服务）。

> **Agent Skill 是什么？** Skill 是「指令 + 脚本 + 资源」的文件夹，AI Agent 会动态发现并加载它，以在特定任务上表现得更好。本仓库遵循 [Agent Skills 开放标准](https://agentskills.io)——**一次编写，处处使用**，可被 Claude、灵犀、Codex 等支持该标准的助手直接读取。

---

## 这是什么

本技能为 AI Agent 提供一套**标准化、可复现**的 FastHTML 桌面应用开发流程，用 Web 技术栈做出带原生窗口的桌面程序：

- **Web 技术栈做桌面**：FastHTML + HTMX 构建界面，pywebview 提供原生窗口（WebView2 渲染）
- **权威文档 HARD-GATE**：`references/fasthtml-refs/fasthtml-llms-ctx.txt`（约 1 万行官方上下文）为写码前必读
- **20+ 参考实现**：`examples/` 覆盖 CRM、ERP、HRM、财务、进销存、法律、文档、表单等真实业务场景
- **完整质量门禁**：路由联动检查、引用检查、无头 UI 验证、release gate
- **跨平台构建**：Windows / macOS / Linux 构建脚本齐全

适合：需要现代 Web 界面、又希望以**原生桌面应用**交付的业务系统。

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

## 安装 / 使用

Agent Skills 通常已内置在支持该标准的助手中；也可将本仓库添加为 **Skill / Plugin**：

```bash
# 以支持 AgentSkills 的助手为例（如 Claude Code）
/plugin marketplace add kuailexiaozixin/fasthtml-desktop
```

安装后，只需对助手说一句，例如：

> 「用 fasthtml-desktop 技能，帮我做一个带 Web 界面的客户管理桌面程序，打包成 EXE。」

助手会读取 `SKILL.md`，按其中的工作流与铁律自动完成从脚手架到打包的完整链路。

---

## 目录结构

```
fasthtml-desktop/
├── SKILL.md              # 技能主入口（工作流 + 铁律）
├── CHANGELOG.md          # 版本变更记录
├── LICENSE               # MIT 许可证
├── README.md             # 本文件
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

## 贡献

欢迎提交 Issue 与 PR 完善工作流。请遵循：

- 改动技能核心逻辑时，同步更新 `SKILL.md`、`references/` 与 `CHANGELOG.md`
- 新增参考实现请放入 `examples/`，并登记到 `examples/README.md`
- 保持「权威文档 HARD-GATE + 质量门禁 + 跨平台构建」的铁律不被破坏

详见 [contributing.md](contributing.md)。

---

## 第三方内容与合规

`examples/` 目录下的参考实现部分**源自第三方开源项目**（Frappe 生态移植版、完整克隆等），各 example 保留自身许可证与版权声明。其中 `07-genui-weather`、`08-code-assistant` 的上游**未声明许可证**（默认保留所有权利），存在合规风险，不建议再分发。完整来源、许可证与使用注意详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

---

## 许可证

[MIT](LICENSE) © kuailexiaozixin

---

**相关**：同系列的 [tkinter-desktop](https://github.com/kuailexiaozixin/tkinter-desktop)（原生 Tkinter 方案，技术栈互斥，可作对比）。
