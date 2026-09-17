# =============================================================================
# pywebview-examples / change_url.py
# 来源: user_skills/pywebview/scripts/change_url.py  (pywebview 官方示例, v6.2.1)
# 分类: B 已覆盖于 06（本文件为上游参考）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 已覆盖于 06-pywebview-shell.md；此处保留上游原版供比对。
# =============================================================================

"""
Change URL ten seconds after the first URL is loaded.
"""

import time

import webview


def change_url(window):
    # wait a few seconds before changing url:
    time.sleep(10)

    # change url:
    window.load_url('https://pywebview.flowrl.com/hello')


if __name__ == '__main__':
    window = webview.create_window('URL Change Example', 'http://www.google.com')
    webview.start(change_url, window)
