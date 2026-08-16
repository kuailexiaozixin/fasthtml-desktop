# -*- coding: utf-8 -*-
"""main.py — 02-TrafficData 桌面入口（pywebview + uvicorn）

上游 `src/devon_traffic/app.py` 是标准 src-layout 包，模块级 `app = create_app()`
即为 ASGI 应用；桌面壳只做"外挂"，**不改一行上游业务代码**：

  - src-layout 适配：把 `src/` 插入 sys.path，import `devon_traffic.app`
  - 离线图表：上游 `include_plotlyjs=False` + CDN（cdn.plot.ly）加载 plotly.js，
    断网时六个页面的图会全空白。这里在首次启动时把**已安装的 plotly 包自带的
    plotly.min.js** 复制到 `vendor/`，再把模块级常量 `PLOTLY_CDN` 指向本地路径。
    仅改运行期变量，不动上游源码；复制失败则自动退回 CDN。
    （FastHTML 内置静态路由 `/{fname:path}.{ext:static}` 以 CWD 为根，故需 chdir）
  - 打包路径适配：只读资源(_MEIPASS) 与可写数据(EXE 同级) 分离
  - find_free_port 自动端口探测；wait_for_server 等服务就绪再开窗，防白屏
  - signal/SIGINT 优雅退出
  - SERVER_ONLY=1 无头模式（服务器 / CI / 冒烟测试）

开发运行:  python main.py
无头运行:  SERVER_ONLY=1 python main.py

本示例为纯合成数据的只读看板：无数据库、无账号登录，打开即用。
"""
import os
import shutil
import signal
import socket
import sys
import threading
from pathlib import Path

APP_TITLE = "Devon Traffic Insights"
DEFAULT_PORT = 5002

if getattr(sys, "frozen", False):
    # 只读资源基目录：--add-data "src;src" 解包到 _MEIPASS（onefile 临时目录，不可写）
    RESOURCE_DIR = Path(sys._MEIPASS)
    # 可写数据基目录：EXE 同级目录（_MEIPASS 为只读临时目录，绝不能写数据到此处）
    DATA_DIR = Path(sys.executable).parent
else:
    RESOURCE_DIR = Path(__file__).parent
    DATA_DIR = Path(__file__).parent

_SRC = str(RESOURCE_DIR / "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# FastHTML 内置静态路由以 CWD 为根，vendor/ 必须落在可写目录下
os.chdir(DATA_DIR)
VENDOR_DIR = DATA_DIR / "vendor"


def ensure_local_plotly() -> str | None:
    """把已安装 plotly 包自带的 plotly.min.js 复制到 vendor/，返回可用的 URL 路径。

    成功返回 "/vendor/plotly.min.js"；plotly 未安装或包内无该文件时返回 None
    （调用方退回上游默认的 CDN 地址）。
    """
    dst = VENDOR_DIR / "plotly.min.js"
    if dst.exists() and dst.stat().st_size > 0:
        return "/vendor/plotly.min.js"
    try:
        import plotly

        src = Path(plotly.__file__).parent / "package_data" / "plotly.min.js"
        if not src.exists():
            return None
        VENDOR_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"[OK] 已缓存本地 plotly.js（{dst.stat().st_size / 1048576:.1f} MB）：{dst}")
        return "/vendor/plotly.min.js"
    except Exception as exc:  # 任何异常都不该阻断启动，退回 CDN 即可
        print(f"[WARN] 本地 plotly.js 缓存失败（{exc}），图表将改从 CDN 加载")
        return None


def find_free_port(preferred: int = DEFAULT_PORT, start: int = 5001, end: int = 6000) -> int:
    def _free(p: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", p)) != 0

    if _free(preferred):
        return preferred
    for port in range(start, end):
        if _free(port):
            return port
    raise RuntimeError("未找到可用端口")


def wait_for_server(url: str, timeout: int = 60) -> bool:
    """等待 HTTP 服务就绪（应用层响应才算真正就绪）"""
    import time

    import requests

    for _ in range(timeout):
        try:
            requests.get(url, timeout=1)
            return True
        except requests.RequestException:
            time.sleep(1)
    return False


def build_app():
    """导入上游 app 并接线离线 plotly，返回 ASGI 应用（dev_check.py 复用）。"""
    import devon_traffic.app as upstream  # 模块级 create_app()：生成全部合成数据

    local_js = ensure_local_plotly()
    if local_js:
        # 只改运行期模块变量：shell() 每次请求才读它，patch 立即生效
        upstream.PLOTLY_CDN = local_js
    else:
        print("[INFO] 使用上游默认 CDN 加载 plotly.js（需要联网才能看到图表）")
    return upstream.app


def start() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", 0)) or find_free_port()

    print("[INFO] 正在生成合成数据（首次约需数秒）...")
    application = build_app()
    print(f"[OK] {APP_TITLE} 服务启动：http://127.0.0.1:{port}")
    print("[INFO] 纯合成数据只读看板：无数据库、无需登录")
    print("[INFO] 关闭窗口或按 Ctrl+C 退出")

    server = uvicorn.Server(
        uvicorn.Config(application, host="127.0.0.1", port=port, reload=False)
    )

    def _cleanup(*_args):
        server.should_exit = True
        print("[INFO] 正在退出...")
        os._exit(0)

    signal.signal(signal.SIGINT, _cleanup)

    if os.environ.get("SERVER_ONLY") == "1":
        print("[INFO] SERVER_ONLY 模式：不创建桌面窗口，直接运行 HTTP 服务")
        server.run()
        return

    threading.Thread(target=server.run, daemon=True).start()
    if not wait_for_server(f"http://127.0.0.1:{port}/"):
        print("[WARN] 服务启动超时，仍尝试打开窗口")

    import webview

    webview.create_window(APP_TITLE, f"http://127.0.0.1:{port}", width=1440, height=900)
    print("WEBVIEW_WINDOW_OPENED", flush=True)
    webview.start()
    print("WEBVIEW_WINDOW_CLOSED", flush=True)


if __name__ == "__main__":
    start()
