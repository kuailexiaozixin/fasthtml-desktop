# =============================================================================
# pywebview-examples / downloads.py
# 来源: user_skills/pywebview/scripts/downloads.py  (pywebview 官方示例, v6.2.1)
# 分类: A 高价值缺口（06 当前缺失/写错，已修正）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: P0修正：下载由 webview.settings['ALLOW_DOWNLOADS']=True 开启（06 已删伪造的 events.download），配合 create_file_dialog 选择保存路径。
# =============================================================================

"""Enable file downloads"""

import webview

if __name__ == '__main__':
    # Create a standard webview window
    webview.settings['ALLOW_DOWNLOADS'] = True
    window = webview.create_window('Simple browser', 'https://pywebview.flowrl.com/download')
    webview.start()
