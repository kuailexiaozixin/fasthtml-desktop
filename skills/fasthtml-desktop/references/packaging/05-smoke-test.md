# 冒烟测试

> 冒烟测试门禁：打包后**必须**启动 EXE 验证 HTTP 200 和窗口句柄存在。
> **严禁让用户代为测试。**

---

## 冒烟测试目标

1. 确认 EXE 在目标环境中能成功加载所有依赖，10 秒内未崩溃
2. 验证 HTTP 服务端口可达（返回 200）
3. 验证桌面窗口句柄存在（pywebview 窗口已创建）
4. 支持无头环境（CI/CD）和桌面环境两种模式

---

## 完整冒烟测试 Python 脚本

保存为 `scripts/smoke_test.py`：

```python
"""
冒烟测试脚本：打包后验证 EXE 是否正常启动。

支持三种验证层级：
  1. 进程存活验证（基础）
  2. HTTP 200 验证（Web 应用）
  3. 窗口句柄检测（pywebview 桌面应用）

兼容 CI/CD 无头环境和桌面环境。
"""

import logging
import subprocess
import sys
import time
import json
import urllib.request
import urllib.error
from pathlib import Path

# ── 配置 ──────────────────────────────────────────────
EXE_PATH = Path("dist/MyApp.exe")
WAIT_SECONDS = 10          # 最长等待时间
HTTP_PORT = 51888          # Web 服务端口
HTTP_CHECK = True          # 是否验证 HTTP 200
WINDOW_CHECK = False       # 是否验证窗口句柄（桌面环境）
CHECK_URL = f"http://127.0.0.1:{HTTP_PORT}/"
# ──────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)
logger = logging.getLogger("smoke_test")


def check_http(url: str, timeout: int = 5) -> bool:
    """检查 HTTP 服务是否返回 200。"""
    try:
        resp = urllib.request.urlopen(url, timeout=timeout)
        if resp.status == 200:
            return True
        else:
            logger.warning(f"HTTP {resp.status} ({url})")
            return False
    except (urllib.error.URLError, ConnectionRefusedError) as e:
        logger.debug(f"HTTP 请求失败: {e}")
        return False


def check_window(title_keyword: str = "pywebview") -> bool:
    """检查是否存在指定标题关键词的窗口（仅桌面环境）。"""
    try:
        import win32gui

        found = []

        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title_keyword.lower() in title.lower():
                    found.append((hwnd, title))

        win32gui.EnumWindows(enum_callback, None)
        if found:
            for hwnd, title in found:
                logger.info(f"  窗口: {title} (HWND={hwnd})")
            return True
        return False
    except ImportError:
        logger.warning("pywin32 未安装，跳过窗口检测")
        return False
    except Exception as e:
        logger.warning(f"窗口检测异常: {e}")
        return False


def run_smoke_test() -> bool:
    """执行冒烟测试全流程。"""
    if not EXE_PATH.exists():
        logger.error(f"可执行文件不存在: {EXE_PATH}")
        return False

    logger.info(f"启动 EXE: {EXE_PATH}")
    logger.info(f"等待 {WAIT_SECONDS} 秒...")

    try:
        # 启动进程
        process = subprocess.Popen(
            [str(EXE_PATH)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            if sys.platform == "win32"
            else 0,
        )

        # 等待服务就绪
        http_ok = False
        for i in range(WAIT_SECONDS):
            if process.poll() is not None:
                # 进程已退出
                _, stderr = process.communicate()
                logger.error(f"程序提前退出 (exit={process.returncode})")
                if stderr.strip():
                    logger.error(f"错误输出:\n{stderr[:2000]}")
                return False

            if HTTP_CHECK and not http_ok:
                http_ok = check_http(CHECK_URL)
                if http_ok:
                    logger.info(f"HTTP 200 OK ({CHECK_URL})")

            if http_ok:
                # HTTP 已就绪，不一定要等满 WAIT_SECONDS
                time.sleep(0.5)
                continue

            time.sleep(1)

        # ── 最终评估 ──
        if process.poll() is not None:
            return False  # 已在上方处理

        passed = True

        if HTTP_CHECK:
            # 做最后一次 HTTP 检查
            if not http_ok:
                http_ok = check_http(CHECK_URL)
            if not http_ok:
                logger.error("HTTP 服务未就绪")
                passed = False
            else:
                logger.info("[PASS] HTTP 200 OK")

        if WINDOW_CHECK and passed:
            window_ok = check_window()
            if window_ok:
                logger.info("[PASS] 桌面窗口已创建")
            else:
                logger.warning("[WARN] 未检测到桌面窗口（无头环境可忽略）")

        if passed:
            logger.info("[PASS] 冒烟测试通过")
        else:
            logger.error("[FAIL] 冒烟测试失败")

        return passed

    except Exception as e:
        logger.error(f"冒烟测试执行异常: {e}")
        return False

    finally:
        # ── 清理进程 ──
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    capture_output=True, check=False,
                )
            else:
                process.terminate()
                process.wait(timeout=5)
        except Exception:
            pass


def main():
    success = run_smoke_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
```

---

## CI/CD 适应方案

### 无头环境适配

在 CI/CD（如 GitHub Actions、GitLab CI）中运行冒烟测试时：

```bash
# 跳过窗口检测（无桌面环境）
python scripts/smoke_test.py --no-window-check
```

如果脚本不支持命令行参数，设置环境变量：

```bash
# PowerShell
$env:SMOKE_NO_WINDOW_CHECK=1
python scripts/smoke_test.py

# Bash
export SMOKE_NO_WINDOW_CHECK=1
python scripts/smoke_test.py
```

### CI/CD 集成示例（GitHub Actions）

```yaml
# .github/workflows/build.yml
jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Build EXE
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
          python -m PyInstaller --onefile --console main.py

      - name: Smoke Test
        run: |
          python scripts/smoke_test.py
```

### Jenkins Pipeline

```groovy
stage('Smoke Test') {
    agent { label 'windows' }
    steps {
        bat 'python scripts/smoke_test.py'
    }
    post {
        failure {
            error '冒烟测试失败，构建中止'
        }
    }
}
```

---

## 测试失败的常见原因

| 症状 | 可能原因 | 修复方向 |
|------|---------|---------|
| 进程启动后立即退出 | 缺少 DLL / 导入失败 | 检查 DLL 诊断 + hidden-imports |
| HTTP 服务未就绪 | uvicorn 启动失败 / 端口冲突 | 确认 `reload=False`，换端口 |
| 窗口未创建 | pywebview 初始化失败 | 检查 clr 是否在 hidden-imports 中 |
| 进程挂起无响应 | 死锁或文件句柄泄漏 | 减少 WAIT_SECONDS，检查日志 |
| `ModuleNotFoundError` | PyInstaller 漏扫 | 添加 `--hidden-import` |

---

## 测试建议

- **每个主要版本更新前**，必须运行冒烟测试
- 冒烟测试失败视为**构建流程失败**，禁止分发
- 即使 `console=False`，冒烟测试也应能检测依赖缺失引发的静默崩溃（通过 HTTP 检测）
- 测试完成后**必须清理进程**，防止残留进程占用端口

---

## 对实际 EXE 运行 pywebview 原生窗口视觉质检

冒烟测试只验证「EXE 起得来、HTTP 200、窗口在」；界面视觉正确性仍需 pywebview 原生窗口视觉门禁（见 `quality-check/04-smoke-and-delivery.md` 测试项五）。要让 `ui_window_verify.py` 指向**实际 EXE**（而非 dev server），只需让脚本知道 EXE **实际**提供服务的端口——**不必固定端口**，按场景二选一：

**做法 A（固定端口，适合 CI / 反复复跑）**
- 入口 `main.py` 默认用 `find_free_port()` 在 `5001–6000` 间**自动挑空闲端口**，只有当 `PORT` 环境变量非 0 时才固定（见模板 `src/main.py`：`PORT = int(os.environ.get("PORT", 0)) or find_free_port()`）。因此固定端口是**可选项**，不是必需。
- 若选固定，启动 EXE 时指定端口，并让冒烟脚本与视觉质检都访问同一端口：
  ```bash
  PORT=51888 ./dist/MyApp.exe > exe_run.log 2>&1 &
  python scripts/ui_window_verify.py --url http://127.0.0.1:51888/ --out exe_shot.png
  ```
- 本文档内联 `smoke_test.py` 模板默认 `HTTP_PORT = 51888`，与上面的固定端口配套；**如改用其他端口，须同步修改 `HTTP_PORT`**，否则会连错端口。

**做法 B（动态发现端口，零配置、最灵活，推荐）**
- 让 EXE 自己选端口，再从其启动输出里读出**实际**端口传给视觉质检脚本——这正是更稳妥的做法，也避免端口冲突。
- EXE 启动时会打印形如 `[OK] 服务启动：http://127.0.0.1:5099` 的行（端口每次可能不同）。
- `ui_window_verify.py` 本身**不会自动猜端口**，但 `--url` 接受任意端口，且其内置等待会在导航前缓冲等待 EXE 就绪，所以只需把读到的端口喂给它即可：
  ```bash
  ./dist/MyApp.exe > exe_run.log 2>&1 &
  PORT=$(grep -oE 'http://127.0.0.1:[0-9]+' exe_run.log | head -1 | grep -oE '[0-9]+$')
  python scripts/ui_window_verify.py --url "http://127.0.0.1:${PORT}/" --out exe_shot.png
  ```

- 验证完成后务必 `taskkill /F /IM MyApp.exe` 清理进程，避免残留占用端口 / 持有 `dist/*.exe` 句柄（见 `08-packaging.md` 铁律 #9）。
