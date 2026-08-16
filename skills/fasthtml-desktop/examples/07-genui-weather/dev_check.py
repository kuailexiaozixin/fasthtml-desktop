# -*- coding: utf-8 -*-
"""dev_check.py — GenUI 质量门禁（子进程冒烟，不弹窗口）

启动上游 weather demo 子进程，探测端口后 GET / 断言 200，再退出。
需要先用 启动.bat 或 `pip install -r requirements.txt` 装好依赖
（python-fasthtml / monsterui / fastcore / claudette / httpx）。
全部通过 exit 0；任一失败 exit 1（供 CI / 打包前门禁串联）。
"""
import os, sys, subprocess, time
from pathlib import Path

HERE = Path(__file__).parent


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


def check(name, ok, detail=""):
    print(("[PASS] " if ok else "[FAIL] ") + name + (f"  ({detail})" if detail else ""))
    return ok


def main():
    env = dict(os.environ)
    proc = subprocess.Popen([sys.executable, "weather/main.py"], cwd=str(HERE), env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        port = probe_port()
        ok_index = False
        detail = ""
        if port is None:
            detail = "未在 40s 内探测到服务端口"
        else:
            import httpx
            r = httpx.get(f"http://127.0.0.1:{port}/", timeout=5)
            ok_index = r.status_code == 200
            detail = f"status={r.status_code}"
        if not check("GET / 返回 200", ok_index, detail):
            sys.exit(1)
        print("[GATE] 全部通过，可交付/可打包")
        sys.exit(0)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    main()
