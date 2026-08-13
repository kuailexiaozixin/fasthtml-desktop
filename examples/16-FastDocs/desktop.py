# -*- coding: utf-8 -*-
"""desktop.py — FastDocs 桌面入口（pywebview + uvicorn）

上游 `web_app.py` 自身就是应用入口（末尾 `serve(port=PORT)`），因此桌面壳另起
`desktop.py`（由 `launcher.json` 的 `entry` 指向），**不改上游 web_app.py 的文件名**：
`serve()` 在被 import（而非 `__main__`）时是空操作，所以 `import web_app` 只会
建库、播种、注册路由，不会自行起服务。

要点：
  - 只读资源(_MEIPASS 顶层) 与可写数据(EXE 同级 data/) 分离
  - 通过 FASTDOCS_DB / FASTSME_AUTH_DB 把两个 SQLite 库重定向到可写目录
    （必须早于 `import web_app`：db.py 与 account_auth.py 在模块级读这两个变量）
  - 首次启动由上游 `_ensure_db()` 自动播种演示数据（幂等）
  - find_free_port 自动端口探测；wait_for_server 防白屏
  - SERVER_ONLY=1 无头模式（服务器/CI/冒烟测试）

开发运行:  python desktop.py
无头运行:  SERVER_ONLY=1 python desktop.py

登录（两套并存）：
  Sign-in 弹窗 / 原生登录页 : admin@fastdocs.example / FastDocs2026$
"""
import os, sys, socket, threading, signal
from pathlib import Path

APP_TITLE = "FastDocs"
ENV_PREFIX = "FASTDOCS"
DB_FILENAME = "fastdocs.sqlite"
DEFAULT_PORT = 5019

if getattr(sys, "frozen", False):
    RESOURCE_DIR = Path(sys._MEIPASS)                   # 只读资源（--add-data 解包处）
    DATA_DIR = Path(sys.executable).parent / "data"     # 可写数据（EXE 同级 data/）
else:
    RESOURCE_DIR = Path(__file__).parent
    DATA_DIR = Path(__file__).parent / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)
# SQLite 落到可写目录（onefile 的 _MEIPASS 为只读临时目录，绝不能写库到那里）
os.environ.setdefault(ENV_PREFIX + "_DB", str(DATA_DIR / DB_FILENAME))
# 登录弹窗用的账号库（account_auth.AccountStore 在 import 时读取）
os.environ.setdefault("FASTSME_AUTH_DB", str(DATA_DIR / "fastsme-accounts.sqlite"))
# 上游用 CWD 相对路径提供 static/，故切到资源目录
os.chdir(RESOURCE_DIR)
if str(RESOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(RESOURCE_DIR))


def find_free_port(preferred: int, start: int = 5001, end: int = 6000) -> int:
    def _free(p):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", p)) != 0
    if _free(preferred):
        return preferred
    for port in range(start, end):
        if _free(port):
            return port
    raise RuntimeError("未找到可用端口")


def wait_for_server(url: str, timeout: int = 30) -> bool:
    import time
    import httpx
    for _ in range(timeout):
        try:
            httpx.get(url, timeout=1)
            return True
        except Exception:
            time.sleep(1)
    return False


def build_app():
    """建库 + 播种 + 返回 ASGI app（dev_check.py 复用）。"""
    import web_app  # 模块级 _ensure_db() 播种；ensure_account() 播种弹窗演示账号
    return web_app.app, web_app.VALID_EMAIL, web_app.VALID_PASSWORD


def start() -> None:
    import uvicorn
    port = int(os.environ.get("PORT", 0)) or find_free_port(DEFAULT_PORT)

    app, email, password = build_app()
    print(f"[OK] {APP_TITLE} 服务启动: http://127.0.0.1:{port}")
    print(f"[INFO] 登录: {email} / {password}")
    print("[INFO] AI 助手需自备 LLM Key（OPENAI_API_KEY / ANTHROPIC_API_KEY / XAI_API_KEY）")
    print("[INFO] 关闭窗口或按 Ctrl+C 退出")

    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, reload=False))

    def _cleanup(*_a):
        server.should_exit = True
        print("[INFO] 正在退出...")
        os._exit(0)
    signal.signal(signal.SIGINT, _cleanup)

    if os.environ.get("SERVER_ONLY") == "1":
        print("[INFO] SERVER_ONLY 模式：不创建桌面窗口，直接运行 HTTP 服务")
        server.run()
        return

    threading.Thread(target=server.run, daemon=True).start()
    if not wait_for_server(f"http://127.0.0.1:{port}/login"):
        print("[WARN] 服务启动超时，仍尝试打开窗口")

    import webview
    webview.create_window(APP_TITLE, f"http://127.0.0.1:{port}", width=1280, height=840)
    print("WEBVIEW_WINDOW_OPENED", flush=True)
    webview.start()
    print("WEBVIEW_WINDOW_CLOSED", flush=True)


if __name__ == "__main__":
    start()
