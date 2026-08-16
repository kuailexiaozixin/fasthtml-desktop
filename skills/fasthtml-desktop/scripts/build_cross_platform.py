# -*- coding: utf-8 -*-
"""跨平台构建驱动（AppBuilder 式，零 PowerShell 依赖）。

用法：<最小venv-python> build_cross_platform.py \
        [--platform windows|macos|linux] [--entry main.py] [--app-name MyApp] [--dry-run]

  --platform 缺省 = 当前平台。非当前平台仅生成配置/命令预演（--dry-run 语义），不实际构建
  （PyInstaller 不支持交叉编译——这是官方事实，不是本脚本限制）。

hidden-import 矩阵（T1 源码内省铁证，pywebview 6.2.1 guilib.py + platforms/*.py，见 references/11-cross-platform.md）：
  Windows : webview.platforms.winforms + edgechromium + mshtml + clr(pythonnet)
  macOS   : webview.platforms.cocoa（依赖 pyobjc：AppKit/Foundation/WebKit/objc/PyObjCTools）+ 回退 webview.platforms.qt
  Linux   : webview.platforms.gtk（依赖 PyGObject: gi）+ 回退 webview.platforms.qt

产物形态：
  Windows → onefile exe（console=True，Web 应用铁律）
  macOS   → PyInstaller --onefile 可执行体（GUI 形态可加 --windowed 产出 .app；py2app 是另一条官方路径，见 build_macos_py2app.py）
  Linux   → PyInstaller onefile 可执行体（AppImage 需再套 appimagetool，见 build_linux_appimage.py）

实证：本脚本在 Windows + 最小 venv 下实跑 windows 目标，产出 onefile + 强制冒烟 ALL_PASS；
     macos/linux 目标在本 Windows 环境只能 DRY-RUN（命令生成正确），真实构建须在对应 OS 执行。
"""
from __future__ import annotations

import argparse
import platform as _plat
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# ---- 平台矩阵（T1 实证）----
# hidden_imports 已包含"目标平台实际会用的后端平台子模块"；pywebview 自带 hook 自动收集
# webview/lib、动态库与 webview/js，无需手动 --hidden-import webview。
MATRIX: dict[str, dict] = {
    "windows": {
        "hidden_imports": [
            "webview.platforms.winforms",      # 宿主（Windows 恒定，guilib.py）
            "webview.platforms.edgechromium",  # 主 renderer
            "webview.platforms.mshtml",        # 无 WebView2 运行时的兜底 renderer
            "clr",                             # pythonnet（winforms 顶层 import）
        ],
        "collect": ["fasthtml"],
        "collect_data": ["certifi"],
        "extra_args": ["--noupx"],
        "artifact": lambda dist, name: dist / f"{name}.exe",
    },
    "macos": {
        "hidden_imports": [
            "webview.platforms.cocoa",         # 主链
            "webview.platforms.qt",            # 回退链
            "AppKit", "Foundation", "WebKit", "objc", "PyObjCTools.AppHelper",
        ],
        "collect": ["fasthtml"],
        "collect_data": ["certifi"],
        "extra_args": [],  # GUI 形态可加 --windowed 产出 .app；调试期先 console
        "artifact": lambda dist, name: dist / name,
    },
    "linux": {
        "hidden_imports": [
            "webview.platforms.gtk",           # 主链
            "webview.platforms.qt",            # 回退链
            "gi", "gi.repository.Gtk", "gi.repository.WebKit2",  # PyGObject
        ],
        "collect": ["fasthtml"],
        "collect_data": ["certifi"],
        "extra_args": ["--noupx"],
        "artifact": lambda dist, name: dist / name,
    },
}

CURRENT = {"Windows": "windows", "Darwin": "macos", "Linux": "linux"}.get(_plat.system(), "unknown")


class AppBuilder:
    def __init__(self, target: str, entry: Path, app_name: str, dry_run: bool) -> None:
        self.target = target
        self.entry = entry
        self.app_name = app_name
        self.dry_run = dry_run
        self.cfg = MATRIX[target]
        self.dist = HERE / "dist"

    def check_deps(self) -> None:
        need = ["PyInstaller", "fasthtml", "webview", "uvicorn"]
        for mod in need:
            r = subprocess.run([sys.executable, "-c", f"import {mod}"], capture_output=True)
            if r.returncode != 0:
                raise SystemExit(f"[FATAL] 缺依赖 {mod}（最小 venv 请自查）: "
                                 f"{r.stderr.decode(errors='replace')[:200]}")
        print("[OK] 依赖检查通过（最小 venv）")

    def clean(self) -> None:
        # DRY-RUN 不清理：避免删掉并行真实构建的 build/ 目录（已实证踩坑）
        if self.target != CURRENT or self.dry_run:
            print("[SKIP] DRY-RUN / 非当前平台：不清理构建目录")
            return
        for d in (HERE / "build", HERE / f"{self.app_name}.spec"):
            if d.is_dir():
                shutil.rmtree(d)
            elif d.is_file():
                d.unlink()
        print("[OK] 旧构建产物已清理")

    def command(self) -> list[str]:
        python = sys.executable
        cmd = [python, "-m", "PyInstaller", "--onefile", "--clean", "--noconfirm",
               "--name", self.app_name, "--distpath", str(self.dist)]
        for hi in self.cfg["hidden_imports"]:
            cmd += ["--hidden-import", hi]
        for c in self.cfg["collect"]:
            cmd += ["--collect-submodules", c]
        for c in self.cfg["collect_data"]:
            cmd += ["--collect-data", c]
        cmd += self.cfg["extra_args"]
        cmd.append(str(self.entry))
        return cmd

    def build(self) -> Path | None:
        cmd = self.command()
        print("[CMD]", " ".join(cmd))
        if self.target != CURRENT or self.dry_run:
            print(f"[DRY-RUN] 目标平台 {self.target} != 当前平台 {CURRENT}（或显式 --dry-run）；"
                  f"PyInstaller 不支持交叉编译，以上命令须在目标平台执行。")
            return None  # 不可返回 Path()（Path() 即 '.'，truthy 且 exists，会误入冒烟）
        r = subprocess.run(cmd, cwd=HERE)
        if r.returncode != 0:
            raise SystemExit("[FATAL] PyInstaller 构建失败")
        art = self.cfg["artifact"](self.dist, self.app_name)
        if not art.exists():
            raise SystemExit(f"[FATAL] 产物缺失: {art}")
        print(f"[OK] 产物 {art.name}  {art.stat().st_size / 1048576:.1f} MB（最小 venv 口径）")
        return art

    def smoke(self, art: Path) -> None:
        print("[SMOKE] 启动打包产物自跑断言 ...")
        r = subprocess.run([str(art)], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300, cwd=HERE)
        out = (r.stdout or "") + (r.stderr or "")
        print("\n".join(out.strip().splitlines()[-30:]))
        if r.returncode != 0 or "ALL_PASS" not in out:
            raise SystemExit(f"[FATAL] 冒烟失败 exit={r.returncode}")
        print("[OK] 打包态冒烟通过（ALL_PASS，exit=0）")

    def cleanup(self) -> None:
        for d in (HERE / "build",):
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)
        print("[OK] 临时构建目录已清理")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--platform", choices=list(MATRIX), default=CURRENT)
    ap.add_argument("--entry", default="main.py")
    ap.add_argument("--app-name", default="MyApp")
    ap.add_argument("--dry-run", action="store_true",
                    help="仅生成命令预演，不实际构建（即便目标==当前平台）")
    args = ap.parse_args()
    if args.platform == "unknown":
        raise SystemExit("[FATAL] 无法识别当前平台")

    b = AppBuilder(args.platform, HERE / args.entry, args.app_name, args.dry_run)
    b.check_deps()
    b.clean()
    art = b.build()
    if art is not None and art.exists():
        b.smoke(art)
    b.cleanup()
    print("BUILD_RESULT=OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
