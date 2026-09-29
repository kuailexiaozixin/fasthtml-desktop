# fasthtml-desktop

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![skills.sh](https://skills.sh/b/kuailexiaozixin/fasthtml-desktop)](https://skills.sh/kuailexiaozixin/fasthtml-desktop)

**FastHTML + pywebview** 桌面应用的全生命周期 **Agent Skill**——从需求澄清、FastHTML Web 开发、pywebview 桌面壳包装到 PyInstaller 打包交付，最终交付物是包含 **pywebview 原生窗口**的 FastHTML 桌面 EXE（WebView2 渲染，本地 HTTP 服务）。

> **Agent Skill 是什么？** Skill 是「指令 + 脚本 + 资源」的文件夹，AI Agent 会动态发现并加载它，以在特定任务上表现得更好。本仓库遵循 [Agent Skills 开放标准](https://agentskills.io)——**一次编写，处处使用**，可被 Claude、灵犀、Codex 等支持该标准的助手直接读取。

---

## 这是什么

本技能为 AI Agent 提供一套**标准化、可复现**的 FastHTML 桌面应用开发流程，用 Web 技术栈做出带原生窗口的桌面程序：

- **Web 技术栈做桌面**：FastHTML + HTMX 构建界面，pywebview 提供原生窗口（WebView2 渲染）
- **权威文档 HARD-GATE**：`references/05-coding/fasthtml-refs/fasthtml-llms-ctx.txt`（约 1 万行官方上下文）为写码前必读
- **23 个参考实现**：`examples/` 为 FastOffice 套件（ERP、财务、HRM、BI、文档、表格、法务等真实业务场景）
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

本仓库遵循 [Agent Skills 开放标准](https://agentskills.io)，技能位于 `skills/fasthtml-desktop/`（符合 `gh skill` 的 `skills/*/SKILL.md` 发现约定），可用 **GitHub CLI（≥ v2.90.0）** 一键安装：

```bash
# 安装到当前项目（project 作用域，默认）
gh skill install kuailexiaozixin/fasthtml-desktop

# 或安装到用户全局（user 作用域，所有项目可用）
gh skill install kuailexiaozixin/fasthtml-desktop --scope user

# 查看/搜索/校验
gh skill list
gh skill preview kuailexiaozixin/fasthtml-desktop
```

> 安装时技能被发现为 `fasthtml-desktop`；`gh skill install` 会按需自动注入来源元数据（`metadata.github-*`），支持 `gh skill update` 增量更新与 `--pin <tag>` 版本锁定。

Agent Skills 通常已内置在支持该标准的助手中（Claude、Codex、灵犀、DeepSeek Harness 等原生支持，可直接读取本仓库）；也可将本仓库显式添加为 **Skill / Plugin**：

```bash
# 以支持 AgentSkills 的助手为例（如 Claude Code）
/plugin marketplace add kuailexiaozixin/fasthtml-desktop
```

本仓库同时已打包为**可分发 dsh 插件**（DeepSeek Harness，Cordis Bundle）发布到 npm，在 Harness 中可用一条命令安装：

```bash
dsh plugin --profile web add dsh-fasthtml-desktop
```

> 也可从 [GitHub Release](https://github.com/kuailexiaozixin/fasthtml-desktop/releases) 下载源码归档离线安装。详见下方「作为 dsh 插件使用」章节。

安装后，只需对助手说一句，例如：

> 「用 fasthtml-desktop 技能，帮我做一个带 Web 界面的客户管理桌面程序，打包成 EXE。」

助手会读取 `SKILL.md`，按其中的工作流与铁律自动完成从脚手架到打包的完整链路。

---

## 作为 dsh 插件使用

本技能已发布为 [DeepSeek Harness (dsh)](https://deepseek-ai.github.io/deepseek-harness/) 的 **Cordis Bundle** 插件 **`dsh-fasthtml-desktop`**（npm 包，网络上的任何人均可在其 dsh 中直接安装）。插件把技能注册进 dsh 的 `ctx.skills`，让 dsh Agent 在会话中通过 `skill` 工具加载使用。**形态**为 Cordis Bundle（Host 侧），**类型**为 skill 插件（嵌入式提供方，参照官方 `dsh-skill-badge`）。

本插件为**自包含**的可分发 npm 包：npm 包根 = 技能仓库根，`resourceBase` 指向包根，SKILL.md 及其引用的 references/、examples/ 等资源全部随包安装，不依赖发布者的机器或仓库位置。

### 安装（命令行，从 npm 分发）

**前置**：已安装 `dsh` CLI（与 `pnpm`）。从 npm 安装插件并装入任意 profile（如 `web`）：

```bash
dsh plugin --profile web add dsh-fasthtml-desktop
```

验证配置层并启动：

```bash
dsh --profile web --dump-config   # 应看到 "# == dsh-fasthtml-desktop" 层
dsh web
```

### 从 GitHub Release 下载安装

不依赖 npm，可直接从 GitHub Releases 页面下载源码归档离线安装：

```bash
# 下载源码归档（zip 或 tar.gz），以下载最新 Release 为例
curl -L -o fasthtml-desktop.zip \
  https://github.com/kuailexiaozixin/fasthtml-desktop/archive/refs/heads/main.zip
unzip fasthtml-desktop.zip      # 得到 fasthtml-desktop-main/（技能位于 skills/fasthtml-desktop/）
```

解压后有两种安装方式：

**方式一：放入 dsh 技能发现目录（推荐，最简单）**

把 `skills/fasthtml-desktop` 目录重命名为技能名（kebab-case，不含版本号）后放进用户技能目录，dsh 启动时即自动发现：

```bash
mkdir -p ~/.dsh/skills
mv fasthtml-desktop-main/skills/fasthtml-desktop ~/.dsh/skills/fasthtml-desktop
dsh web    # 重启后即可通过 skill 工具加载
```

> 用户技能目录默认 `<dshHome>/skills`，Windows 下为 `C:\Users\<用户名>\.dsh\skills\`。

**方式二：作为 dsh 插件从本地目录安装**

```bash
dsh plugin --profile web add /绝对路径/fasthtml-desktop-main/skills/fasthtml-desktop
```

> `dsh plugin add` 支持本地目录路径（pnpm 语义），与从 npm 安装等价。

### 使用

启动 dsh Web UI 后，对 Agent 说一句即可触发，例如：

> 「用 fasthtml-desktop 技能，帮我做一个带 Web 界面的客户管理桌面程序，打包成 EXE。」

Agent 会调用 `skill` 工具加载本技能，按 `SKILL.md` 的工作流完成从脚手架到打包的完整链路。

### 移除

```bash
dsh plugin --profile web remove dsh-fasthtml-desktop
```

---

## 目录结构

仓库遵循 gh skill 标准发布树（技能本体自包含于 `skills/fasthtml-desktop/`）：

```
fasthtml-desktop/                # 仓库根
├── skills/
│   └── fasthtml-desktop/        # 技能根（gh skill 发现路径 skills/*/SKILL.md）
│       ├── SKILL.md             # 技能主入口（工作流①→⑨ + 铁律内联）
│       ├── CHANGELOG.md         # 版本变更记录
│       ├── LICENSE              # MIT 许可证
│       ├── README.md            # 本文件
│       ├── references/          # 深度参考（按工作流①→⑨编号）
│       │   ├── 02-architecture/ # ② 架构设计（18 章 + 模块设计）
│       │   ├── 05-coding/       # ⑤ 编码（含 fasthtml-refs/ 官方上下文、pywebview-examples/）
│       │   ├── 07-quality-gate/ # ⑦ 质量门禁（Check/Test/Debug 三层）
│       │   ├── 08-packaging/    # ⑧ 打包（深度指南 + 跨平台 + 7 子专题）
│       │   └── ...
│       ├── examples/            # 23 个参考实现（FastOffice 套件，优先参考）
│       │   ├── FastERP          # ERP（订单到收款/采购到付款/会计引擎）
│       │   ├── FastAccounts     # 财务总账（复式记账）
│       │   ├── FastBI           # BI 分析平台（RAG 问答）
│       │   ├── FastLegal        # 法务 AI
│       │   ├── FastSheets       # 电子表格
│       │   └── ...              # 完整列表见 examples/README.md
│       ├── templates/           # 项目脚手架模板
│       ├── scripts/             # 构建、校验、门禁自动化脚本
│       ├── docs/                # 交付清单、术语表、排障
│       ├── package.json         # npm 包声明（dsh-fasthtml-desktop，Cordis Bundle）
│       ├── index.js             # 嵌入式 skill 提供方
│       └── cordis.patch.yml     # dsh bundle patch（注册插件）
├── .github/workflows/ci.yml     # gh skill publish --dry-run + 目录结构校验
├── .gitattributes               # 强制 .bat 以 CRLF 分发
└── README.md                    # 仓库级说明（本文件为技能内说明）
```

---

## 快速开始（给 Agent）

1. **读取入口**：`SKILL.md` 定义完整工作流与铁律。
2. **写 FastHTML 代码前**：必读 `references/05-coding/fasthtml-refs/fasthtml-llms-ctx.txt`（HARD-GATE），注意与 FastAPI 的语法差异。
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

`examples/` 目录下的参考实现为 **FastOffice 套件 23 个项目**，均来自 Predictive Labs（`predictivelabsai` 组织）（FastERP 等 18 个项目 MIT、FastPE/FastVC/liquidround Apache-2.0、FastLegal AGPL-3.0、FastWiki 无声明）。完整来源、许可证与使用注意详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

---

## 许可证

[MIT](LICENSE) © kuailexiaozixin

---

**相关**：同系列的 [tkinter-desktop](https://github.com/kuailexiaozixin/tkinter-desktop)（原生 Tkinter 方案，技术栈互斥，可作对比）。
