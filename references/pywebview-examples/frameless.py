# =============================================================================
# pywebview-examples / frameless.py
# 来源: user_skills/pywebview/scripts/frameless.py  (pywebview 官方示例, v6.2.1)
# 分类: B 已覆盖于 06（本文件为上游参考）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 已覆盖于 06-pywebview-shell.md；此处保留上游原版供比对。
# =============================================================================

"""Create a frameless window. The window can be moved around by dragging any point."""

import webview

if __name__ == '__main__':
    # Create a resizable webview window with minimum size constraints
    webview.create_window(
        'Frameless window', 'http://pywebview.flowrl.com/hello', frameless=True, easy_drag=True
    )
    webview.start()
