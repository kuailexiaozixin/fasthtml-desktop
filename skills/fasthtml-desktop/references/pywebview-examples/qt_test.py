"""
Qt 后端示例（cross-platform 回退链）。

`gui='qt'` 依赖 `qtpy`（需 `pip install qtpy` + 任一 Qt 绑定，如 PyQt6/PySide6）。
通常 gtk 是 Linux 首选；指定 qt 可跨平台统一外观。打包 hidden-import 见 11-cross-platform.md §3。
来源：pywebview 官方 qt_test.py；适配注释见 references/06-pywebview-shell.md。
"""
import webview

if __name__ == '__main__':
    webview.create_window('Qt Example', 'http://127.0.0.1:5001')
    webview.start(gui='qt')
