# 十二、状态机设计

> 本文档由 `02-architecture.md` 自动拆分生成。
> 源文件：[../02-architecture.md](../02-architecture.md)

## 十二、状态机设计

### 什么是状态机

状态机描述一个实体（页面、任务、窗口）的**生命周期**——可能处于哪些状态、什么事件触发状态转换、每个状态的进入和退出条件。

### 页面状态模型

fasthtml-desktop 应用的每个页面或操作可以抽象为以下状态：

```
         ┌──────────┐
         │  就绪     │
         └────┬─────┘
              │ 用户触发操作
              ▼
         ┌──────────┐
         │  处理中   │  ← 显示加载状态 / SSE 进度
         └────┬─────┘
        ┌─────┴──────┐
        ▼            ▼
   ┌────────┐  ┌────────┐
   │  成功   │  │  失败   │
   │(显示结果)│  │(显示错误)│
   └────┬───┘  └────┬───┘
        │            │ 用户点重试
        └──────┬─────┘
               │
               ▼
         ┌──────────┐
         │  就绪     │
         └──────────┘
```

### FastHTML 中的实现

```python
# 前端通过状态切换显示不同内容
def render_state(state: str, data=None, error=None):
    if state == "idle":
        return Div(
            Form(Input(name="path"), Button("开始", hx_post="/process", hx_target="#result")),
            id="result"
        )
    elif state == "loading":
        return Div(Progress(), P("处理中..."), id="result")
    elif state == "success":
        return Div(P(f"完成：{data}"), Button("返回", hx_get="/", hx_target="body"), id="result")
    elif state == "error":
        return Div(P(f"错误：{error}", style="color:red"),
                   Button("重试", hx_get="/", hx_target="body"), id="result")

# 路由只负责计算状态，不负责渲染样式
@app.post
def process(path: str):
    try:
        result = do_process(path)
        return render_state("success", data=result)
    except Exception as e:
        return render_state("error", error=str(e))
```

### 文件批量重命名工具的状态机示例

```
用户操作 → 页面状态
  ├─ 打开工具 → 就绪（等待用户输入）
  ├─ 填写参数 → 就绪
  ├─ 点击预览 → 处理中 → 预览完成（就绪）
  ├─ 点击执行 → 处理中 → 重命名成功 → 就绪
  │                                  → 重命名部分失败 → 显示失败列表
  └─ 点击取消 → 就绪
```

---
