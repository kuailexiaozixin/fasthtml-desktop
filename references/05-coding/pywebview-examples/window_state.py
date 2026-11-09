# =============================================================================
# pywebview-examples / window_state.py
# 来源: user_skills/pywebview/scripts/window_state.py  (pywebview 官方示例, v6.2.1)
# 分类: B 已覆盖于 06（本文件为上游参考）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 已覆盖于 06-pywebview-shell.md；此处保留上游原版供比对。
# =============================================================================

"""Minimize, restore and maximize window programmatically"""

from time import sleep

import webview


def minimize(window):
    print('Window is started minimized')

    sleep(5)
    print('Restoring window')
    window.restore()

    sleep(5)
    print('Maximizing window')
    window.maximize()

    sleep(5)
    print('Minimizing window')
    window.minimize()


if __name__ == '__main__':
    window = webview.create_window(
        'Minimize window example', html='<h1>Minimize window</h1>', minimized=True
    )
    webview.start(minimize, window)
