# =============================================================================
# pywebview-examples / multiprocess.py
# 来源: user_skills/pywebview/scripts/multiprocess.py  (pywebview 官方示例, v6.2.1)
# 分类: 多进程运行 pywebview
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: multiprocessing 场景主线程不阻塞；Windows 注意 freeze_support。
# =============================================================================

"""Example of running pywebview in a separate process with shared state. Main thread is not blocked in this example."""

import multiprocessing
import threading
import time

import webview

html = """
<!DOCTYPE html>
<html>
    <head>
       <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css">
    </head>

    <script>
        window.addEventListener('pywebviewready', () => {
            window.pywebview.state.addEventListener('change', event => {
                console.log('State changed:', event)
                document.getElementById('counter').innerText = pywebview.state.counter
                document.getElementById('message').innerText = pywebview.state.message
            })
        })
    </script>

    <body>
        <h1>Multiprocess State Example</h1>

        <p>Counter value: <span id="counter">0</span></p>
        <p>Message from main process: <span id="message">Waiting...</span></p>
    </body>
</html>
"""


def run_webview(shared_dict):
    """Function to run webview in a separate process with shared state."""

    def on_counter_change(type, key, value):
        print(f'Webview process - {key}: {value}')

    def sync_from_shared_state():
        """Sync webview state from shared dictionary."""
        try:
            # Check if shared state has changed and update webview state
            if window.state.counter != shared_dict.get('counter', 0):
                window.state.counter = shared_dict['counter']
            if window.state.message != shared_dict.get('message', 'Waiting...'):
                window.state.message = shared_dict['message']
        except Exception as e:
            print(f'Error syncing state: {e}')

    def on_loaded(window):
        window.state += on_counter_change
        # Sync initial state from shared dictionary
        window.state.counter = shared_dict.get('counter', 0)
        window.state.message = shared_dict.get('message', 'Waiting...')

        def periodic_sync():
            while True:
                try:
                    time.sleep(0.5)  # Check every 500ms
                    sync_from_shared_state()
                except Exception:
                    break  # Exit if window is closed

        sync_thread = threading.Thread(target=periodic_sync, daemon=True)
        sync_thread.start()

    window = webview.create_window('Multiprocess State Example', html=html)
    window.state.counter = shared_dict.get('counter', 0)
    window.state.message = shared_dict.get('message', 'Waiting...')
    window.events.loaded += on_loaded
    webview.start()


if __name__ == '__main__':
    # Create shared state between processes
    manager = multiprocessing.Manager()
    shared_dict = manager.dict()
    shared_dict['counter'] = 0
    shared_dict['message'] = 'Waiting...'

    # Create and start the webview process
    webview_process = multiprocessing.Process(target=run_webview, args=(shared_dict,))
    webview_process.start()

    # Main process is free to do other work
    print('Webview started in separate process')
    print('Main process is free to do other work...')

    # Simulate some work in the main process and update state
    for i in range(10):
        time.sleep(2)
        # Update shared state from main process
        shared_dict['counter'] = i + 1
        shared_dict['message'] = f'Main process step {i+1}/10'
        print(f"Main process working... {i+1}/10 (counter: {shared_dict['counter']})")

    shared_dict['message'] = 'Main process completed!'
    print('Main process finished its work')
    print('Waiting for webview process to complete...')

    # Wait for the webview process to finish
    webview_process.join()
    print('Webview process completed')
