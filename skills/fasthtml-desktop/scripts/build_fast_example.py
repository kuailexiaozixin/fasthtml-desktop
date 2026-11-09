# -*- coding: utf-8 -*-
"""build_fast_example.py — Fast* 示例（扁平布局）Windows EXE 构建驱动。

扁平布局：main.py / web_app.py / db.py / seed.py / web/ / static/ / swagger.json 全在仓库根。
对照 01-announcement-downloader 的已验证配方（SKILL.md 铁律）：
  * 冻结态 RESOURCE_DIR = sys._MEIPASS（顶层，无 app/ 子目录）——见各示例 main.py
  * --onefile --noupx --console（禁止 onedir）
  * --collect-submodules fasthtml / sqlite3；--collect-data certifi
  * hidden-import: clr / webview.platforms.winforms / webview.platforms.edgechromium
  * hidden-import: _sqlite3 / fastapi / starlette / pydantic / python_multipart
  * --additional-hooks-dir scripts/pyinstaller_hooks（hook-sqlite3 保证 _sqlite3 二进制入包）
  * webview/lib 由 pywebview 自带 PyInstaller hook 自动收集（无需手动 --add-data）
  * --add-data static；web/static；swagger.json（项目数据文件由 import 自动收集）
  * 强制冒烟：以 SERVER_ONLY=1 + 固定 PORT 启动 EXE，轮询 http://127.0.0.1:<port>/ 直到 200

用法：
    python scripts/build_fast_example.py --project-dir . --app-name FastCRM --port 5006 \
        [--build-venv C:/.../python.exe] [--skip-smoke]
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


def log(level: str, msg: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} [{level}] {msg}", flush=True)


class Builder:
    def __init__(self, a: argparse.Namespace) -> None:
        self.project = Path(a.project_dir).resolve()
        self.app = a.app_name
        self.port = a.port
        self.python = Path(a.build_venv) if a.build_venv else \
            self.project / ".venv" / "Scripts" / "python.exe"
        self.entry = self.project / "main.py"
        self.dist = self.project / "dist"
        self.work = self.project / "build"
        self.hook_dir = Path(__file__).resolve().parent / "pyinstaller_hooks"
        self.skip_smoke = a.skip_smoke

    def check(self) -> bool:
        if not self.python.exists():
            log("FAIL", f"未找到打包 venv：{self.python}")
            return False
        if not self.entry.exists():
            log("FAIL", "未找到入口 main.py")
            return False
        for m in ("PyInstaller", "webview", "fasthtml", "_sqlite3"):
            if subprocess.run([str(self.python), "-c", f"import {m}"],
                              capture_output=True).returncode != 0:
                log("FAIL", f"打包 venv 缺依赖：{m}（最小 venv 原则：手动装缺的包）")
                return False
        return True

    def clean(self) -> None:
        exe = self.dist / f"{self.app}.exe"
        if exe.exists():
            exe.unlink()
            log("OK", "已删除旧产物")
        if self.work.exists():
            shutil.rmtree(self.work, ignore_errors=True)

    def build(self) -> Path | None:
        cmd = [str(self.python), "-m", "PyInstaller",
               "--onefile", "--noupx", "--console",
               "--name", self.app,
               "--distpath", str(self.dist),
               "--workpath", str(self.work),
               "--specpath", str(self.project), "-y",
               "--collect-submodules", "fasthtml",
               "--collect-submodules", "sqlite3",
               "--collect-data", "certifi",
               "--hidden-import", "clr",
               "--hidden-import", "webview.platforms.winforms",
               "--hidden-import", "webview.platforms.edgechromium",
               "--hidden-import", "_sqlite3",
               "--hidden-import", "fastapi",
               "--hidden-import", "starlette",
               "--hidden-import", "pydantic",
               "--hidden-import", "python_multipart"]
        if self.hook_dir.exists():
            cmd += ["--additional-hooks-dir", str(self.hook_dir)]
        # webview/lib 由 pywebview 自带 PyInstaller hook 自动收集，无需手动 --add-data
        # 扁平布局：项目模块（web_app/db/seed/web）由 import 自动收集；
        # 仅 cwd 相对服务的数据文件需显式 --add-data 到 _MEIPASS 顶层。
        cmd += ["--add-data", "static;static",
                "--add-data", "web/static;web/static",
                "--add-data", "swagger.json;."]
        cmd.append(str(self.entry))
        log("INFO", "PyInstaller 构建中（onefile 常 >120s，外层请带大 timeout 或后台运行）...")
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", cwd=str(self.project))
        if r.returncode != 0:
            log("FAIL", f"PyInstaller 退出码 {r.returncode}\n{r.stderr[-3000:]}")
            return None
        log("OK", f"构建完成，耗时 {time.time() - t0:.0f}s")
        exe = self.dist / f"{self.app}.exe"
        return exe if exe.exists() else None

    def smoke(self, exe: Path) -> bool:
        url = f"http://127.0.0.1:{self.port}/"
        env = dict(os.environ)
        env["PORT"] = str(self.port)
        env["SERVER_ONLY"] = "1"   # 无头模式，仅 HTTP，避免无显示器时建窗失败
        log("INFO", f"冒烟测试：启动 EXE 并轮询 {url}（SERVER_ONLY=1）")
        proc = subprocess.Popen([str(exe)], cwd=str(exe.parent), env=env,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            deadline = time.time() + 90
            while time.time() < deadline:
                if proc.poll() is not None and proc.returncode != 0:
                    log("FAIL", f"EXE 提前退出，exit={proc.returncode}")
                    return False
                try:
                    with urllib.request.urlopen(url, timeout=2) as resp:
                        if resp.status == 200:
                            log("OK", f"健康端点 200：{url}")
                            return True
                except OSError:
                    pass
                time.sleep(1)
            log("FAIL", "健康端点超时未 200（防假绿：阻断交付）")
            return False
        finally:
            if proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
                # Windows 上 uvicorn 子线程/子进程可能残留，导致 EXE 文件被锁；
                # 用 taskkill /T 强制回收整棵进程树。
                if sys.platform.startswith("win"):
                    try:
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    except Exception:
                        pass
                try:
                    proc.wait(timeout=5)
                except Exception:
                    pass

    def run(self) -> int:
        if not self.check():
            return 1
        self.clean()
        exe = self.build()
        if exe is None:
            return 1
        log("OK", f"产物 {exe.name}  {exe.stat().st_size / 1048576:.1f} MB")
        if self.skip_smoke:
            log("WARN", "已跳过冒烟测试（--skip-smoke）：交付前必须另行冒烟，铁律不可豁免")
            return 0
        return 0 if self.smoke(exe) else 1


def main() -> int:
    p = argparse.ArgumentParser(
        description="fasthtml-desktop Fast* 示例 EXE 构建驱动",
        epilog=(
            "示例目录清洁铁律：examples 演示场景『复用全局、不建 .venv』，故不要在本脚本默认位置"
            "（<project-dir>/.venv）建打包 venv——那会在示例目录里残留 .venv，既撑大技能目录、"
            "又易被误当成『示例自带的 .venv』（正是要消除的混同）。构建示例时请传入 --build-venv"
            " 指向示例目录之外的独立 venv（如 %TEMP%/fd_build_03），构建后该 venv 可随时删除。"
        ),
    )
    p.add_argument("--project-dir", required=True)
    p.add_argument("--app-name", required=True)
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--build-venv", default=None,
                   help="独立干净打包 venv 的 python.exe（构建示例时务必指向示例目录之外，保持目录干净）")
    p.add_argument("--skip-smoke", action="store_true")
    return Builder(p.parse_args()).run()


if __name__ == "__main__":
    sys.exit(main())
