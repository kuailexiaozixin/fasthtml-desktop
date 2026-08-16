# -*- coding: utf-8 -*-
"""desktop.py — FastLMS 桌面入口（pywebview + uvicorn）

上游 `main.py` 末尾的 `if __name__ == "__main__":` 才会 `db.bootstrap_schema()` +
`uvicorn.run()`，因此桌面壳另起 `desktop.py`（由 `launcher.json` 的 `entry` 指向），
**不改上游 main.py 的文件名**：`import main` 只注册路由、不会自行起服务。

要点：
  - 只读资源(_MEIPASS 顶层) 与可写数据(EXE 同级 data/) 分离
  - 通过 FASTLMS_DB / FASTLMS_DATA_DIR / FASTSME_AUTH_DB 把两个 SQLite 库重定向到
    可写目录（必须早于 `import db` 与 `import main`，二者在模块级读这些变量）
  - 首次启动自动 bootstrap_schema() + seed_all()（库为空时才播种，幂等）
  - find_free_port 自动端口探测；wait_for_server 防白屏
  - SERVER_ONLY=1 无头模式（服务器/CI/冒烟测试）

开发运行:  python desktop.py
无头运行:  SERVER_ONLY=1 python desktop.py

登录（两套并存，见 main.py 文档串）：
  Sign-in 弹窗 : admin@fastlms.example / FastLMS2026$
  /auth/login  : instructor@fastlms.dev / admin   （seed.py 播种）
                 student@fastlms.dev    / admin
"""
import os, sys, socket, threading, signal
from pathlib import Path

APP_TITLE = "FastLMS"
ENV_PREFIX = "FASTLMS"
DB_FILENAME = "fastlms.sqlite"
DEFAULT_PORT = 5016

if getattr(sys, "frozen", False):
    RESOURCE_DIR = Path(sys._MEIPASS)                   # 只读资源（--add-data 解包处）
    DATA_DIR = Path(sys.executable).parent / "data"     # 可写数据（EXE 同级 data/）
else:
    RESOURCE_DIR = Path(__file__).parent
    DATA_DIR = Path(__file__).parent / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)
# SQLite 落到可写目录（onefile 的 _MEIPASS 为只读临时目录，绝不能写库到那里）
os.environ.setdefault(ENV_PREFIX + "_DB", str(DATA_DIR / DB_FILENAME))
os.environ.setdefault(ENV_PREFIX + "_DATA_DIR", str(DATA_DIR))
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


def bootstrap_data() -> None:
    """建表 + 首次播种（库已有课程则跳过，避免每次启动重刷 school 表）。"""
    import sqlalchemy as sa
    import db

    db.bootstrap_schema()
    with db.connect() as conn:
        courses = conn.execute(sa.text(f"SELECT COUNT(*) FROM {db.S}.courses")).scalar() or 0
    if courses:
        return
    print("[INFO] 首次启动：播种演示课程 / 学员 / 题库 ...")
    import seed
    seed.seed_all()


def build_app():
    """建库 + 播种 + 返回 ASGI app（dev_check.py 复用）。"""
    bootstrap_data()
    import main  # 模块级会 ensure_account() 播种弹窗演示账号并 set_demo_credentials()
    return main.app, main.VALID_EMAIL, main.VALID_PASSWORD


def start() -> None:
    import uvicorn
    port = int(os.environ.get("PORT", 0)) or find_free_port(DEFAULT_PORT)

    app, email, password = build_app()
    print(f"[OK] {APP_TITLE} 服务启动: http://127.0.0.1:{port}")
    print(f"[INFO] 登录弹窗: {email} / {password}")
    print("[INFO] 原生登录页 /auth/login: instructor@fastlms.dev / admin（或 student@fastlms.dev / admin）")
    print("[INFO] AI 助教需自备 LLM Key（XAI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY）")
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
    if not wait_for_server(f"http://127.0.0.1:{port}/healthz"):
        print("[WARN] 服务启动超时，仍尝试打开窗口")

    import webview
    webview.create_window(APP_TITLE, f"http://127.0.0.1:{port}", width=1280, height=840)
    print("WEBVIEW_WINDOW_OPENED", flush=True)
    webview.start()
    print("WEBVIEW_WINDOW_CLOSED", flush=True)


if __name__ == "__main__":
    start()
