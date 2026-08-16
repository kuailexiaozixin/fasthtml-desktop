# 08-code-assistant — phact/code-assistant 完整克隆（仅加桌面壳）

> **定位**：本目录是 [phact/code-assistant](https://github.com/phact/code-assistant) 的**完整源码克隆**，与 `examples/03~06` 同属「重型应用参考语料」——**只外加桌面壳（`launcher.py` / `launcher.json` / `启动.bat` / `requirements.txt` / `dev_check.py`），不修改上游任何业务代码**。上游原始文档见 `README.upstream.md`，依赖锁见 `pyproject.toml` / `uv.lock`。

Code Assistant 是一个 **FastHTML 应用，用来「用 LLM 生成别的 FastHTML 应用」**：你在对话里描述想要的应用，它调用 LLM（基于 OpenAI Assistant API + astra-assistants）写代码、预览、修错，并把生成的 13 个示例应用托管为子路由。

## 核心能力

- **LLM 生成应用**：描述需求 → 生成 FastHTML 代码 → 实时预览 → 自动修 bug。
- **内置 13 个示例应用**（`code_assistant/generated_apps/`，全部上游原文）：
  `calculator_app`、`fast_game`、`fasthtml_k8s_app`、`fasthtml_mortgage_calculator`、`graphing_calculator`、`minecraft_clone`、`photo_book_app`、`riddle_generator`、`roll_dice_app`、`scavenger_hunt_app`、`sudoku_app`、`tick_tack_toe`、`trivia_app`。
- **多模型**：OpenAI / Anthropic / Claude / Groq / Gemini / 本地模型，Key 经环境变量或界面内填写。
- **生成物隔离**：启动时把内置 `generated_apps/` 拷到 `CA_GENERATED_APPS_DIR`（默认 `generated_apps/`）。

## 快速开始

```bash
# 1) 双击 启动.bat  （首次自动建"外置隔离环境"并装依赖 → 打开桌面窗口，服务端口 5001）
# 2) 只体检不启动
python launcher.py --check
# 3) 无头 / CI / 冒烟
SERVER_ONLY=1 python launcher.py server
```

### ⚠️ 本示例运行在「外置隔离环境」中（与其它示例不同）

上游锁定 `python-fasthtml==0.5.1`，与 `examples/03~06` 要求的 `>=0.12.0` **数学上不可共存**。若直接装进全局环境会把 03~06 全部搞挂。因此本示例的 `launcher.json` 配置了 `isolated_venv`，行为如下：

| 项目 | 说明 |
| --- | --- |
| 环境位置 | `%LOCALAPPDATA%\fasthtml-desktop\venvs\08-code-assistant`（**不在本目录内**，可用环境变量 `FD_VENV_HOME` 改） |
| 对全局环境的影响 | **零**。实测全局 `python-fasthtml` 保持 `0.14.9`，隔离环境内为 `0.5.1` |
| 对本目录体积的影响 | **零**。目录里不产生 `.venv` |
| 装包器 | 优先 `uv`（全局 cache 硬链接，快）；uv 失败自动回退 `pip` |
| 首次启动 | 需下载约 84 个包（~184 MB，落在上述外置目录），耗时取决于网速 |
| 二次启动 | 用 `requirements.txt` 指纹戳跳过装包，**实测 0.7s** |
| 卸载 | 直接删除上述目录即可，全局环境无残留 |

**配置 LLM Key**（无 Key 界面可开，但生成会报错）：

```bash
set OPENAI_API_KEY=sk-...        # Windows
set ANTHROPIC_API_KEY=sk-...
set CA_MODEL=gpt-4o-2024-08-06   # 可选，覆盖默认模型
set CA_GENERATED_APPS_DIR=generated_apps   # 可选，覆盖生成物目录
```

## 项目结构

```
08-code-assistant/
├── main.py                 # 桌面壳：子进程 `python -m code_assistant.code_assistant` + pywebview 包裹
├── launcher.py             # 启动器决策层（引擎拷贝，配置读 launcher.json）
├── launcher.json           # 本示例启动配置（entry=main.py / isolated_venv / 安装说明…）
├── 启动.bat                # GBK+CRLF 派发壳，仅交权给 launcher.py
├── requirements.txt        # 技能侧依赖清单（ast-grep-py/astra-assistants/python-fasthtml/python-dotenv…）
├── dev_check.py            # 质量门禁：子进程冒烟 GET / → 200
├── README.md               # 本文件
├── README.upstream.md      # 上游原始 README（改名保留）
├── pyproject.toml / uv.lock / Dockerfile / .github/   # 上游工程文件（保留）
├── code_assistant/         # 上游完整源码包（未改动）
│   ├── main.py             # 入口：模块底部 serve()（fasthtml 默认端口 5001）
│   ├── code_assistant.py   # 控制台入口 app()：读 PORT 环境变量拉起 uvicorn
│   ├── app.py / assistants.py / routes/ / constants/ / util/ / generated_apps/
└── generated_apps/         # 运行时由上游从包内拷贝生成（可写）
```

## 技术栈

`python-fasthtml` + `astra-assistants`（OpenAI Assistant API 封装，拉入 openai / anthropic 等）+ `ast-grep-py`（语法校验）+ `python-dotenv`。管理界面用 Tailwind/daisyUI/pico CDN，运行时需联网。

## 可借鉴要点（给 LLM / 构建者）

1. **「元应用」架构**：一个 FastHTML 应用负责生成并托管别的 FastHTML 应用——`routes/` 把每个 `generated_apps/*` 挂载为子路由。
2. **桌面壳模式**：上游入口 `serve()` 导入即起服务（5001），壳用子进程拉起 + 探测端口 + pywebview 包裹，零侵入。
3. **生成物隔离**：通过 `CA_GENERATED_APPS_DIR` 把 LLM 产物放到可写目录，不污染包内代码。
4. **13 个 generated_apps** 是「LLM 实际能生成的应用」的高质量语料，适合作为示例抽取候选（见下）。

## 抽取决策（供参考，本目录不执行）

13 个内置 app 不逐个拆成独立 `examples/` 条目（与 03~06「克隆重型应用」定位不同，它们是小 demo）。若需做成独立桌面示例，推荐候选：`sudoku_app` / `tick_tack_toe` / `calculator_app` / `graphing_calculator` / `fasthtml_mortgage_calculator`；不推荐 `fast_game` / `minecraft_clone`（逻辑重、依赖多）。

## 打包注意

- 依赖链重：`astra-assistants` 会拉入 `openai` / `anthropic` 等；PyInstaller 需 `--collect-submodules fasthtml`、`--collect-submodules astra_assistants`，并显式 hidden-import `dotenv`、`ast_grep_py`。
- 运行时必须可访问对应 LLM API。

## 与 03~06 的一致性

根目录平铺，上游 `code_assistant/` 包原样放置，仅追加六件套（`launcher.py` / `launcher.json` / `启动.bat` / `requirements.txt` / `dev_check.py` / `README.md`）。
