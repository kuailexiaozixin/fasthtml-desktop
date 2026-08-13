"""
CEF 后端示例（cross-platform，但受 Python 版本约束）。

⚠ P1 谨慎项：cefpython3 仅支持到 Python 3.9（≥3.10 导入即报
"Python version not supported"）。现代 Python 下**不能**作为跨平台一致后端。
仅在 Python 3.9 环境 + `pip install cefpython3` 后可用，且需在目标平台实跑验证。

Fasthtml-desktop 默认推荐各平台官方后端（Win=WebView2 / mac=cocoa / Linux=gtk），无需 CEF。
来源：pywebview 官方 cef.py；适配注释见 references/11-cross-platform.md §6。
"""
import webview

# 向 CEF 传入自定义设置
from webview.platforms.cef import browser_settings, settings

settings.update({'persist_session_cookies': True})
browser_settings.update({'dom_paste_disabled': False})

if __name__ == '__main__':
    webview.create_window('CEF browser', 'http://127.0.0.1:5001')
    webview.start(gui='cef')
