# =============================================================================
# pywebview-examples / http_server.py
# 来源: user_skills/pywebview/scripts/http_server.py  (pywebview 官方示例, v6.2.1)
# 分类: 内置 HTTP server
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: 相对路径入口自动起内置服务；fasthtml-desktop 常规路线仍是 uvicorn，此为补充认知。
# =============================================================================

"""A built-in HTTP server example."""

import webview

if __name__ == '__main__':
    webview.create_window('My first HTML5 application', 'assets/index.html')
    # HTTP server is started automatically for local relative paths
    webview.start(ssl=True)
