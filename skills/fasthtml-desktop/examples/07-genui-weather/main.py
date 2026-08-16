# -*- coding: utf-8 -*-
"""main.py — GenUI 桌面入口（pywebview + uvicorn 子进程拉起上游 demo）

完整克隆 kafkasl/genUI（见 README.genui.md）。本文件是「仅加桌面壳」部分，
**不修改上游任何代码**。

为什么用 `uvicorn <mod>:app` 而不是 `python <demo>/main.py`：
    fasthtml 的 `serve()` 只在**调用方模块是 `__main__`** 时才真正 `uvicorn.run(...)`
    （见 fasthtml 源码：`if glb.get('__name__')=='__main__'` 才取到 appname）。
    因此以模块方式导入时 `serve()` 自动 no-op，我们可以用 `claudette_compat.py`
    包装进程接管 uvicorn 参数：
      * 先一次性修复 claudette 0.3.14 的 `mk_ns` 多工具 bug（your_color 传 2 工具触发，
        上游代码与全局库都不动，仅在本子进程内 monkeypatch）；
      * `reload=False` —— 上游默认 `reload=True` 会 fork 出 reloader 子进程，
        父进程 terminate 后孙进程残留、端口不释放，表现为「关窗后仍占用 5001 / 启动器挂死」；
      * 端口由本壳先探测空闲位再显式指定，免去在 5001-5020 区间盲扫。

三个 demo 可通过环境变量切换：GENUI_DEMO=weather | your_color | hal9000
cwd 设为 demo 自身目录，保证 `style.css` / 图片等相对静态资源解析正确。

LLM 接入支持两种方式（壳内极简 `.env` 加载，不引入第三方依赖）：
  1. 同目录 `.env`（推荐，key 不出本目录，且已被 .gitignore 忽略）：
        ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
        ANTHROPIC_AUTH_TOKEN=sk-xxxx        # DeepSeek API Key
    也可用官方 Anthropic 端点（不设 ANTHROPIC_BASE_URL 即默认）。
  2. 系统/会话环境变量（优先级更高，已设置的不会被 .env 覆盖）。
  DeepSeek 的 Anthropic 兼容端点会把 claude-haiku/sonnet 模型名自动映射到
  deepseek-v4-flash、claude-opus 映射到 deepseek-v4-pro，故上游硬编码的
  model 名无需改动。
无 Key 时页面可打开、发起对话会报错——这是上游行为，非缺陷。

开发运行:  python main.py          （或双击 启动.bat）
无头运行:  SERVER_ONLY=1 python main.py
"""
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
DEMO = os.environ.get("GENUI_DEMO", "weather")


def load_dotenv(path: Path) -> None:
    """极简 .env 加载：KEY=VALUE 行，已存在的环境变量优先，不引入第三方依赖。"""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val
APP_TITLE = {"weather": "GenUI Weather",
             "your_color": "GenUI Your Color",
             "hal9000": "GenUI HAL 9000"}.get(DEMO, "GenUI")


def find_free_port(preferred: int = 5001) -> int:
    """优先用上游默认端口，被占则让内核分配一个空闲端口。"""
    for port in (preferred, 0):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", port))
                return s.getsockname()[1]
            except OSError:
                continue
    return preferred


def wait_for_server(url: str, timeout: int = 40) -> bool:
    """轮询直到服务可用，避免 pywebview 抢跑白屏。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1):
                return True
        except Exception:
            time.sleep(0.4)
    return False


def start() -> None:
    demo_dir = HERE / DEMO
    if not (demo_dir / "main.py").exists():
        sys.exit(f"[ERR] 未找到 demo: {demo_dir}（可选 weather / your_color / hal9000）")

    load_dotenv(HERE / ".env")
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"

    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    if not (env.get("ANTHROPIC_API_KEY") or env.get("ANTHROPIC_AUTH_TOKEN")):
        print("[WARN] 未配置 LLM API（.env 或环境变量 ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN）—— 页面可打开，但发起对话会报错。")

    # claudette_compat.py：先修复 claudette 0.3.14 的 mk_ns 多工具 bug，
    # 再等价于 `python -m uvicorn main:app --app-dir <demo>`。不动上游代码、不动全局库。
    # cwd 决定静态资源相对路径，--app-dir 决定 demo 模块导入路径，二者都指向 demo 目录。
    proc = subprocess.Popen(
        [sys.executable, str(HERE / "claudette_compat.py"),
         "--host", "127.0.0.1", "--port", str(port), "--app-dir", str(demo_dir)],
        cwd=str(demo_dir), env=env,
    )
    print(f"[OK] 已启动上游 GenUI demo「{DEMO}」子进程 (pid={proc.pid}) -> {url}")

    def _cleanup(*_a):
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
        print("WEBVIEW_WINDOW_CLOSED", flush=True)
        os._exit(0)

    signal.signal(signal.SIGINT, _cleanup)

    if not wait_for_server(url):
        print("[WARN] 服务未在预期时间内就绪，仍尝试打开窗口。")

    if os.environ.get("SERVER_ONLY") == "1":
        print(f"[INFO] SERVER_ONLY 模式：不创建桌面窗口，服务运行于 {url}")
        try:
            proc.wait()
        except KeyboardInterrupt:
            _cleanup()
        return

    import webview
    webview.create_window(APP_TITLE, url, width=1100, height=820)
    print("WEBVIEW_WINDOW_OPENED", flush=True)
    webview.start()
    _cleanup()


if __name__ == "__main__":
    start()
