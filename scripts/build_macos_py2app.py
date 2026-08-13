# -*- coding: utf-8 -*-
"""macOS py2app 打包脚本（fasthtml + pywebview cocoa 路径）。

⚠️ 仅能在 macOS 上执行：py2app 是 macOS 专属打包器。
来源：pywebview 技能 scripts/py2app_setup.py + freezing.md，针对 FastHTML 场景适配：
  - FastHTML 是纯 Python SSR，无静态 HTML —— DATA_FILES 不需要 web 资源目录；
  - packages 须含 fasthtml（其模块动态 import 多，等价于 PyInstaller --collect-submodules fasthtml）；
  - pywebview cocoa 后端依赖 pyobjc（AppKit/WebKit 等），py2app 对 pyobjc 有原生识别。

前置（macOS）：
  python3 -m venv venv && source venv/bin/activate
  pip install python-fasthtml pywebview pyobjc py2app

用法：python build_macos_py2app.py [--entry main.py] [--app-name MyApp] [--icon assets/icon.icns]
产物：dist/<AppName>.app
校验（macOS）：./dist/<AppName>.app/Contents/MacOS/<AppName>   # demo 自跑断言 ALL_PASS
签名/公证（macOS，分发必需）：
  codesign --deep --force --options runtime --sign "Developer ID Application: <name>" dist/<AppName>.app
  xcrun notarytool submit <zip> --keychain-profile <profile> --wait && xcrun stapler staple dist/<AppName>.app
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entry", default="main.py")
    ap.add_argument("--app-name", default="MyApp")
    ap.add_argument("--icon", default=None, help="可选 .icns 图标路径")
    args = ap.parse_args()

    if sys.platform != "darwin":
        print(f"[FATAL] 本脚本仅限 macOS 执行（当前 {sys.platform}）。"
              "py2app 不支持交叉编译。请在 macOS 上运行。")
        return 1

    entry = HERE / args.entry
    if not entry.exists():
        print(f"[FATAL] 入口文件不存在: {entry}")
        return 1

    from setuptools import setup

    data_files: list = []  # FastHTML SSR 无静态资源；如有 assets/ 再加 ("assets", ["assets/x.png"])
    options = {
        "argv_emulation": False,      # pywebview 官方模板取 False；True 会与 Cocoa 事件循环冲突
        "strip": True,
        "packages": ["fasthtml", "webview", "uvicorn", "starlette"],  # 动态 import 重的包整包收集
        "includes": ["webview.platforms.cocoa"],
        "plist": {
            "CFBundleName": args.app_name,
            "CFBundleIdentifier": f"com.example.{args.app_name.lower()}",
            "NSHighResolutionCapable": True,
            # 本地回环服务器（uvicorn 127.0.0.1）不需要额外网络权限声明
        },
    }
    if args.icon:
        options["iconfile"] = str(Path(args.icon).resolve())

    setup(
        app=[str(entry)],
        name=args.app_name,
        data_files=data_files,
        options={"py2app": options},
        setup_requires=["py2app"],
        script_args=["py2app"],
    )
    print("BUILD_RESULT=OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
