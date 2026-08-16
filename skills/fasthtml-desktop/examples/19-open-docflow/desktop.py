# -*- coding: utf-8 -*-
"""desktop.py — open-docflow 桌面入口（pywebview + uvicorn）

上游 `app.py` 自身就是应用入口（末尾 `serve(port=PORT)`），因此桌面壳另起
`desktop.py`（由 `launcher.json` 的 `entry` 指向），**不改上游 app.py 的文件名**：
`serve()` 在被 import（而非 `__main__`）时是空操作，所以 `import app` 只会
建库、播种文档类型、注册路由与认证，不会自行起服务。

要点：
  - 只读资源(_MEIPASS 顶层) 与可写数据(EXE 同级 data/) 分离
  - 通过 DOCFLOW_DB / FASTSME_AUTH_DB / DOCFLOW_UPLOAD_DIR 把 SQLite 库与上传目录
    重定向到可写目录（必须早于 `import app`：src/models.py 与 account_auth.py 在
    模块级读这些变量）
  - 上游本来是 PostgreSQL，本示例已整体改造为 SQLite，离线零依赖可跑
  - 首次启动（documents 表为空）自动调用上游 data/generate_sample.py 播种 200 条
  - find_free_port 自动端口探测；wait_for_server 防白屏
  - SERVER_ONLY=1 无头模式（服务器/CI/冒烟测试）

开发运行:  python desktop.py
无头运行:  SERVER_ONLY=1 python desktop.py

登录：admin@docflow.example / DocFlow2026$
（登录弹窗内可直接注册新账号，离线环境无需邮件验证）
"""
import os, sys, socket, threading, signal
from pathlib import Path

APP_TITLE = "open-docflow"
ENV_PREFIX = "DOCFLOW"
DB_FILENAME = "open-docflow.sqlite"
DEFAULT_PORT = 5022
SAMPLE_DOCS = 200

if getattr(sys, "frozen", False):
    RESOURCE_DIR = Path(sys._MEIPASS)                   # 只读资源（--add-data 解包处）
    DATA_DIR = Path(sys.executable).parent / "data"     # 可写数据（EXE 同级 data/）
    UPLOAD_DIR = Path(sys.executable).parent / "uploads"
else:
    RESOURCE_DIR = Path(__file__).parent
    DATA_DIR = Path(__file__).parent / "data"
    UPLOAD_DIR = Path(__file__).parent / "uploads"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# SQLite 落到可写目录（onefile 的 _MEIPASS 为只读临时目录，绝不能写库到那里）
os.environ.setdefault(ENV_PREFIX + "_DB", str(DATA_DIR / DB_FILENAME))
# 登录弹窗用的账号库（account_auth.AccountStore 在 import 时读取）
os.environ.setdefault("FASTSME_AUTH_DB", str(DATA_DIR / "fastsme-accounts.sqlite"))
# 上传文件目录（app.py 在模块级读取）
os.environ.setdefault(ENV_PREFIX + "_UPLOAD_DIR", str(UPLOAD_DIR))
# 上游用 CWD 相对路径 import（data/generate_sample.py 里有 sys.path.insert(0, ".")）
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


def seed_sample_data() -> int:
    """documents 表为空时，用上游脚本播种演示数据。返回新增条数。"""
    from src.models import Document, get_session

    session = get_session()
    try:
        if session.query(Document).count() > 0:
            return 0
    finally:
        session.close()

    from data.generate_sample import generate_documents

    generate_documents(SAMPLE_DOCS)
    return SAMPLE_DOCS


def build_app():
    """建库 + 播种 + 返回 ASGI app（dev_check.py 复用）。"""
    import app as web  # 模块级 init_db() 建表播种类型；ensure_account() 播种演示账号
    seeded = seed_sample_data()
    if seeded:
        print(f"[OK] 首次启动：已播种 {seeded} 条演示文档")
    return web.app, web.VALID_EMAIL, web.VALID_PASSWORD


def start() -> None:
    import uvicorn
    port = int(os.environ.get("PORT", 0)) or find_free_port(DEFAULT_PORT)

    application, email, password = build_app()
    print(f"[OK] {APP_TITLE} 服务启动: http://127.0.0.1:{port}")
    print(f"[INFO] 登录: {email} / {password}")
    print(f"[INFO] 数据库: {os.environ[ENV_PREFIX + '_DB']}")
    print("[INFO] 关闭窗口或按 Ctrl+C 退出")

    server = uvicorn.Server(uvicorn.Config(application, host="127.0.0.1", port=port, reload=False))

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
