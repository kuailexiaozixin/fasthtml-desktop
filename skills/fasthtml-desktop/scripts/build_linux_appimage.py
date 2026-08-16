# -*- coding: utf-8 -*-
"""Linux AppImage 构建脚本（fasthtml + pywebview gtk 路径）。

⚠️ 仅能在 Linux 上执行（PyInstaller 不支持交叉编译）。
流程：PyInstaller onefile → AppDir 骨架（AppRun + .desktop + icon）→ appimagetool。

前置（以 Debian/Ubuntu 为例）：
  sudo apt install python3-venv libgirepository1.0-dev gir1.2-webkit2-4.1 libgtk-3-dev
  python3 -m venv venv && . venv/bin/activate
  pip install python-fasthtml pywebview PyGObject pyinstaller
  # appimagetool: https://github.com/AppImage/appimagetool/releases (chmod +x, 加入 PATH)

用法：python build_linux_appimage.py [--entry main.py] [--app-name MyApp] [--icon assets/icon.png]
产物：dist/<AppName>-x86_64.AppImage
校验：./dist/<AppName>-x86_64.AppImage  → demo 自跑断言 ALL_PASS（退出码 0）
"""
from __future__ import annotations

import argparse
import base64
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# 1x1 透明 PNG（AppImage 规范要求 icon；无真实图标时的占位）
_PLACEHOLDER_PNG = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    b"YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")


def _run(cmd: list[str], **kw) -> None:
    print("[CMD]", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True, **kw)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entry", default="main.py")
    ap.add_argument("--app-name", default="MyApp")
    ap.add_argument("--icon", default=None, help="可选 .png 图标路径")
    args = ap.parse_args()

    if sys.platform != "linux":
        print(f"[FATAL] 本脚本仅限 Linux 执行（当前 {sys.platform}）。"
              "PyInstaller 不支持交叉编译。")
        return 1

    entry = HERE / args.entry
    if not entry.exists():
        print(f"[FATAL] 入口文件不存在: {entry}")
        return 1

    name = args.app_name
    dist = HERE / "dist"

    # 1) PyInstaller onefile（hidden-import 矩阵来自 pywebview 6.2.1 guilib/gtk.py 源码内省）
    _run([sys.executable, "-m", "PyInstaller", "--onefile", "--clean", "--noconfirm",
          "--name", name, "--distpath", str(dist),
          "--hidden-import", "webview.platforms.gtk",
          "--hidden-import", "webview.platforms.qt",
          "--hidden-import", "gi",
          "--hidden-import", "gi.repository.Gtk",
          "--hidden-import", "gi.repository.WebKit2",
          "--collect-submodules", "fasthtml",
          "--noupx",
          str(entry)], cwd=HERE)

    exe = dist / name
    if not exe.exists():
        print("[FATAL] PyInstaller 产物缺失")
        return 1

    # 2) AppDir 骨架
    appdir = HERE / f"{name}.AppDir"
    if appdir.exists():
        shutil.rmtree(appdir)
    (appdir / "usr" / "bin").mkdir(parents=True)
    shutil.copy2(exe, appdir / "usr" / "bin" / name)

    desktop = (
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={name}\n"
        f"Exec={name}\n"
        f"Icon={name.lower()}\n"
        "Categories=Utility;\n"
    )
    (appdir / f"{name}.desktop").write_text(desktop, encoding="utf-8")

    apprun = (
        "#!/bin/sh\n"
        'HERE="$(dirname "$(readlink -f "$0")")"\n'
        f'exec "$HERE/usr/bin/{name}" "$@"\n'
    )
    apprun_path = appdir / "AppRun"
    apprun_path.write_text(apprun, encoding="utf-8")
    apprun_path.chmod(0o755)

    icon = Path(args.icon).resolve() if args.icon else None
    if icon and icon.exists():
        shutil.copy2(icon, appdir / f"{name.lower()}.png")
    else:
        (appdir / f"{name.lower()}.png").write_bytes(_PLACEHOLDER_PNG)

    # 3) appimagetool
    tool = shutil.which("appimagetool")
    if not tool:
        print("[WARN] 未找到 appimagetool，AppDir 已就绪：", appdir)
        print("       手动执行: appimagetool", appdir)
        return 0
    _run([tool, str(appdir), str(dist / f"{name}-x86_64.AppImage")])
    print("BUILD_RESULT=OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
