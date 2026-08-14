# -*- coding: utf-8 -*-
"""gen_launchers.py — 以 templates/shared/launcher.py 为唯一真源，分发自包含启动器到 examples。

与旧 sync_launchers.py 的本质区别：
  * 旧方案把配置用**脆弱的正则**渲染进 `run.py` 的「配置区」——一旦配置区格式稍有变动，
    正则即失配、整片启动器出错（这正是用户反馈"模板太僵硬、BUG 多"的根因）。
  * 新方案把 `launcher.py` 当作**无状态引擎**，所有项目差异放进同目录的 `launcher.json`；
    本脚本只做三件零风险的事：① 复制引擎（launcher.py 在 20 个示例间逐字节相同）；
    ② 写出 launcher.json（纯 JSON，可被任何工具读取/校验，不再 parse 代码）；
    ③ 写出 启动.bat（GBK+CRLF，≤8 行）。改逻辑只改引擎；改某示例只改它的 json。

产出（每个示例目录）：
  * `launcher.py`   —— 引擎副本（逐字一致，由本脚本从真源复制）
  * `launcher.json` —— 本项目配置（app_name / entry / use_venv / isolated_venv /
                        bundled_venv / auto_install / side_processes / install_note / startup_note）
  * `启动.bat`      —— ≤8 行派发壳，GBK/ANSI + CRLF（cmd.exe 硬要求），只 `python launcher.py %*`
                      文件名默认 `启动.bat`，可用 CONFIGS 的 `BAT_NAME` 逐示例覆盖（如 07 改为 `启动-weather.bat`）
  * （旧 `run.py` 在此被删除，避免双启动器并存）

用法：
    python scripts/gen_launchers.py            # 分发 + 清理旧 run.py
    python scripts/gen_launchers.py --diff     # 只比对，不写入
    python scripts/gen_launchers.py --keep-run # 分发但不删旧 run.py（灰度用）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SHARED_ENGINE = SKILL / "templates" / "shared" / "launcher.py"
EXAMPLES = SKILL / "examples"

# ≤8 行派发壳：cd -> 确认 PATH 有可用 python -> 交给 launcher.py。绝不在此实现任何决策逻辑。
BAT = """@echo off
setlocal
cd /d "%~dp0"
python -c "import sys;sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul
if errorlevel 1 (echo [启动.bat] 未找到可用的 Python 3.10+，请先安装并加入 PATH: https://www.python.org/downloads/ & pause & exit /b 1)
python "%~dp0launcher.py" %*
if errorlevel 1 pause
"""

# 原 run.py「配置区」键 -> launcher.json 键（顺序即 JSON 输出顺序）
_REMAP = [
    ("APP_NAME", "app_name"),
    ("ENTRY", "entry"),
    ("USE_VENV", "use_venv"),
    ("ISOLATED_VENV", "isolated_venv"),
    ("BUNDLED_VENV", "bundled_venv"),
    ("AUTO_INSTALL", "auto_install"),
    ("SIDE_PROCESSES", "side_processes"),
    ("INSTALL_NOTE", "install_note"),
    ("STARTUP_NOTE", "startup_note"),
]

# 各示例配置（与旧 sync_launchers.py 的 CONFIGS 同义，键名沿用 run.py 配置区命名）。
CONFIGS: dict[str, dict] = {
    # 01/02：predictivelabsai 系列「完整克隆 + 仅加桌面壳」引入（Bricksmith / TrafficData）。
    # 01 为 RAG 知识库（SQLite + sqlite-vec，无外部数据库服务）；02 为纯合成数据只读看板（无 DB 无登录）。
    "01-Bricksmith": dict(
        APP_NAME="Bricksmith",
        STARTUP_NOTE="提示：聊天/RAG 问答需要配置大模型 API Key —— 在 .env 中填入 XAI_API_KEY 或 OPENAI_API_KEY（任选其一，OPENAI_BASE_URL 可指向兼容网关）。\n    未配置 Key 时桌面窗口与所有落地页仍可正常打开，仅对话接口会报错。\n    数据库为本地 SQLite（data/bricksmith.db），由应用首次启动时自动建表，无需外部服务。",
    ),
    "02-TrafficData": dict(
        APP_NAME="Devon Traffic Insights",
        STARTUP_NOTE="提示：本示例为纯合成数据的只读看板 —— 无数据库、无需注册登录、无需任何 API Key，双击即可查看全部六个分析页面。\n    首次启动会生成约 2.3 万条合成观测数据（数秒），并把 plotly.js 从已安装的 plotly 包缓存到 vendor/ 目录，之后完全离线可用。",
    ),
    "03-FastCRM": dict(APP_NAME="FastCRM"),
    "04-FastERP": dict(APP_NAME="FastERP"),
    # 04/05 的 -latest：predictivelabsai 上游「完整版」克隆（保留 migrations/fasterp/ATS 等全部模块），
    # 仅加桌面壳（main.py 包装 web_app.app + 建库播种），不精简不删减功能。
    "04-FastERP-latest": dict(APP_NAME="FastERP"),
    "05-FastHRM": dict(APP_NAME="FastHRM"),
    "05-FastHRM-latest": dict(APP_NAME="FastHRM"),
    "06-FastInsights": dict(APP_NAME="FastInsights"),
    # 07：genUI Weather（kafkasl/genUI 完整克隆 + 仅加桌面壳）。上游 serve() 默认端口 5001，
    # 调用 LLM 生成 UI，需 LLM API Key；推荐用户级环境变量（setx ANTHROPIC_BASE_URL=…/anthropic
    # + setx ANTHROPIC_AUTH_TOKEN=<Key>，Key 不进文件、目录外发不泄露）；壳 main.py 也支持同目录
    # .env（已 gitignore，环境变量优先）。DeepSeek 端点会把 claude-haiku/sonnet 模型名自动映射到
    # deepseek-v4-flash，上游 model 无需改动。依赖走 CDN、无离线兜底（上游行为）。
    "07-genui-weather": dict(
        APP_NAME="GenUI Weather",
        BAT_NAME="启动-weather.bat",
        STARTUP_NOTE="[提示] 本示例调用 LLM 生成 UI：推荐用用户级环境变量（setx ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic + setx ANTHROPIC_AUTH_TOKEN=<DeepSeek Key>），\n    也可在示例目录 .env 配置（环境变量优先于 .env）。未配置时页面可打开，发起对话会报错（上游行为，非缺陷）。",
    ),
    # 08：code-assistant（phact/code-assistant 完整克隆 + 仅加桌面壳）。上游锁定 python-fasthtml==0.5.1，
    # 与 03-06 的 >=0.12.0 互斥，故走外置隔离环境（isolated_venv），全局环境不被降级。
    "08-code-assistant": dict(
        APP_NAME="Code Assistant",
        ISOLATED_VENV="08-code-assistant",
        AUTO_INSTALL=False,
        INSTALL_NOTE="    [版本互斥] 上游 code-assistant 锁定 python-fasthtml==0.5.1，与 examples/03-06 的 >=0.12.0 数学上不可共存。\n    因此本示例在「示例目录之外」的隔离环境中运行，全局环境不会被降级，示例目录也不会膨胀。",
        STARTUP_NOTE="[提示] 本示例需 LLM API Key（如 OPENAI_API_KEY / ANTHROPIC_API_KEY）；未设置时页面可打开，发起生成会报错（上游行为，非缺陷）。",
    ),
    "09-FastSheets": dict(APP_NAME="FastSheets"),
    "10-FastSlides": dict(APP_NAME="FastSlides"),
    "11-FastDrive": dict(APP_NAME="FastDrive"),
    # 12-15：上游入口在 `if __name__ == "__main__"` 里才起服务（且 import 即建库），
    # 因此外挂独立桌面壳 `desktop.py`。launcher 的 resolve_entry() 只认 src/main.py|main.py，
    # 必须在此显式声明 entry，否则会误拉起上游 main.py 而绕过壳的库路径重定向。
    "12-FastLegal": dict(
        APP_NAME="FastLegal",
        ENTRY="desktop.py",
        STARTUP_NOTE="[提示] AI 助手需按需安装 LLM SDK 并配 Key（三选一）："
                     "langchain-openai / langchain-anthropic / langchain-google-genai；"
                     "未装时业务功能不受影响，仅助手页发起对话会报错。",
    ),
    "13-FastLMS": dict(APP_NAME="FastLMS", ENTRY="desktop.py"),
    "14-FastMeet": dict(APP_NAME="FastMeet", ENTRY="desktop.py"),
    "15-FastMail": dict(APP_NAME="FastMail", ENTRY="desktop.py"),
    # 16-20：predictivelabsai 系列「完整克隆 + 仅加桌面壳」，同 12-15 同构，外挂 desktop.py。
    # 上游入口只在 __main__ 起服务 / import 即建库，launcher 入口探测只认 src/main.py|main.py，
    # 必须显式 entry="desktop.py" 指过去（否则会误拉上游 main.py 绕过壳的库路径重定向）。
    # 全部用 SQLite 离线运行（PostgreSQL 已替换为 SQLite），account_auth 登录/注册离线修复。
    "16-FastDocs": dict(APP_NAME="FastDocs", ENTRY="desktop.py"),
    "17-FastESM": dict(APP_NAME="FastESM", ENTRY="desktop.py"),
    "18-FastMSR": dict(APP_NAME="FastMSR", ENTRY="desktop.py"),
    "19-open-docflow": dict(APP_NAME="open-docflow", ENTRY="desktop.py"),
    "20-FastHelpdesk": dict(APP_NAME="FastHelpdesk", ENTRY="desktop.py"),
}


def to_json_cfg(cfg: dict) -> dict:
    """把 run.py 配置区键映射到 launcher.json 键，只输出非默认/显式声明的字段。"""
    out: dict = {}
    for old_key, new_key in _REMAP:
        if old_key in cfg:
            out[new_key] = cfg[old_key]
    return out


def main() -> int:
    diff_only = "--diff" in sys.argv[1:]
    keep_run = "--keep-run" in sys.argv[1:]
    if not SHARED_ENGINE.exists():
        raise SystemExit(f"[ERR] 缺少引擎真源: {SHARED_ENGINE}")

    # 以字节写入，避免 Windows 上 write_text 的默认 newline 翻译把 \n 变成 \r\n，
    # 从而保证「launcher.py 在 20 个示例间逐字节相同」这一核心不变量。
    engine_bytes = SHARED_ENGINE.read_bytes()
    bat_bytes = BAT.replace("\n", "\r\n").encode("gbk")

    changed = 0
    for name, cfg in CONFIGS.items():
        d = EXAMPLES / name
        if not d.is_dir():
            print(f"[SKIP] 示例目录不存在: {d}")
            continue

        json_cfg = to_json_cfg(cfg)
        json_text = json.dumps(json_cfg, ensure_ascii=False, indent=2) + "\n"
        json_bytes = json_text.encode("utf-8")
        py_path = d / "launcher.py"
        json_path = d / "launcher.json"
        bat_name = cfg.get("BAT_NAME", "启动.bat")
        bat_path = d / bat_name
        run_path = d / "run.py"

        py_diff = (not py_path.exists()) or py_path.read_bytes() != engine_bytes
        json_diff = (not json_path.exists()) or json_path.read_bytes() != json_bytes
        bat_diff = (not bat_path.exists()) or bat_path.read_bytes() != bat_bytes
        run_exists = run_path.exists()

        if diff_only:
            flags = "".join([
                "  [launcher.py]" if py_diff else "",
                "  [launcher.json]" if json_diff else "",
                "  [bat]" if bat_diff else "",
                "  [run.py 待删]" if run_exists else "",
            ])
            print(f"{'DIFF' if (py_diff or json_diff or bat_diff or run_exists) else 'OK  '} {name}{flags}")
            continue

        if py_diff:
            py_path.write_bytes(engine_bytes)
        if json_diff:
            json_path.write_bytes(json_bytes)
        if bat_diff:
            bat_path.write_bytes(bat_bytes)
        changed += int(py_diff) + int(json_diff) + int(bat_diff)

        # 删除旧 run.py：本就是「删掉 run.py 模板」的一部分，避免双启动器并存。
        if run_exists and not keep_run:
            run_path.unlink()
            changed += 1

        print(f"[OK] {name}: launcher.py + launcher.json + {bat_name}"
              + (f"  (已删 run.py)" if (run_exists and not keep_run) else ""))

    if not diff_only:
        print(f"=== done（写入/清理 {changed} 个文件）===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
