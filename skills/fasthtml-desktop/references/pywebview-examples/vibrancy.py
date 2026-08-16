"""
macOS vibrancy 示例（仅 macOS cocoa 后端有效）。

⚠ 实测 6.2.1：vibrancy 仅在 macOS cocoa 后端实现，Windows(LT)Edge/winforms 与 Linux gtk 源码 0 命中，
设 True 无任何视觉效果，请勿在跨平台应用里依赖它。
来源：pywebview 官方 vibrancy.py；适配注释见 references/06-pywebview-shell.md。
"""
import webview


def load_css(window):
    window.load_css('body { background: transparent !important; }')


if __name__ == '__main__':
    window = webview.create_window(
        'Vibrancy example', 'http://127.0.0.1:5001', transparent=True, vibrancy=True
    )
    webview.start(load_css, window)
