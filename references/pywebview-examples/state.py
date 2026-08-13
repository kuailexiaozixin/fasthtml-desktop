# =============================================================================
# pywebview-examples / state.py
# 来源: user_skills/pywebview/scripts/state.py  (pywebview 官方示例, v6.2.1)
# 分类: B 已覆盖于 06（本文件为上游参考）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 已覆盖于 06-pywebview-shell.md；此处保留上游原版供比对。
# =============================================================================

"""
Demonstrate usage of the state object to share state between Python and JavaScript.
"""

import webview

html = """
<!DOCTYPE html>
<html>
    <head>
       <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
    </head>

    <script>
        window.addEventListener('pywebviewready', () => {
            window.pywebview.state.addEventListener('change', event => {
                console.log('Counter value changed:', event)
                document.getElementById('counter').innerText = pywebview.state.counter
            })
        })

        function increaseCounter() {
            pywebview.state.counter++
            document.getElementById('counter').innerText = pywebview.state.counter
        }
    </script>

    <body>
        <h1>State</h1>

        <p>Counter value: <span id="counter">0</span></p>

        <button onclick="increaseCounter()">Increase counter from JS</button>
        <button onclick="pywebview.api.decrease_counter()">Decrease counter from Python</button>
    </body>
</html>
"""


def on_counter_change(type, key, value):
    print(f'Event {type} for {key} value : {value}')


def decrease_counter():
    window.state.counter -= 1


def on_loaded(window):
    window.expose(decrease_counter)
    window.state += on_counter_change


if __name__ == '__main__':
    global window
    window = webview.create_window('State example', html=html)
    window.state.counter = 0
    window.events.loaded += on_loaded
    webview.start(debug=True)
