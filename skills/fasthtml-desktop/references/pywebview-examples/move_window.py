# =============================================================================
# pywebview-examples / move_window.py
# 来源: user_skills/pywebview/scripts/move_window.py  (pywebview 官方示例, v6.2.1)
# 分类: B 已覆盖于 06（本文件为上游参考）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 已覆盖于 06-pywebview-shell.md；此处保留上游原版供比对。
# =============================================================================

"""Set window coordinates and move window after its creation."""

from time import sleep

import webview


def move(window):
    print(f'Window coordinates are ({window.x}, {window.y})')
    print(f'Window dimensions are ({window.width}x{window.height})')

    # Get the primary screen to calculate relative position
    screens = webview.screens
    if screens:
        primary_screen = screens[0]
        print(f'Primary screen: {primary_screen.width}x{primary_screen.height}')

        # Move to bottom-right area of screen (with some padding)
        new_x = primary_screen.width - window.width - 100
        new_y = primary_screen.height - window.height - 100
    else:
        # Fallback to absolute coordinates
        new_x, new_y = 500, 500

    sleep(2)
    window.move(new_x, new_y)
    print(f'Moving window to ({new_x}, {new_y})...')
    sleep(1)
    print(f'Window coordinates are now ({window.x}, {window.y})')


if __name__ == '__main__':
    window = webview.create_window('Move window example', html='<h1>Move window</h1>', x=300, y=300)
    webview.start(move, window)
