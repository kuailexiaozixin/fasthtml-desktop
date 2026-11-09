# =============================================================================
# pywebview-examples / user_agent.py
# 来源: user_skills/pywebview/scripts/user_agent.py  (pywebview 官方示例, v6.2.1)
# 分类: N5 已实证
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: ⚠ user_agent 是 webview.start() 的参数，不是 create_window 参数（签名实证）。
# =============================================================================

"""
Change the user-agent of a window.
"""

import webview

if __name__ == '__main__':
    webview.create_window('User Agent Test', 'https://pywebview.flowrl.com/hello')
    webview.start(user_agent='Custom user agent')
