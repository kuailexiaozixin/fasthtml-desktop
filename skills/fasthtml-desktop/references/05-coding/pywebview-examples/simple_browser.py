# =============================================================================
# pywebview-examples / simple_browser.py
# 来源: user_skills/pywebview/scripts/simple_browser.py  (pywebview 官方示例, v6.2.1)
# 分类: 最小窗口示例
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: create_window + start 最小闭环。
# =============================================================================

"""The most basic example of creating a webview window."""

import webview

if __name__ == '__main__':
    # Create a standard webview window
    window = webview.create_window('Simple browser', 'https://pywebview.flowrl.com/hello')
    webview.start()
