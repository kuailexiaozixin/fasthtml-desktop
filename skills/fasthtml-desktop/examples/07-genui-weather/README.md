# 07-genui-weather — GenUI 完整克隆（仅加桌面壳）

> **定位**：本目录是 [kafkasl/genUI](https://github.com/kafkasl/genUI) 的**完整克隆**，与 `examples/03~06` 同属「重型应用参考语料」——**只外加桌面壳（`main.py` / `启动-weather.bat` / `requirements.txt` / `dev_check.py`），不修改上游任何业务代码**。上游原始文档见 `README.genui.md` 与 `genui-post.md`。

GenUI 演示 **Generative UI（生成式 UI）**：让 LLM 返回「返回 FastHTML 组件的 Python 函数」作为 tool，其返回值直接成为 UI——没有 JSON 契约、没有前后端协议，只有 Python 组件。

## 核心能力

- **组件即工具（Component-as-Tool）**：LLM 通过 `client.structured(messages, tools=[WeatherComponent])` 返回组件函数，返回值即渲染结果。
- **三个独立 demo（均为上游原文，未改动）**：
  - `weather/` — 展示型：用 `WeatherComponent` 把地点渲染成天气卡（需 Claude）。
  - `your_color/` — 交互式：用户选图，LLM 生成配色 UI。
  - `hal9000/` — 融合式：带背景图/图标的对话式 UI。
- **无状态历史**：聊天记录以 `Hidden(msg, name="messages")` 随表单往返，前端无状态。
- **OOB 交换**：`ChatInput()` 用 `hx_swap_oob` 在提交后清空输入框。

## 快速开始

```bash
# 1) 双击 启动-weather.bat  （自动定位 Python → 首次 pip 装依赖 → 打开桌面窗口）
# 2) 开发模式（需先 pip install -r requirements.txt）
python main.py
# 3) 无头 / CI / 冒烟（不弹窗口，直接跑 HTTP 服务）
SERVER_ONLY=1 python main.py
```

**必须配置 LLM API Key**（weather / your_color / hal9000 都调用 LLM 生成 UI）。推荐用**用户级环境变量**（Key 不进任何文件，目录外发不泄露）：

```powershell
# Windows（用户级，永久生效，一次即可）
setx ANTHROPIC_BASE_URL "https://api.deepseek.com/anthropic"   # DeepSeek 兼容端点
setx ANTHROPIC_AUTH_TOKEN "sk-..."                             # DeepSeek API Key
# 设置后需新开终端/重启应用才生效；不设 ANTHROPIC_BASE_URL 即走 Anthropic 官方端点

# macOS/Linux（shell 配置 ~/.bashrc / ~/.zshrc）
export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
export ANTHROPIC_AUTH_TOKEN=sk-...
```

> 注意：`ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` 是 Anthropic SDK 通用变量，设全局后本机所有调用 Anthropic SDK 的程序都会走 DeepSeek——请确认这是你要的效果；仅想单目录生效时，可在同目录放 `.env`（已 gitignore），壳会优先读取环境变量、其次 `.env`。

**DeepSeek 接入说明**：DeepSeek 的 Anthropic 兼容端点（`https://api.deepseek.com/anthropic`）会把 `claude-haiku`/`claude-sonnet` 开头的模型名自动映射到 `deepseek-v4-flash`、`claude-opus` 映射到 `deepseek-v4-pro`，因此上游 `weather/main.py` 硬编码的 `claude-3-5-haiku-20241022` **无需改动**即生效。已实测端到端（真实对话 → 天气卡渲染）通过。

> **claudette 兼容性说明**：上游 `your_color` demo 向 `cli.structured()` 传入 **2 个工具**，会触发 claudette 0.3.14 的 `mk_ns(*tools)` 多参数 bug（`TypeError: mk_ns() takes 1 positional argument but 2 were given`）。该 bug 仅影响 2+ 工具的调用，weather/hal9000（单工具）不受影响。修复放在桌面壳的 `claudette_compat.py` 启动包装里：在 uvicorn 子进程内把 `mk_ns` 包成可变参数版本，**不修改全局 site-packages、也不修改任何上游 genUI 代码**。三个 demo 现已全部经 DeepSeek 实测跑通。

> 无 Key 时页面可打开，但发起对话会报错——这是上游行为，非缺陷。

运行其他两个 demo（壳默认只拉起 `weather`）：

```bash
cd weather   && python main.py     # 或 your_color / hal9000
```

## 项目结构

```
07-genui-weather/
├── main.py                 # 桌面壳：子进程拉起 demo + pywebview 包裹；含极简 .env 加载（可选）
├── claudette_compat.py     # claudette 0.3.14 兼容启动包装：修复 mk_ns 多工具 bug（仅桌面壳，不动上游）
├── 启动-weather.bat                # GBK+CRLF 启动器（定位 Python / 装依赖 / WebView2 检测）
├── requirements.txt        # 技能侧依赖清单（fasthtml/monsterui/fastcore/claudette…）
├── dev_check.py            # 质量门禁：子进程冒烟 GET / → 200
├── README.md               # 本文件
├── README.genui.md         # 上游原始 README（改名保留）
├── requirements.genui.txt  # 上游原始依赖（改名保留）
├── weather/                # 上游 demo（未改动）
├── your_color/             # 上游 demo（未改动）
├── hal9000/                # 上游 demo（未改动）
├── genui-post.md / index.md / _config.yml   # 上游文档
```

## 技术栈

`python-fasthtml`（FastHTML + HTMX）+ `monsterui`（Tailwind 风格组件）+ `fastcore` + `claudette`（Anthropic 封装）。样式经 monsterui CDN 注入，运行时需联网。

## 可借鉴要点（给 LLM / 构建者）

1. **组件即工具**是 GenUI 的灵魂：tool 的返回值是 UI 组件而非数据，省掉序列化层。
2. **无状态历史**：用 `Hidden` 字段把消息列表塞回每个请求，后端无需存会话。
3. **OOB 交换**清空输入框：`hx_swap_oob='true'` 让提交后的输入组件被替换。
4. 三个 demo 覆盖「展示 / 交互 / 融合」三种生成式 UI 形态，是学习该范式的最佳语料。
5. **桌面壳模式**：上游 `serve()` 导入即起服务（fasthtml 默认端口 5001），壳用子进程拉起 + 探测端口 + pywebview 包裹，零侵入。

## 打包注意

- 依赖含 `monsterui` / `claudette`（Anthropic SDK），体积较大；PyInstaller 需 `--collect-submodules fasthtml` 并显式 hidden-import `monsterui`、`claudette`、`anthropic`。
- 运行时必须可访问 Anthropic API（或改 `weather/main.py` 的 `model` 与 `Client` 指向本地模型——但那属于改上游，本目录不这么做）。

## 与 03~06 的一致性

本示例遵循 `examples/` 统一约定：**根目录平铺**（无 `src/` 子目录），上游代码原样放置，仅追加 `main.py`(pywebview 壳) / `启动-weather.bat` / `requirements.txt` / `dev_check.py` / `README.md` 五件套。
