# =============================================================================
# pywebview-examples / drag_drop.py
# 来源: user_skills/pywebview/scripts/drag_drop.py  (pywebview 官方示例, v6.2.1)
# 分类: A 高价值缺口（06 当前缺失/写错，已修正）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: A2修正：拖放读取 file 用 e['dataTransfer']['files'][0]['pywebviewFullPath']（06 已修正 domTransfer->dataTransfer）；事件用 webview.dom.DOMEventHandler 绑定。
# =============================================================================

"""This example demonstrates how to expose Python functions to the Javascript domain."""

import webview
from webview.dom import DOMEventHandler


def on_drag(e):
    pass


def on_drop(e):
    files = e['dataTransfer']['files']
    if len(files) == 0:
        return

    print(f'Event: {e["type"]}. Dropped files:')

    for file in files:
        print(file.get('pywebviewFullPath'))


def bind(window):
    window.dom.document.events.dragenter += DOMEventHandler(on_drag, True, True)
    window.dom.document.events.dragstart += DOMEventHandler(on_drag, True, True)
    window.dom.document.events.dragover += DOMEventHandler(on_drag, True, True, debounce=500)
    window.dom.document.events.drop += DOMEventHandler(on_drop, True, True)


if __name__ == '__main__':
    window = webview.create_window(
        'Drag & drop example',
        html="""
            <html>
                <body style="height: 100vh;"->
                    <h1>Drag files here</h1>
                </body>
            </html>
        """,
    )
    webview.start(bind, window)
