# =============================================================================
# pywebview-examples / headers.py
# 来源: user_skills/pywebview/scripts/headers.py  (pywebview 官方示例, v6.2.1)
# 分类: 请求级事件（#565 翻案实证存在）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: window.events.request_sent / response_received 是 Window.__init__ 动态挂载的实例属性，edgechromium 后端有完整实现；类级 hasattr 检查会误判不存在。原文用 bottle 演示。
# =============================================================================

"""Subscribe and unsubscribe to pywebview events."""

from bottle import Bottle, request

import webview


def on_request(window, request):
    print('Request sent: ' + request.url)
    request.headers['pywebview'] = 'header'


def on_response(window, response):
    print('Response received: ' + response.url)


app = Bottle()


@app.route('/')
def display_headers():
    headers = dict(request.headers)
    return '<br>'.join(f'{key}: {value}' for key, value in headers.items())


if __name__ == '__main__':
    window = webview.create_window('Headers', app)

    window.events.request_sent += on_request
    window.events.response_received += on_response

    webview.start(debug=True)
