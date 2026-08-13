# =============================================================================
# pywebview-examples / cookies.py
# 来源: user_skills/pywebview/scripts/cookies.py  (pywebview 官方示例, v6.2.1)
# 分类: B 已覆盖于 06（本文件为上游参考）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 已覆盖于 06-pywebview-shell.md；此处保留上游原版供比对。
# =============================================================================

"""A cookies and local storage example."""

import webview


def read_cookies(window):
    cookies = window.get_cookies()
    for c in cookies:
        print(c.output())


class Api:
    def clearCookies(self):
        window.clear_cookies()


if __name__ == '__main__':
    window = webview.create_window('Cookie example', 'assets/cookies.html', js_api=Api())

    # We need to explicitly set a http port to persist cookies between sessions
    webview.start(read_cookies, window, private_mode=False, http_server=True, http_port=13377)
