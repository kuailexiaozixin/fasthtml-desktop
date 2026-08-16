# =============================================================================
# pywebview-examples / settings.py
# 来源: user_skills/pywebview/scripts/settings.py  (pywebview 官方示例, v6.2.1)
# 分类: B 已覆盖于 06（本文件为上游参考）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 已覆盖于 06-pywebview-shell.md；此处保留上游原版供比对。
# =============================================================================

"""
Use application flags to modify default behaviour of pywebview
"""

import webview

html = """
  <html>
    <head></head>
    <body>
      <h2></h2>
      <p><a href='https://pywebview.flowrl.com' target='_blank'>target='_blank' link</a> will be opened in the current window.</p>
    </body>
  </html>
"""


if __name__ == '__main__':
    print(webview.settings)
    webview.settings['OPEN_EXTERNAL_LINKS_IN_BROWSER'] = False
    webview.settings['OPEN_DEVTOOLS_IN_DEBUG'] = False

    window = webview.create_window('Application flags', html=html)
    webview.start()
