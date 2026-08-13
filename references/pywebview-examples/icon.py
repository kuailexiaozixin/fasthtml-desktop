"""
运行时设置窗口图标（仅 GTK / QT 后端生效）。

⚠ `webview.start(icon=...)` 的运行时图标**仅 GTK 与 QT 后端**支持；
Edge(cocoa) 图标在打包阶段设置（Windows 用 --icon .ico，macOS 用 py2app iconfile），
运行时设 icon 参数无效。来源：pywebview 官方 icon.py；适配注释见 references/11-cross-platform.md。
"""
import webview

if __name__ == '__main__':
    window = webview.create_window('Set window icon', 'http://127.0.0.1:5001')
    webview.start(icon='../assets/logo.png')
