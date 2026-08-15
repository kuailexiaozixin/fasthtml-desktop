# dsh-fasthtml-desktop

将 **fasthtml-desktop** 技能打包为 [DeepSeek Harness (dsh)](https://deepseek-ai.github.io/deepseek-harness/) 插件的 **Cordis Bundle**。

- **形态**：Cordis Bundle（Host 侧 / Node 后端组合包）
- **类型**：skill 插件（嵌入式提供方，参照官方 `@deepseek-ai/dsh-skill-badge`）
- **作用**：把 `fasthtml-desktop` 技能注册到 dsh 的 `ctx.skills`，让 dsh Agent 在会话中通过 `skill` 工具加载并使用它，从需求澄清到打包含原生窗口 EXE 的完整 FastHTML 桌面开发链路。

## 目录结构

```
dsh-plugin/
├── package.json       # 声明 dsh.bundle → cordis.patch.yml
├── cordis.patch.yml   # 插入插件行（name = 包名）
├── index.js           # ctx.skills.registerProvider 注册嵌入式 skill
└── assets/
    └── SKILL.md       # 技能正文（与技能仓库根 SKILL.md 同步）
```

## 安装

在已安装 `dsh` CLI 的机器上，进入本技能仓库根目录，将插件装入一个 profile（如 `web`）：

```bash
dsh plugin --profile web add ./dsh-plugin
```

首次使用会初始化该 profile，pnpm 链接此目录，`dsh` 因 `dsh.bundle` 声明把 `dsh-fasthtml-desktop` 追加进 `dsh.profile.bundles`。

先验证配置层，再启动：

```bash
dsh --profile web --dump-config   # 应能看到 "# == dsh-fasthtml-desktop" 层
dsh web                           # 启动 Web UI
```

> 说明：`assets/SKILL.md` 是技能正文的副本。如需同步最新内容，复制技能根 `SKILL.md` 覆盖它。

## 使用

启动 dsh Web UI 后，直接对 Agent 说一句即可触发：

> 「用 fasthtml-desktop 技能，帮我做一个带 Web 界面的客户管理桌面程序，打包成 EXE。」

Agent 会调用 `skill` 工具加载 `fasthtml-desktop`，按 SKILL.md 的工作流与铁律完成从脚手架到打包的完整链路。`resourceBase` 指向技能仓库根目录，`references/`、`scripts/`、`examples/` 等相对路径均可被模型按需解析。

## 移除

```bash
dsh plugin --profile web remove dsh-fasthtml-desktop
```

会同时移除依赖与对应的 bundle 层。
