"""
macOS py2app setup 模板（经典 `python setup.py py2app` 用法）。

⚠ 仅 macOS 可执行（py2app 是 macOS 专属打包器）。
Fasthtml-desktop 同时提供可运行版 `scripts/build_macos_py2app.py`（支持 --app-name/--entry/--icon）。
关键适配（相对官方原版）：
  - FastHTML 是纯 SSR，无静态资源目录 → DATA_FILES = []
  - packages 含 fasthtml（动态 import 重，等价于 PyInstaller --collect-submodules fasthtml）
  - includes=['webview.platforms.cocoa']（cocoa 后端）
  - argv_emulation=False（True 会与 Cocoa 事件循环冲突）
来源：pywebview 官方 py2app_setup.py；完整说明见 references/11-cross-platform.md §4。
"""
import os

from setuptools import setup


def tree(src):
    return [
        (root, list(map(lambda f: os.path.join(root, f), files)))
        for (root, dirs, files) in os.walk(os.path.normpath(src))
    ]


ENTRY_POINT = ['main.py']  # FastHTML 入口壳（与 src/main.py 同构）
DATA_FILES = tree('DATA_FILES_DIR') + tree('DATA_FILES_DIR2')
OPTIONS = {
    'argv_emulation': False,
    'strip': True,
    # 'iconfile': 'icon.icns',  # 取消注释以包含图标
    'includes': ['WebKit', 'Foundation', 'webview', 'webview.platforms.cocoa'],
    'packages': ['fasthtml', 'uvicorn', 'starlette'],
}

setup(
    app=ENTRY_POINT,
    name='MyApp',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
