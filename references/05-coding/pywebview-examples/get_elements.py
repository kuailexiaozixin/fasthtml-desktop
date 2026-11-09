# =============================================================================
# pywebview-examples / get_elements.py
# 来源: user_skills/pywebview/scripts/get_elements.py  (pywebview 官方示例, v6.2.1)
# 分类: A 类 DOM 已实证
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 注意 API 是 window.dom.get_elements(selector)（返回列表）；不存在 window.get_elements。
# =============================================================================

"""Get DOM elements using selectors."""

import webview


def get_elements(window):
    heading = window.dom.get_elements('#heading')
    content = window.dom.get_elements('.content')
    print(f'Heading:\n {heading[0].node["outerHTML"]}')
    print(f'Content 1:\n {content[0].node["outerHTML"]}')
    print(f'Content 2:\n {content[1].node["outerHTML"]}')


if __name__ == '__main__':
    html = """
      <html>
        <body>
          <h1 id="heading">Heading</h1>
          <div class="content">Content 1</div>
          <div class="content">Content 2</div>
        </body>
      </html>
    """
    window = webview.create_window('Get elements example', html=html)
    webview.start(get_elements, window)
