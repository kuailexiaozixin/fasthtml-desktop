# =============================================================================
# pywebview-examples / dom_manipulation.py
# 来源: user_skills/pywebview/scripts/dom_manipulation.py  (pywebview 官方示例, v6.2.1)
# 分类: A 类 DOM 已实证
# 适配: Windows / Edge WebView2 + FastHTML 技术栈
#   - 原始脚本多以 flask / 内置 http server / https:// 演示；在 fasthtml-desktop 中
#     请将页面地址改为 http://127.0.0.1:<fasthtml端口>（默认 5001，打包时由 07 协商）。
#   - 本文件为上游权威参考，保持原样；实际落地代码见 06-pywebview-shell.md 的改写版。
# 适配要点: create_element/append/text/classes/style/remove 全部在 6.2.1 实证通过。
# =============================================================================

"""This example demonstrates how to manipulate DOM in Python."""

import random

import webview

rectangles = []


def random_color():
    red = random.randint(0, 255)
    green = random.randint(0, 255)
    blue = random.randint(0, 255)

    return f'rgb({red}, {green}, {blue})'


def bind(window):
    def toggle_disabled():
        disabled = None if len(rectangles) > 0 else True
        remove_button.attributes = {'disabled': disabled}
        empty_button.attributes = {'disabled': disabled}
        move_button.attributes = {'disabled': disabled}

    def create_rectangle(_):
        color = random_color()
        rectangle = window.dom.create_element(
            f'<div class="rectangle" style="background-color: {color};"></div>', rectangle_container
        )
        rectangles.append(rectangle)
        toggle_disabled()

    def remove_rectangle(_):
        if len(rectangles) > 0:
            rectangles.pop().remove()
        toggle_disabled()

    def move_rectangle(_):
        if len(rectangle_container.children) > 0:
            rectangle_container.children[-1].move(circle_container)

    def empty_container(_):
        rectangle_container.empty()
        rectangles.clear()
        toggle_disabled()

    def change_color(_):
        circle.style['background-color'] = random_color()

    def toggle_class(_):
        circle.classes.toggle('circle')

    rectangle_container = window.dom.get_element('#rectangles')
    circle_container = window.dom.get_element('#circles')
    circle = window.dom.get_element('#circle')

    toggle_button = window.dom.get_element('#toggle-button')
    toggle_class_button = window.dom.get_element('#toggle-class-button')
    duplicate_button = window.dom.get_element('#duplicate-button')
    remove_button = window.dom.get_element('#remove-button')
    move_button = window.dom.get_element('#move-button')
    empty_button = window.dom.get_element('#empty-button')
    add_button = window.dom.get_element('#add-button')
    color_button = window.dom.get_element('#color-button')

    toggle_button.events.click += lambda e: circle.toggle()
    duplicate_button.events.click += lambda e: circle.copy()
    toggle_class_button.events.click += toggle_class
    remove_button.events.click += remove_rectangle
    move_button.events.click += move_rectangle
    empty_button.events.click += empty_container
    add_button.events.click += create_rectangle
    color_button.events.click += change_color


if __name__ == '__main__':
    window = webview.create_window(
        'DOM Manipulations Example',
        html="""
            <html>
                <head>
                <style>
                    button {
                        font-size: 100%;
                        padding: 0.5rem;
                        margin: 0.3rem;
                        text-transform: uppercase;
                    }

                    .rectangle {
                        width: 100px;
                        height: 100px;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        margin: 0.5rem;
                        border-radius: 5px;
                        background-color: red;
                    }

                    .circle {
                        border-radius: 50px;
                        background-color: red;
                    }

                    .circle:hover {
                        background-color: green;
                    }

                    .container {
                        display: flex;
                        flex-wrap: wrap;
                    }
                </style>
                </head>
                <body>
                    <button id="toggle-button">Toggle circle</button>
                    <button id="toggle-class-button">Toggle class</button>
                    <button id="color-button">Change color</button>
                    <button id="duplicate-button">Duplicate circle</button>
                    <button id="add-button">Add rectangle</button>
                    <button id="remove-button" disabled>Remove rectangle</button>
                    <button id="move-button" disabled>Move rectangle</button>
                    <button id="empty-button" disabled>Remove all</button>
                    <div id="circles" style="display: flex; flex-wrap: wrap;">
                        <div id="circle" class="rectangle circle"></div>
                    </div>

                    <div id="rectangles" class="container"></div>
                </body>
            </html>
        """,
    )
    webview.start(bind, window)
