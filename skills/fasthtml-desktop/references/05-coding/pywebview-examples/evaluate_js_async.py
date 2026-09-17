# =============================================================================
# pywebview-examples / evaluate_js_async.py
# 来源: user_skills/pywebview/scripts/evaluate_js_async.py  (pywebview 官方示例, v6.2.1)
# 分类: B 已覆盖于 06（本文件为上游参考）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 已覆盖于 06-pywebview-shell.md；此处保留上游原版供比对。
# =============================================================================

"""
Run asynchronous Javascript code and invoke a callback.
"""

import webview


def callback(result):
    print(result)


def evaluate_js_async(window):
    window.evaluate_js(
        """
        new Promise((resolve, reject) => {
            setTimeout(() => {
                resolve('Whaddup!');
            }, 300);
        });
        """,
        callback,
    )


if __name__ == '__main__':
    window = webview.create_window('Run async Javascript', html='<html><body></body></html>')
    webview.start(evaluate_js_async, window)
