# =============================================================================
# pywebview-examples / remote_debugging.py
# 来源: user_skills/pywebview/scripts/remote_debugging.py  (pywebview 官方示例, v6.2.1)
# 分类: settings 远程调试
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: webview.settings['REMOTE_DEBUGGING_PORT']，Edge WebView2 生效。
# =============================================================================

"""
Enable remote debugging when using `edgechromium`.
This can be used to write tests for the application using Playwright.
See [https://playwright.dev/docs/webview2](https://playwright.dev/docs/webview2) for how to configure it.
"""

import webview

if __name__ == '__main__':
    webview.settings['REMOTE_DEBUGGING_PORT'] = 9222

    window = webview.create_window('Webview', 'https://pywebview.flowrl.com/hello')
    webview.start()
