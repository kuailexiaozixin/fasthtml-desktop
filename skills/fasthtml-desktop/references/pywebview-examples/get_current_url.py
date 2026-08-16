# =============================================================================
# pywebview-examples / get_current_url.py
# 来源: user_skills/pywebview/scripts/get_current_url.py  (pywebview 官方示例, v6.2.1)
# 分类: N2 已实证（gap-demo 打包态 ALL_PASS）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: window.get_current_url() 返回当前 URL 字符串，已在 6.2.1 实证。
# =============================================================================

"""Print current URL after page is loaded."""

import webview


def get_current_url(window):
    print(window.get_current_url())


if __name__ == '__main__':
    window = webview.create_window('Get current URL', 'https://pywebview.flowrl.com/hello')
    webview.start(get_current_url, window)
