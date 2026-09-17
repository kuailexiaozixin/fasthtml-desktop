# =============================================================================
# pywebview-examples / hide_window.py
# 来源: user_skills/pywebview/scripts/hide_window.py  (pywebview 官方示例, v6.2.1)
# 分类: B 已覆盖于 06（本文件为上游参考）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 已覆盖于 06-pywebview-shell.md；此处保留上游原版供比对。
# =============================================================================

"""Programmatically hide and show window."""

import time

import webview


def hide_show(window):
    print('Window is started hidden')

    time.sleep(5)
    print('Showing window')
    window.show()

    time.sleep(5)
    print('Hiding window')
    window.hide()

    time.sleep(5)
    print('And showing again')
    window.show()


if __name__ == '__main__':
    window = webview.create_window(
        'Hide / show window', 'https://pywebview.flowrl.com/hello', hidden=True
    )
    webview.start(hide_show, window)
