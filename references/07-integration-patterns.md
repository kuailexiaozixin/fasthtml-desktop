# 三者联调集成模式

> 本文档覆盖 fasthtml + pywebview + PyInstaller 三者协同工作时
> 原四个技能中没有任何一个覆盖的空白地带。

---

## 1. 启动顺序（最重要的设计决策）

**规则：先起 uvicorn，再开 pywebview 窗口。**

```python
# main.py — 固定模板
import sys, os, uvicorn, webview, threading
from pathlib import Path
from fasthtml.common import *

from app import app  # FastHTML 应用

def run_server():
    """在后台线程启动 FastHTTP 服务器"""
    uvicorn.run(app, host="127.0.0.1", port=PORT, reload=False)

if __name__ == "__main__":
    # 路径适配
    if getattr(sys, 'frozen', False):
        BASE_DIR = Path(sys.executable).parent
    else:
        BASE_DIR = Path(__file__).parent

    PORT = int(os.environ.get("PORT", 5001))

    # 先启服务
    threading.Thread(target=run_server, daemon=True).start()

    # 再开窗口（等待服务就绪）
    webview.create_window("我的应用", f"http://127.0.0.1:{PORT}")
    webview.start()

    # webview.start() 是阻塞的，窗口关闭后进程退出
```

### 推荐：用 `webview.start(func)` 启动后端（替代手动 threading）

pywebview 官方推荐把后端（uvicorn）作为 `start()` 的第一个参数传入，pywebview 会在独立线程中运行它，无需手动 `threading.Thread`：

```python
def run_server():
    """在独立线程启动 FastHTML 服务器"""
    uvicorn.run(app, host="127.0.0.1", port=PORT, reload=False)

if __name__ == "__main__":
    # 路径适配
    if getattr(sys, 'frozen', False):
        BASE_DIR = Path(sys.executable).parent
    else:
        BASE_DIR = Path(__file__).parent

    PORT = int(os.environ.get("PORT", 5001))

    webview.create_window("我的应用", f"http://127.0.0.1:{PORT}")
    webview.start(run_server)   # run_server 在独立（非 daemon）线程执行，见下方退出陷阱
```

> 与"手动 `threading.Thread` + `webview.start()`"写法相似但**有关键差异**，请先看下方「⚠️ 退出陷阱」。

### ⚠️ 退出陷阱（已实证）：`webview.start(func)` 的 func 跑在非 daemon 线程

`webview.start(func)` 内部用 `threading.Thread(target=func, args=args)`（**未设 daemon**）运行 `func`。若 `func`（如 uvicorn 服务）不会自行退出，则**窗口关闭后进程不会退出**——主线程 `webview.start()` 返回后，Python 仍会等待这个非 daemon 线程结束，导致残留进程（本技能实测复现）。

**安全写法（任选其一）：**

- **方案 A（推荐）：仍用 `webview.start(func)`，但在 `closed` 事件中强制退出**
  ```python
  window.events.closed += lambda: os._exit(0)   # 窗口关闭即强杀进程
  webview.start(run_server)
  ```
- **方案 B：回归上方「手动 `threading.Thread(..., daemon=True)` + `webview.start()`」固定模板**——`run_server` 是 daemon 线程，主线程结束即退出（本技能实测退出码 0，干净无残留）。
- **方案 C：让 `run_server` 可被关闭**（如捕获退出信号后 `uvicorn` 自行 `should_exit`），但实现较重，一般不推荐。

> 一句话：`webview.start(func)` 的"简洁"是有代价的——务必配合 `closed` 事件强退，或坚持用 daemon 手动模板。

### 为什么是这个顺序？

| 方案 | 问题 |
|------|------|
| 先开窗口，再起服务 | pywebview 加载空白页 / 报连接拒绝 |
| 同一线程先后启动 | uvicorn.run() 是阻塞的，窗口永远打不开 |
| 两个线程同时启动（推荐） | 服务启动中 → 窗口打开时可能仍在启动 → pywebview 自动重试加载 |

### 等待服务就绪（可选增强）

如果窗口打开时服务还没就绪，pywebview 会显示空白。以下方案可解决：

```python
import requests, time

def wait_for_server():
    """阻塞直到服务就绪"""
    for _ in range(30):
        try:
            requests.get(f"http://127.0.0.1:{PORT}", timeout=1)
            return
        except:
            time.sleep(1)

# 在线程中先等再开窗口
def open_window():
    wait_for_server()
    webview.create_window("我的应用", f"http://127.0.0.1:{PORT}")
    webview.start()

threading.Thread(target=open_window, daemon=True).start()
uvicorn.run(app, host="127.0.0.1", port=PORT, reload=False)
```

---

## 2. 端口协商

固定端口（如 5001）可能被其他程序占用。桌面 EXE 不能要求用户修改命令行参数。

```python
import socket

def find_free_port(start=5001, end=6000):
    """自动探测空闲端口"""
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    raise RuntimeError("未找到可用端口")

PORT = int(os.environ.get("PORT", 0)) or find_free_port()
```

将端口传递给 pywebview：

```python
webview.create_window("我的应用", f"http://127.0.0.1:{PORT}")
```

---

## 3. 优雅退出

关闭 pywebview 窗口后，uvicorn 线程会被回收——**但前提是它跑在 daemon 线程上**（即「手动 `threading.Thread(..., daemon=True)` + `webview.start()`」固定模板）。若使用 `webview.start(run_server)`，`run_server` 是**非 daemon** 线程，窗口关闭后进程不会退出，须按上方「⚠️ 退出陷阱」在 `closed` 事件中 `os._exit(0)` 强退。

此外，如果用户通过 Ctrl+C 在控制台终止，需要确保干净退出：

```python
import signal

def cleanup(signum=None, frame=None):
    """退出时清理资源"""
    print("\n正在关闭...")
    os._exit(0)

signal.signal(signal.SIGINT, cleanup)
```

也可监听窗口关闭事件：

```python
window = webview.create_window("我的应用", f"http://127.0.0.1:{PORT}")

def on_closed():
    print("窗口已关闭，进程退出")

window.events.closed += on_closed
webview.start()
```

---

## 4. 控制台策略

**铁律：`console=True`。**

| 技能 | 建议 | 在此技能中 |
|------|------|-----------|
| pywebview | 可 `console=False` | **被覆盖**：必须 `console=True` |
| fasthtml | `serve()` 自带控制台 | 改用 `uvicorn.run()`，仍 `console=True` |

原因：
- 用户需要看到启动日志（"服务已启动：http://127.0.0.1:5001"）
- 用户需要看到访问地址
- 调试时能看到报错信息
- `console=False` 的收益（隐藏黑窗口）小于损失（用户不知道应用是否在运行）

如果用户坚持要隐藏控制台，参考以下方案：
- 保留 `console=True`，将启动日志精简为一行
- 在 pywebview 窗口中加入启动状态提示

---

## 5. 双入口设计

开发期和打包后的入口策略不同：

| 场景 | 入口 | 方式 |
|------|------|------|
| **开发期** | 直接访问浏览器 | `uv run myapp` → 浏览器打开 `http://127.0.0.1:5001` |
| **打包后** | pywebview 桌面窗口 | 双击 EXE → 自动开窗口 |

两者共享同一套 `app.py`（业务逻辑不变），仅 `main.py` 中的入口方式不同。

### 开发期入口（不打开 pywebview）

```python
# dev_main.py — 开发用
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=5001, reload=True)
```

```bash
# 开发时用
uv run python dev_main.py
# 浏览器访问 http://127.0.0.1:5001
```

### 打包入口（pywebview 壳）

```python
# main.py — 打包用
import uvicorn, webview, threading

PORT = 5001

if __name__ == "__main__":
    threading.Thread(target=lambda: uvicorn.run("app:app", host="127.0.0.1", port=PORT, reload=False)).start()
    webview.create_window("我的应用", f"http://127.0.0.1:{PORT}")
    webview.start()
```

---

## 6. 日志体系

三个组件的日志应该统一到同一个位置：

```python
import logging

# FastHTML 应用日志
logger = logging.getLogger("app")

# uvicorn 日志
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.setLevel(logging.INFO)

# pywebview 日志（通过 events）
def on_log(msg):
    logger.info(f"[webview] {msg}")

# 所有日志写入同一个文件
handler = logging.FileHandler(BASE_DIR / "logs" / "app.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
uvicorn_logger.addHandler(handler)
```

---

## 7. 静态资源策略

**问题本质**：pywebview 加载 `http://127.0.0.1:PORT` 时，FastHTML 默认的 `static_path` / `/static/` 路由在打包后失效——打包后源码位于只读临时目录 `sys._MEIPASS`，而该路由按开发期相对路径去磁盘找文件，找不到就 404。

**三条可行路线（按场景选，并非互斥）**：

1. **内联小片段**（推荐给几行 CSS/JS）：直接写进 `Style(...)` / `Script(...)` / `Script(NotStr(...))`，零路径问题。
   ```python
   app, rt = fast_app(hdrs=(Style("body{font-family:sans-serif;margin:0}"),))
   ```
2. **vendor 大库（htmx / surreal / 业务 JS）经 `--add-data` + 冻结感知路由**（推荐给体积较大的库，避免把 50KB htmx 塞进字符串）。打包命令加 `--add-data "src;src"`（本技能 §8 快速命令已含），再用下面 `get_static_dir()` + `/vendor/*` 路由对外服务：
   ```python
   import sys
   from pathlib import Path
   from fasthtml.common import serve_static

   def get_static_dir() -> Path:
       # 开发期：源码树里的 static 目录；冻结期：sys._MEIPASS 下的同一相对路径
       if getattr(sys, "frozen", False):
           base = Path(sys._MEIPASS)
       else:
           base = Path(__file__).resolve().parents[2]   # 按项目深度调整
       return base / "src" / "rdapp" / "static"

   @rt("/vendor/{fname:path}")
   async def vendor(fname: str):
       return serve_static(fname, get_static_dir() / "vendor")
   ```
   > 实测：冻结 EXE 下 `/vendor/htmx.min.js` 完整返回 **51076 字节**，此路完全可行。`--add-data` 是本技能打包命令已含的，与「内联」互补而非二选一。
3. **运行时 CDN**（仅联网场景）：本技能不禁止 CDN（见 SKILL.md 质量门禁注），但**离线分发的 EXE 不要用**——接收方无网即白屏。

❌ 仍要避免：依赖 FastHTML 默认 `static_path` 路由在打包后不可用；`<link href="/styles.css">` 指向开发期文件 → 打包后 404。

---

## 7.1 托管第二个常驻服务（onefile 子进程重入）

桌面壳常需同时跑两样东西：你自己的 FastHTML 服务 + 一个第三方常驻进程（如本地网关、本地模型服务）。单文件 EXE 下的稳妥做法：

- **父进程只做壳**：起 FastHTML（uvicorn）+ 用 `subprocess.Popen([sys.executable, "--child"])` 拉起子进程。
- **`--child` 分支**：在 `main.py` 顶部拦截，子进程专跑常驻服务并**前台阻塞**，不进入 GUI 流程。
  ```python
  if "--child" in sys.argv:
      from launcher import run_resident_child
      run_resident_child()    # 内部启动常驻服务（如网关）；前台阻塞直到退出
      sys.exit(0)
  ```
- **冻结感知**：`sys.executable` 在 onefile 下就是 EXE 自身，重入会触发一次解压（几秒），属正常。
- **优雅退出**：父进程 `atexit` / `finally` 里 `proc.terminate()` 杀掉子进程，避免残留。
- **就绪探测用 `urllib`（stdlib，不要懒导入 `requests`）**，避免冻结后缺包崩溃：
  ```python
  import urllib.request, time
  def wait_for(url, timeout=30):
      for _ in range(timeout):
          try:
              if urllib.request.urlopen(url, timeout=1).status == 200:
                  return True
          except Exception:
              pass
          time.sleep(1)
      return False
  ```
- 完整 headless 冒烟测试门禁见本技能 `references/quality-check/04-smoke-and-delivery.md`（验证窗口 + 业务健康端点，防假绿）。

---

## 8. 常见联调故障速查

| 故障 | 原因 | 修复 |
|------|------|------|
| 窗口白屏，浏览器访问正常 | pywebview 加载 URL 时服务未就绪 | 增加 `wait_for_server()` 后再开窗口 |
| 打包后窗口白屏 | `console=False` 或端口未传递 | 确认 `console=True` 和端口传递 |
| 关闭窗口后进程不退出 | 服务线程非 daemon（`threading.Thread` 漏设 `daemon=True`，或用了 `webview.start(func)` 的非 daemon 线程） | 手动模板设 `daemon=True`；或 `webview.start(func)` 时在 `closed` 事件 `os._exit(0)`（见 §1 退出陷阱） |
| Ctrl+C 无效 | 多线程导致信号处理异常 | 添加 `signal.signal(SIGINT, cleanup)` |
| 端口被占用 | 固定端口冲突 | 使用 `find_free_port()` 自动探测 |
| 窗口能开但页面加载失败 | localhost 被安全软件拦截 | 改用 `127.0.0.1` 而非 `localhost` |
| 启动报错但窗口仍打开 | 异常未被捕获 | 加上 `try/except` 包裹服务器启动 |


## 9. 带后端交互的模态框契约（防 404 死链）

模态框若需「关闭/提交」等后端动作，必须走独立路由，禁止把 `hx_get` 指向不存在的路径。

**反例（踩坑实录，曾导致点击静默 404）**：
```python
# 错误：overlay 上的 hx_get 指向从未注册的 /close-{id}
Div(..., hx_get=f"/close-{modal_id}")   # app.py 无对应 @rt → 404
```

**正例（建议配套 `tests/test_modal_close.py` 回归测试）**：
```python
# components.modal_dialog：关闭只绑在标题栏 × 按钮
Button("×", cls="modal-close",
       hx_get=f"/close/{modal_id}",      # 指向真实存在的路由
       hx_target=f"#{modal_id}",
       hx_swap="outerHTML",
       aria_label="关闭")
# app.py 配套注册：
@rt("/close/{modal_id}")
def modal_close(modal_id: str):
    return ""   # 空串 + outerHTML 把整个 overlay 从 DOM 移除
```

**铁律**：
1. 组件内任何 `hx_get`/`href`/`action` 必须指向真实存在的路由；写完用 `python scripts/check_routes_linkage.py src/` 校验，它会把「前端引用但无后端路由」的端点列为阻断级 404 隐患。
2. 关闭/提交等破坏性动作绑在**明确的按钮**上，不要绑在 overlay 容器本身（否则点弹窗内部任意位置都会误触发）。
3. 模态框加 `role="dialog"`、`aria-modal="true"`、`aria-label=title`；关闭按钮加 `aria_label`。
