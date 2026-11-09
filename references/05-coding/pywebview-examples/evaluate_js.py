# =============================================================================
# pywebview-examples / evaluate_js.py
# 来源: user_skills/pywebview/scripts/evaluate_js.py  (pywebview 官方示例, v6.2.1)
# 分类: B 已覆盖于 06（本文件为上游参考）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 已覆盖于 06-pywebview-shell.md；此处保留上游原版供比对。
# =============================================================================

"""Run Javascript code from Python."""

import webview
from webview.errors import JavascriptException


def evaluate_js(window):
    result = window.evaluate_js(
        r"""
        var h1 = document.createElement('h1')
        var text = document.createTextNode('Hello pywebview')
        h1.appendChild(text)
        document.body.appendChild(h1)

        document.body.style.backgroundColor = '#212121'
        document.body.style.color = '#f2f2f2'

        // Return user agent
        'User agent:\n' + navigator.userAgent;
        """
    )

    print(result)

    try:
        result = window.evaluate_js('syntaxerror#$%#$')
    except JavascriptException as e:
        print('Javascript exception occured: ', e)


if __name__ == '__main__':
    window = webview.create_window('Evaluate JavaScript', html='<html><body></body></html>')
    webview.start(evaluate_js, window)
