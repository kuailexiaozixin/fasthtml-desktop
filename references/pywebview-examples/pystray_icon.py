# =============================================================================
# pywebview-examples / pystray_icon.py
# 来源: user_skills/pywebview/scripts/pystray_icon.py  (pywebview 官方示例, v6.2.1)
# 分类: A 高价值缺口（06 当前缺失/写错，已修正）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 系统托盘正确实现：需 pip install pystray Pillow，并用 multiprocessing 起独立进程（06 已修正删除了伪造的 webview.TrayIcon/tray=True）。
# =============================================================================

"""
Run pywebview alongside with pystray to display a system tray icon.
"""

import multiprocessing
import sys

from PIL import Image
from pystray import Icon, Menu, MenuItem

import webview

if sys.platform == 'darwin':
    ctx = multiprocessing.get_context('spawn')
    Process = ctx.Process
    Queue = ctx.Queue
else:
    Process = multiprocessing.Process
    Queue = multiprocessing.Queue


webview_process = None


def run_webview():
    webview.create_window('Webview', 'https://pywebview.flowrl.com/hello')
    webview.start()


if __name__ == '__main__':

    def start_webview_process():
        global webview_process
        webview_process = Process(target=run_webview)
        webview_process.start()

    def on_open(icon, item):
        global webview_process
        if not webview_process.is_alive():
            start_webview_process()

    def on_exit(icon, item):
        icon.stop()

    start_webview_process()

    image = Image.open('assets/logo.png')
    menu = Menu(MenuItem('Open', on_open), MenuItem('Exit', on_exit))
    icon = Icon('Pystray', image, menu=menu)
    icon.run()

    webview_process.terminate()
