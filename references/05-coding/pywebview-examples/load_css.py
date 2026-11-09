# =============================================================================
# pywebview-examples / load_css.py
# 来源: user_skills/pywebview/scripts/load_css.py  (pywebview 官方示例, v6.2.1)
# 分类: C2 已实证
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: window.load_css() 注入样式，gap-demo 以 getComputedStyle 断言生效。
# =============================================================================

"""
Loading custom CSS in a webview window
"""

import webview


def load_css(window):
    window.load_css('body { background: red !important; }')


if __name__ == '__main__':
    window = webview.create_window('Load CSS Example', 'https://pywebview.flowrl.com/hello')
    webview.start(load_css, window)
