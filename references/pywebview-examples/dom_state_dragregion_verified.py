# -*- coding: utf-8 -*-
"""fasthtml-desktop 缺口实证 demo：FastHTML(SSR) + pywebview 6.2.1 全流程自动验证。

验证目标（对应 skill-comparison-report.md 缺口编号）：
  A: Python DOM API —— window.dom.get_element / create_element / Element.append/text/classes/remove / ManipulationMode
  B: 无边框拖拽区 —— frameless + .pywebview-drag-region + settings['DRAG_REGION_SELECTOR']（新 API，旧 webview.DRAG_REGION_SELECTOR 已弃用）
  C: load_css / webview.settings 全字段 / window.state 双向同步 + 事件订阅(StateEventType)
  F: 应用代码使用 logging（而非 print）作为运行日志（PASS 断言输出仍用 print 便于外部采集）

运行方式：python main.py  → 自动开窗、自动断言、自动销毁窗口，最后打印 ALL_PASS / SOME_FAIL 并以 0/1 退出。
"""
import logging
import socket
import sys
import threading
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("demo")

# ---------------------------------------------------------------- FastHTML 应用（SSR，无静态 index.html）
from fasthtml.common import fast_app, Div, Input, Titled, serve  # noqa: E402
import uvicorn  # noqa: E402

app, rt = fast_app()


@rt("/")
def index():
    return Titled(
        "Gap Demo",
        Div("drag me", cls="pywebview-drag-region", id="dragbar",
            style="height:32px;background:#ddd;"),
        Div("content-area", id="content"),
        Input(id="state-input", value=""),
    )


@rt("/healthz")
def healthz():
    return {"ok": True}


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


PORT = _free_port()


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")


def wait_port(port: int, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False


# ---------------------------------------------------------------- pywebview 壳 + 自动化断言
import webview  # noqa: E402
from webview.dom import ManipulationMode  # noqa: E402
from webview.state import StateEventType  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = ""):
    RESULTS.append((name, bool(cond), detail))
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}", flush=True)


state_events: list[tuple] = []


def on_state_change(event_type, key, value):
    state_events.append((event_type, key, value))


def verify(window: webview.Window):
    try:
        window.events.loaded.wait(20)
        time.sleep(1.0)  # 等 pywebviewready 桥接完成

        # ---------- Gap C-1: webview.settings 全字段 ----------
        expected_keys = {
            "ALLOW_DOWNLOADS", "ALLOW_FILE_URLS", "DRAG_REGION_SELECTOR",
            "DRAG_REGION_DIRECT_TARGET_ONLY", "DEFAULT_HTTP_PORT",
            "OPEN_EXTERNAL_LINKS_IN_BROWSER", "OPEN_DEVTOOLS_IN_DEBUG",
            "REMOTE_DEBUGGING_PORT", "IGNORE_SSL_ERRORS", "SHOW_DEFAULT_MENUS",
            "WEBVIEW2_RUNTIME_PATH",
        }
        check("C1.settings 全 11 字段", expected_keys <= set(webview.settings.keys()),
              f"keys={sorted(webview.settings.keys())}")

        # ---------- Gap B: drag-region 机制 ----------
        check("B1.settings['DRAG_REGION_SELECTOR'] 默认值",
              webview.settings["DRAG_REGION_SELECTOR"] == ".pywebview-drag-region")
        drag_els = window.dom.get_elements(".pywebview-drag-region")
        check("B2.页面存在拖拽区元素(frameless 窗口)", len(drag_els) == 1,
              f"count={len(drag_els)}")

        # ---------- Gap A: Python DOM API ----------
        content = window.dom.get_element("#content")
        check("A1.dom.get_element", content is not None and content.id == "content",
              f"tag={getattr(content, 'tag', None)}")
        check("A2.Element.text 读取", content.text.strip() == "content-area",
              f"text={content.text!r}")

        p1 = window.dom.create_element('<p id="p1">hello-dom</p>', parent=content,
                                       mode=ManipulationMode.LastChild)
        check("A3.dom.create_element+ManipulationMode", p1 is not None and p1.tag == "p")
        check("A4.新元素 text", window.dom.get_element("#p1").text == "hello-dom")

        p1.classes.append("marked")
        check("A5.Element.classes.append", "marked" in window.dom.get_element("#p1").classes)
        p1.style["color"] = "rgb(9, 9, 9)"
        check("A6.Element.style 写入", p1.style["color"] == "rgb(9, 9, 9)",
              f"color={p1.style['color']!r}")
        p1.remove()
        check("A7.Element.remove", window.dom.get_element("#p1") is None)
        check("A8.dom.body/document/window 句柄",
              window.dom.body is not None and window.dom.document is not None
              and window.dom.window is not None)

        # ---------- Gap C-2: load_css ----------
        window.load_css("#content { background-color: rgb(1, 2, 3); }")
        time.sleep(0.5)
        bg = window.evaluate_js(
            "getComputedStyle(document.getElementById('content')).backgroundColor")
        check("C2.load_css 注入生效", bg == "rgb(1, 2, 3)", f"bg={bg!r}")

        # ---------- Gap C-3: window.state 双向 + 事件 ----------
        window.state += on_state_change          # 订阅（__iadd__ 实证存在）
        window.state.py_key = "from-python"      # Python → JS
        time.sleep(0.8)
        js_val = window.evaluate_js("window.pywebview.state.py_key")
        check("C3.state Python→JS 同步", js_val == "from-python", f"js={js_val!r}")

        window.evaluate_js("window.pywebview.state.js_key = 'from-js'")  # JS → Python
        deadline = time.time() + 5
        while time.time() < deadline and getattr(window.state, "js_key", None) != "from-js":
            time.sleep(0.2)
        check("C4.state JS→Python 同步",
              getattr(window.state, "js_key", None) == "from-js",
              f"py={getattr(window.state, 'js_key', None)!r}")
        time.sleep(0.5)
        change_keys = [k for (t, k, v) in state_events if t == StateEventType.CHANGE]
        check("C5.state 事件订阅(StateEventType.CHANGE)",
              "py_key" in change_keys, f"events={state_events}")
        window.state -= on_state_change          # __isub__ 退订

        # ---------- 业务健康端点（冒烟口径） ----------
        # 注意：evaluate_js 的代码被包裹进普通函数，不能用顶层 await（实证：SyntaxError）
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/healthz", timeout=5) as resp:
            check("S1.业务健康端点 /healthz==200", resp.status == 200, f"status={resp.status}")

    except Exception as e:  # noqa: BLE001
        log.exception("verify 阶段异常")
        check("EXC.无未捕获异常", False, repr(e))
    finally:
        window.destroy()


def main() -> int:
    threading.Thread(target=run_server, daemon=True).start()
    if not wait_port(PORT):
        print("[FAIL] server 未在 15s 内就绪", flush=True)
        return 1
    log.info("FastHTML server ready on 127.0.0.1:%s", PORT)

    window = webview.create_window(
        "gap-demo", f"http://127.0.0.1:{PORT}/",
        width=480, height=360, frameless=True, easy_drag=False,  # 真实启用 drag-region 场景
    )
    webview.start(verify, window, private_mode=True)

    ok = all(passed for _, passed, _ in RESULTS) and len(RESULTS) >= 15
    print(f"RESULT_COUNT={len(RESULTS)}", flush=True)
    print("ALL_PASS" if ok else "SOME_FAIL", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
