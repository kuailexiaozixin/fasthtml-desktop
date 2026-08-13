# -*- coding: utf-8 -*-
"""main.py — FastInsights 桌面入口（pywebview + uvicorn）

将上游 web_app.py 的 FastHTML 应用包装为桌面应用：
  - 只读资源(_MEIPASS 顶层) 与可写数据(EXE 同级 data/) 分离
  - 通过 FASTINSIGHTS_DB 环境变量把 SQLite 重定向到可写目录
  - find_free_port 自动端口探测；wait_for_server 防白屏
  - SERVER_ONLY=1 无头模式（服务器/CI/冒烟测试）
  - import web_app 时会自动建库并播种合成数据（首次启动稍慢）

开发运行:  python main.py            （需先 python start.py 装好依赖）
无头运行:  SERVER_ONLY=1 python main.py
"""
import os, sys, socket, threading, signal
from pathlib import Path

APP_TITLE = "FastInsights"
ENV_PREFIX = "FASTINSIGHTS"
DB_FILENAME = "fastinsights.sqlite"
DEFAULT_PORT = 5008

if getattr(sys, "frozen", False):
    RESOURCE_DIR = Path(sys._MEIPASS)          # 只读资源（--add-data 解包处）
    DATA_DIR = Path(sys.executable).parent / "data"    # 可写数据（EXE 同级 data/）
else:
    RESOURCE_DIR = Path(__file__).parent
    DATA_DIR = Path(__file__).parent

DATA_DIR.mkdir(parents=True, exist_ok=True)
# SQLite 落到可写目录（onefile 的 _MEIPASS 为只读临时目录，绝不能写库到那里）
os.environ.setdefault(ENV_PREFIX + "_DB", str(DATA_DIR / DB_FILENAME))
# fast_app 的静态文件按 cwd 相对路径服务（/static/... -> ./static/...）
os.chdir(RESOURCE_DIR)
if str(RESOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(RESOURCE_DIR))



def _bootstrap_db():
    """与上游 Dockerfile 的 CMD 一致：import web_app 前先确保数据库已播种。
    （如 FastInsights 的 web.api 在 import 期就要求仓库表已存在）"""
    import db
    if not db.db_exists():
        print("[INFO] 首次启动：正在生成合成种子数据...")
        import seed
        seed.build()

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


def start() -> None:
    import uvicorn
    port = int(os.environ.get("PORT", 0)) or find_free_port(DEFAULT_PORT)
    print(f"[OK] FastInsights 服务启动: http://127.0.0.1:{port}")
    print("[INFO] 登录: admin@fastinsights.example / FastInsights2026$")
    print("[INFO] 关闭窗口或按 Ctrl+C 退出")

    # import 即触发建库+播种（_ensure_db），必须在环境变量设置之后
    _bootstrap_db()
    import web_app

    server = uvicorn.Server(uvicorn.Config(web_app.app, host="127.0.0.1", port=port, reload=False))

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
