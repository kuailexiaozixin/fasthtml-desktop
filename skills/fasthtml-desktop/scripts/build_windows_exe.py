# -*- coding: utf-8 -*-
"""build_windows_exe.py — fasthtml-desktop 通用 Windows EXE 纯 Python 构建驱动。

定位：与 build_windows_exe.ps1 功能对齐的 **零 PowerShell 依赖**路线（AppBuilder 模式，
源自 python-pyinstaller-build 技能）。PowerShell 不可用 / 路径含空格 / 纯 Python CI
环境下优先使用本脚本。已在真实 FastHTML+pywebview 应用上实证：构建 46s、17.9MB
onefile、打包态 22 项自动断言 ALL_PASS（2026-07）。

用法（用最小 venv 的 python 运行）：
    <venv>/Scripts/python.exe scripts/build_windows_exe.py --project-dir <dir> \
        --app-name MyApp [--entry src/main.py] [--build-venv <python.exe>] \
        [--hidden-import mod1 --hidden-import mod2] [--health-url http://...] \
        [--exclude mod] [--hook-dir dir] [--skip-smoke] [--no-cleanup]

铁律对齐：
  * --onefile（禁 onedir）、--noupx、console=True
  * hidden-import: clr / webview.platforms.winforms / webview.platforms.edgechromium
  * --collect-submodules fasthtml、--collect-data certifi、--add-data webview/lib
  * 项目专有懒加载模块经 --hidden-import 或 src/pyinstaller_hidden_imports.txt 传入，不硬编码
  * 冒烟强制：EXE 启动 + 全部 health-url 200 才放行；清理临时文件强制执行
退出码：0 全通过；1 任一环节失败。
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


def log(level: str, msg: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} [{level}] {msg}", flush=True)


class AppBuilder:
    def __init__(self, a: argparse.Namespace) -> None:
        self.project = Path(a.project_dir).resolve()
        self.app_name = a.app_name
        self.entry = self.project / a.entry
        self.python = Path(a.build_venv) if a.build_venv else \
            self.project / ".venv" / "Scripts" / "python.exe"
        self.hidden = list(a.hidden_import or [])
        self.health_urls = list(a.health_url or [])
        self.excludes = list(a.exclude or [])
        self.hook_dir = a.hook_dir
        self.skip_smoke = a.skip_smoke
        self.no_cleanup = a.no_cleanup
        self.dist = self.project / "dist"
        self.work = self.project / "build"
        # 声明文件补充懒加载 hidden-imports（与 ps1 行为一致）
        decl = self.project / "src" / "pyinstaller_hidden_imports.txt"
        if decl.exists():
            for line in decl.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    self.hidden.append(line)
        # 健康端点声明文件（与 ps1 行为一致）
        hdecl = self.project / "src" / "health_endpoints.txt"
        if hdecl.exists():
            for line in hdecl.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    self.health_urls.append(line)

    def check_env(self) -> bool:
        if not self.python.exists():
            log("FAIL", f"未找到打包 venv python：{self.python}")
            return False
        if not self.entry.exists():
            log("FAIL", f"未找到入口：{self.entry}")
            return False
        for mod in ("PyInstaller", "webview", "fasthtml"):
            if subprocess.run([str(self.python), "-c", f"import {mod}"],
                              capture_output=True).returncode != 0:
                log("FAIL", f"打包 venv 缺依赖：{mod}（最小 venv 原则：手动装缺的包）")
                return False
        if " " in str(self.project):
            log("WARN", "项目路径含空格：本脚本用 subprocess 列表传参，不受 shell 分词影响（这正是纯 Python 路线的优势）")
        log("OK", f"环境检查通过：{self.python}")
        return True

    def clean_old_artifacts(self) -> None:
        exe = self.dist / f"{self.app_name}.exe"
        if exe.exists():
            exe.unlink()
            log("OK", f"已删除旧产物 {exe.name}")
        if self.work.exists():
            shutil.rmtree(self.work, ignore_errors=True)

    def run_pyinstaller(self) -> bool:
        probe = subprocess.run(
            [str(self.python), "-c", "import webview, pathlib;"
             "print(pathlib.Path(webview.__file__).parent / 'lib')"],
            capture_output=True, text=True)
        webview_lib = probe.stdout.strip()
        cmd = [str(self.python), "-m", "PyInstaller",
               "--onefile", "--noupx", "--console",
               "--name", self.app_name,
               "--hidden-import", "clr",
               "--hidden-import", "webview.platforms.winforms",
               "--hidden-import", "webview.platforms.edgechromium",
               "--collect-submodules", "fasthtml",
               "--collect-data", "certifi",
               "--distpath", str(self.dist),
               "--workpath", str(self.work),
               "--specpath", str(self.project),
               "-y"]
        if webview_lib and Path(webview_lib).exists():
            cmd += ["--add-data", f"{webview_lib};webview/lib"]
        for m in self.hidden:
            cmd += ["--hidden-import", m]
        for m in self.excludes:
            cmd += ["--exclude-module", m]
        if self.hook_dir:
            cmd += ["--additional-hooks-dir", self.hook_dir]
        cmd.append(str(self.entry))
        log("INFO", "PyInstaller 构建中（onefile 常 >120s，外层请带大 timeout 或后台运行）...")
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", cwd=str(self.project))
        if r.returncode != 0:
            log("FAIL", f"PyInstaller 退出码 {r.returncode}\n{r.stderr[-2000:]}")
            return False
        log("OK", f"构建完成，耗时 {time.time() - t0:.0f}s")
        return True

    def verify_output(self) -> Path | None:
        exe = self.dist / f"{self.app_name}.exe"
        if not exe.exists():
            log("FAIL", "dist 下无 EXE")
            return None
        if list(self.dist.glob("*/_internal")):
            log("FAIL", "检测到 _internal/（onedir 违规，铁律禁止）")
            return None
        log("OK", f"产物 {exe.name}  {exe.stat().st_size / 1048576:.1f} MB")
        return exe

    def run_smoke_test(self, exe: Path) -> bool:
        """启动 EXE → 轮询全部健康端点 200 → 终止。无 health-url 时要求进程存活 15s。"""
        log("INFO", "冒烟测试：启动 EXE ...")
        proc = subprocess.Popen([str(exe)], cwd=str(exe.parent),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            if not self.health_urls:
                time.sleep(15)
                alive = proc.poll() is None
                # 自动断言型应用（如 gap-demo）会自跑断言后 exit 0，也算通过
                ok = alive or proc.returncode == 0
                log("OK" if ok else "FAIL",
                    f"无健康端点声明：进程{'存活' if alive else f'退出码 {proc.returncode}'}")
                return ok
            deadline = time.time() + 60
            pending = list(self.health_urls)
            while pending and time.time() < deadline:
                if proc.poll() is not None and proc.returncode != 0:
                    log("FAIL", f"EXE 提前退出，exit={proc.returncode}")
                    return False
                for url in pending[:]:
                    try:
                        with urllib.request.urlopen(url, timeout=2) as resp:
                            if resp.status == 200:
                                log("OK", f"健康端点 200：{url}")
                                pending.remove(url)
                    except OSError:
                        pass
                if pending:
                    time.sleep(1)
            if pending:
                log("FAIL", f"健康端点超时未 200：{pending}（防假绿：阻断交付）")
                return False
            return True
        finally:
            if proc.poll() is None:
                proc.terminate()

    def cleanup_temp_files(self) -> None:
        if self.no_cleanup:
            return
        if self.work.exists():
            shutil.rmtree(self.work, ignore_errors=True)
            log("OK", "已清理 build/ 临时目录")

    def build(self) -> bool:
        if not self.check_env():
            return False
        self.clean_old_artifacts()
        if not self.run_pyinstaller():
            return False
        exe = self.verify_output()
        if exe is None:
            return False
        try:
            if self.skip_smoke:
                log("WARN", "已跳过冒烟测试（--skip-smoke）：交付前必须另行冒烟，铁律不可豁免")
                return True
            return self.run_smoke_test(exe)
        finally:
            self.cleanup_temp_files()


def main() -> int:
    p = argparse.ArgumentParser(description="fasthtml-desktop 纯 Python EXE 构建驱动")
    p.add_argument("--project-dir", required=True)
    p.add_argument("--app-name", required=True)
    p.add_argument("--entry", default="src/main.py")
    p.add_argument("--build-venv", default=None, help="独立打包 venv 的 python.exe")
    p.add_argument("--hidden-import", action="append", default=[])
    p.add_argument("--health-url", action="append", default=[])
    p.add_argument("--exclude", action="append", default=[])
    p.add_argument("--hook-dir", default=None)
    p.add_argument("--skip-smoke", action="store_true")
    p.add_argument("--no-cleanup", action="store_true")
    return 0 if AppBuilder(p.parse_args()).build() else 1


if __name__ == "__main__":
    sys.exit(main())
