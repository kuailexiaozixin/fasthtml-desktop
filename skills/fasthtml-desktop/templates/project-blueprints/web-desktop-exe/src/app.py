\"\"\"app.py — FastHTML 计算器业务逻辑
\"\"\"
from fasthtml.common import *

app, rt = fast_app(
    hdrs=(
        Style("""
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, sans-serif; padding: 20px; background: #f5f5f5; }
            .container { max-width: 600px; margin: auto; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; margin-bottom: 10px; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; }
            input, select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
            button { background: #3498db; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer; margin-top: 10px; }
            button:hover { background: #2c80b9; }
            #result { margin-top: 20px; padding: 15px; background: #eef2f5; border-radius: 4px; font-size: 1.2em; text-align: center; }
        """),
    ),
)

@rt
def index():
    \"\"\"首页 - 计算器\"\"\""
    return Titled("简单计算器", 
        Div(
            H1("简单计算器"),
            Div(
                Class("container"),
                Div(
                    Class("form-group"),
                    Label("第一个数字:"),
                    Input(type="number", name="num1", placeholder="输入数字", value="0"),
                ),
                Div(
                    Class("form-group"),
                    Label("第二个数字:"),
                    Input(type="number", name="num2", placeholder="输入数字", value="0"),
                ),
                Div(
                    Class("form-group"),
                    Label("运算符:"),
                    Select(
                        name="operator",
                        children=[
                            Option("+", value="+"),
                            Option("-", value="-"),
                            Option("*", value="*"),
                            Option("/", value="/"),
                        ],
                    ),
                ),
                Button("计算", type="submit"),
                Div(
                    id="result",
                    Class="result",
                    "等待计算..."
                ),
            ),
        )
    )

@rt
def calculate():
    \"\"\"处理计算请求\"\"\""
    try:
        num1 = float(request.form.get("num1", 0))
        num2 = float(request.form.get("num2", 0))
        operator = request.form.get("operator", "+")
        
        if operator == "+":
            result = num1 + num2
        elif operator == "-":
            result = num1 - num2
        elif operator == "*":
            result = num1 * num2
        elif operator == "/":
            result = num1 / num2 if num2 != 0 else "除零错误"
        else:
            result = "未知操作"
            
        return f"结果: {result}"
    except Exception as e:
        return f"错误: {str(e)}"

# 将计算器视图添加到应用
app = app