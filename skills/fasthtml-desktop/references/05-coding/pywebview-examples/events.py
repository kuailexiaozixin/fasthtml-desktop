# =============================================================================
# pywebview-examples / events.py
# 来源: user_skills/pywebview/scripts/events.py  (pywebview 官方示例, v6.2.1)
# 分类: B 已覆盖于 06（本文件为上游参考）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 已覆盖于 06-pywebview-shell.md；此处保留上游原版供比对。
# =============================================================================

"""Subscribe and unsubscribe to pywebview events."""

import webview


def on_before_show(window):
    print('Native window object', window.native)


def on_closed():
    print('pywebview window is closed')


def on_closing():
    print('pywebview window is closing')


def on_initialized(renderer):
    # return False to cancel initialization
    print(f'GUI is initialized with renderer: {renderer}')


def on_shown():
    print('pywebview window shown')


def on_minimized():
    print('pywebview window minimized')


def on_restored():
    print('pywebview window restored')


def on_maximized():
    print('pywebview window maximized')


def on_resized(width, height):
    print(f'pywebview window is resized. new dimensions are {width} x {height}')


# you can supply optional window argument to access the window object event was triggered on
def on_loaded(window):
    print('DOM is ready')

    # unsubscribe event listener
    window.events.loaded -= on_loaded
    window.load_url('https://pywebview.flowrl.com/hello')


def on_moved(x, y):
    print(f'pywebview window is moved. new coordinates are x: {x}, y: {y}')


if __name__ == '__main__':
    window = webview.create_window(
        'Simple browser', 'https://pywebview.flowrl.com/', confirm_close=True
    )

    window.events.closed += on_closed
    window.events.closing += on_closing
    window.events.before_show += on_before_show
    window.events.initialized += on_initialized
    window.events.shown += on_shown
    window.events.loaded += on_loaded
    window.events.minimized += on_minimized
    window.events.maximized += on_maximized
    window.events.restored += on_restored
    window.events.resized += on_resized
    window.events.moved += on_moved

    webview.start()
