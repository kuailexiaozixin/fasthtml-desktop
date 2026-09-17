# =============================================================================
# pywebview-examples / transparent.py
# 来源: user_skills/pywebview/scripts/transparent.py  (pywebview 官方示例, v6.2.1)
# 分类: 透明无边框窗口（Windows 可用）
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: transparent=True + frameless；与 vibrancy 无关（vibrancy 仅 macOS，勿混淆）。
# =============================================================================

"""Create a transparent frameless window with custom chrome."""

import webview

html = """
<!doctype html>
<html lang="en">
	<head>
		<meta charset="utf-8">
        <title>Test app</title>
        <style>
            .frame {
                border-radius: 5px 5px 0 0;
                position: fixed;
                box-sizing: border-box;
                width: 90%;
                height: 90%;
                background-color: #0055e4;
                box-shadow: inset 1px 1px 1px 0px rgba(255,255,255,.25), inset -1px -1px 1px 0px rgba(0,0,0,.25), inset 0px 2px 4px -2px rgba(255,255,255,1);
            }
            .frame>tbody>tr>td {
                vertical-align: top;
            }
            .header {
                box-sizing: border-box;
                padding: 5px;
                height: 20px;
                font-weight: bold;
                color: white;
            }
            .header>img {
                height: 16px;
                transform: translateY(3px);
            }
            .content {
                box-sizing: border-box;
                background-color: #f0f0e8;
                margin: 0 5px 5px 5px ;
            }
            .bodypanel {
                background-color: #f0f0e8;
                height: 100%;
                box-shadow: 1px 1px 1px 0px rgba(255,255,255,.25), -1px -1px 1px 0px rgba(0,0,0,.25), inset 0px 0px 3px -2px rgba(0,0,0,1);
                padding: 5px;
            }
        </style>
	</head>
	<body>
        <table class="frame">
            <tbody>
                <tr>
                    <td class="header">
                        <img src="folder.png"/>
                        Danger!
                    </td>
                </tr>
                <tr>
                    <td class="body">
                        <div class="bodypanel">
                            <b>Alert!</b><br>
                            Lorem ipsum dolor sit amet, consectetur adipiscing elit
                            <button>Button</button>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
	</body>
</html>
"""


if __name__ == '__main__':
    # Create a transparent webview window
    webview.create_window(
        'Transparent window', html=html, transparent=True, frameless=True
    )  # , hidden=True)
    webview.start()
