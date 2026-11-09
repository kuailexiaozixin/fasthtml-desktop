# =============================================================================
# pywebview-examples / expose.py
# 来源: user_skills/pywebview/scripts/expose.py  (pywebview 官方示例, v6.2.1)
# 分类: B 已覆盖于 06（本文件为上游参考）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 已覆盖于 06-pywebview-shell.md；此处保留上游原版供比对。
# =============================================================================

"""Exposing Python functions to the Javascript domain."""

import webview


def lol():
    print('LOL')


def wtf():
    print('WTF')


def echo(arg1, arg2, arg3):
    print(arg1)
    print(arg2)
    print(arg3)


def expose(window):
    window.expose(echo)  # expose a function during the runtime

    window.evaluate_js('pywebview.api.lol()')
    window.evaluate_js('pywebview.api.wtf()')
    window.evaluate_js('pywebview.api.echo(1, 2, 3)')


if __name__ == '__main__':
    window = webview.create_window(
        'JS Expose Example',
        html='<html><head></head><body><h1>JS API function Expose</body></html>',
    )
    window.expose(lol, wtf)  # expose functions beforehand

    webview.start(expose, window)
