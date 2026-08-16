# =============================================================================
# pywebview-examples / screens.py
# 来源: user_skills/pywebview/scripts/screens.py  (pywebview 官方示例, v6.2.1)
# 分类: N4 已实证
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: webview.screens 返回屏幕列表（Proxy），s.width/s.height 可用。
# =============================================================================

"""Get available display information using `webview.screens`"""

import webview

if __name__ == '__main__':
    screens = webview.screens
    print('Available screens:')

    for i, screen in enumerate(screens):
        print(f'\nScreen {i + 1}:')
        print(f'  Position: ({screen.x}, {screen.y})')
        print(f'  Size: {screen.width}x{screen.height}')
        print(f'  Scale: {screen.scale}x')
        print(f'  DPI: {screen.dpi}')
        print(f'  Physical Size: {screen.physical_width}x{screen.physical_height}')

        webview.create_window('', html=f'placed on the monitor {i + 1}', screen=screen)

    webview.start()
