# =============================================================================
# pywebview-examples / localization.py
# 来源: user_skills/pywebview/scripts/localization.py  (pywebview 官方示例, v6.2.1)
# 分类: N6 已实证
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: start(localization=...) 6.2.1 实证；Windows 生效键为 windows.* 与 global.*，cocoa.*/linux.* 键在 Windows 无效但无害。
# =============================================================================

"""Localize system text string used by pywebview. For a full list of used string, refer to the `webview/localization.py` file."""

import webview

if __name__ == '__main__':
    localization = {
        'global.saveFile': 'Сохранить файл',
        'cocoa.menu.about': 'О программе',
        'cocoa.menu.services': 'Cлужбы',
        'cocoa.menu.view': 'Вид',
        'cocoa.menu.hide': 'Скрыть',
        'cocoa.menu.hideOthers': 'Скрыть остальные',
        'cocoa.menu.showAll': 'Показать все',
        'cocoa.menu.quit': 'Завершить',
        'cocoa.menu.fullscreen': 'Перейти ',
        'windows.fileFilter.allFiles': 'Все файлы',
        'windows.fileFilter.otherFiles': 'Остальлные файльы',
        'linux.openFile': 'Открыть файл',
        'linux.openFiles': 'Открыть файлы',
        'linux.openFolder': 'Открыть папку',
    }

    window_localization_override = {
        'global.saveFile': 'Save file',
    }

    webview.create_window(
        'Localization Example',
        'https://pywebview.flowrl.com/hello',
        localization=window_localization_override,
    )
    webview.start(localization=localization)
