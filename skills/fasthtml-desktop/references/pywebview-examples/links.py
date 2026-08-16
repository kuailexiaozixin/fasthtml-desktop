# =============================================================================
# pywebview-examples / links.py
# 来源: user_skills/pywebview/scripts/links.py  (pywebview 官方示例, v6.2.1)
# 分类: 外链行为
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: target='_blank' 走外部浏览器；配合 settings['OPEN_EXTERNAL_LINKS_IN_BROWSER']。
# =============================================================================

"""
Demonstrate a difference between different link types
"""

import webview

html = """
  <html>
    <head></head>
    <body>
      <h2>Links</h2>

      <p><a href='https://pywebview.flowrl.com'>Regular links</a> are opened in the application window.</p>
      <p><a href='https://pywebview.flowrl.com' target='_blank'>target='_blank' links</a> are opened in an external browser.</p>

    </body>
  </html>
"""


if __name__ == '__main__':
    window = webview.create_window('Link types', html=html)
    webview.start()
