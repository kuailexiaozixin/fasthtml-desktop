# =============================================================================
# pywebview-examples / drag_region.py
# 来源: user_skills/pywebview/scripts/drag_region.py  (pywebview 官方示例, v6.2.1)
# 分类: B 类拖拽区已实证
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: frameless + .pywebview-drag-region + settings['DRAG_REGION_SELECTOR']（新 API）。
# =============================================================================

"""Demonstrates the use of dynamic draggable regions in a frameless window using pywebview."""

import webview

html = """
<!DOCTYPE html>
<html>
<head>
    <style type="text/css">
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }

        .header {
            background: #333;
            color: white;
            padding: 10px;
            text-align: center;
            margin-bottom: 20px;
        }

        .pywebview-drag-region {
            width: 120px;
            height: 40px;
            background: orange;
            border: 2px solid #ff8c00;
            border-radius: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: move;
            margin: 10px;
            padding: 5px;
            font-weight: bold;
            color: white;
        }

        .content {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-bottom: 20px;
        }

        .controls {
            text-align: center;
            padding: 20px;
        }

        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }

        button:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <div class="content">
        <div class="pywebview-drag-region">Drag me!</div>
    </div>

    <div class="controls">
        <button onclick="addDragRegion()">Add New Drag Region</button>
        <p>Click the button to add more draggable regions, or drag the orange areas to move the window.</p>
    </div>

    <script>
        function addDragRegion() {
            const newDiv = document.createElement('div');
            newDiv.className = 'pywebview-drag-region';
            newDiv.textContent = 'New drag region!';

            const content = document.querySelector('.content');
            content.appendChild(newDiv);
        }
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    window = webview.create_window(
        'API example',
        html=html,
        frameless=True,
        easy_drag=False,
    )
    webview.start()
