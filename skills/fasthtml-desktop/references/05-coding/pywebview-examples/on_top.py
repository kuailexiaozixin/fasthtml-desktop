# =============================================================================
# pywebview-examples / on_top.py
# 来源: user_skills/pywebview/scripts/on_top.py  (pywebview 官方示例, v6.2.1)
# 分类: B 已覆盖于 06（本文件为上游参考）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 已覆盖于 06-pywebview-shell.md；此处保留上游原版供比对。
# =============================================================================

"""Create a window that stays on top of other windows."""

import time

import webview


def deactivate(window):
    # window starts as on top of and reverts back to normal after 20 seconds
    time.sleep(20)
    window.on_top = False
    window.load_html('<h1>This window is no longer on top of other windows</h1>')


if __name__ == '__main__':
    # Create webview window that stays on top of, all other windows
    window = webview.create_window(
        'Topmost window', html='<h1>This window is on top of other windows</h1>', on_top=True
    )
    webview.start(deactivate, window)
