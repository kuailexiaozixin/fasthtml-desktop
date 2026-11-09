# =============================================================================
# pywebview-examples / run_js.py
# 来源: user_skills/pywebview/scripts/run_js.py  (pywebview 官方示例, v6.2.1)
# 分类: N3 已实证
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: window.run_js(script) 返回 JS 求值结果（gap-demo 断言 420）。
# =============================================================================

"""Run Javascript code from Python."""

import webview


def run_js(window):
    result = window.run_js(
        r"""
        var h1 = document.createElement('h1')
        var text = document.createTextNode('Hello pywebview')
        h1.appendChild(text)
        document.body.appendChild(h1)

        function test() {
            return 420
        }

        test()
        """
    )

    print(result)


if __name__ == '__main__':
    window = webview.create_window('Run JavaScript', html='<html><body></body></html>')
    webview.start(run_js, window)
