# -*- coding: utf-8 -*-
"""main.py — Code Assistant 桌面入口（pywebview + 子进程拉起上游服务）

完整克隆 phact/code-assistant（见 README.upstream.md）。本文件是「仅加桌面壳」部分，
**不修改上游任何代码**：上游 code_assistant.main 在模块底部 serve()，导入即起服务
（fasthtml 默认端口 5001）；控制台入口 code_assistant.code_assistant:app 读 PORT 环境变量
（默认 5001）后拉起 uvicorn。故用子进程 `python -m code_assistant.code_assistant` 拉起，
探测端口后 pywebview 包裹。

生成应用需要 LLM Key（OpenAI / Anthropic / Claude / Groq / Gemini …）：可在界面内填，
或经环境变量（OPENAI_API_KEY / ANTHROPIC_API_KEY / CA_MODEL 等）传入。
无 Key 时界面可打开，生成会报错——这是上游行为，非缺陷。

开发运行:  python main.py
无头运行:  SERVER_ONLY=1 python main.py
"""
import os, sys, signal, subprocess, time
from pathlib import Path

APP_TITLE = "Code Assistant"
HERE = Path(__file__).parent
GENERATED_APPS_DIR = HERE / "generated_apps"
DEFAULT_PORT = 5001


def probe_port(host="127.0.0.1", ports=range(5001, 5021), path="/", timeout=40):
    import httpx
    deadline = time.time() + timeout
    while time.time() < deadline:
        for p in ports:
            try:
                r = httpx.get(f"http://{host}:{p}{path}", timeout=0.5)
                if r.status_code < 500:
                    return p
            except Exception:
                pass
        time.sleep(0.4)
    return None


def wait_for_server(url, timeout=30):
    import httpx
    for _ in range(timeout):
        try:
            httpx.get(url, timeout=1)
            return True
        except Exception:
            time.sleep(1)
    return False


def start():
    GENERATED_APPS_DIR.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    # code_assistant 启动时会把内置 generated_apps 拷到 CA_GENERATED_APPS_DIR。
    # 上游 config.py 用 `os.getcwd() + "/" + CA_GENERATED_APPS_DIR`，因此这里必须是相对路径。
    env["CA_GENERATED_APPS_DIR"] = "generated_apps"

    proc = subprocess.Popen(
        [sys.executable, "-m", "code_assistant.code_assistant"],
        cwd=str(HERE), env=env,
        stdout=None, stderr=None,
    )
    print(f"[OK] 已启动上游 Code Assistant 子进程 (pid={proc.pid})")

    def _cleanup(*_a):
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        print("WEBVIEW_WINDOW_CLOSED", flush=True)
        os._exit(0)

    signal.signal(signal.SIGINT, _cleanup)

    port = probe_port()
    if port is None:
        print("[WARN] 未能探测到服务端口，回退到默认 5001")
        port = DEFAULT_PORT
    url = f"http://127.0.0.1:{port}"
    print(f"[OK] Code Assistant 服务: {url}")

    if os.environ.get("SERVER_ONLY") == "1":
        print("[INFO] SERVER_ONLY 模式：不创建桌面窗口，直接运行 HTTP 服务")
        proc.wait()
        return

    wait_for_server(url)
    import webview
    webview.create_window(APP_TITLE, url, width=1280, height=840)
    print("WEBVIEW_WINDOW_OPENED", flush=True)
    webview.start()
    _cleanup()


if __name__ == "__main__":
    start()
