# 五、接口设计

> 本文档由 `02-architecture.md` 自动拆分生成。
> 源文件：[../02-architecture.md](../02-architecture.md)

## 五、接口设计

### 什么是接口设计

接口设计定义模块之间的**通信契约**——函数的输入、输出、错误处理。它不是 REST API 设计（那是外部接口），而是**内部模块之间的接口**。

### 三层接口规范

**路由层 → 服务层**

```python
# routes/task_route.py
@rt
def create_task(title: str, project_id: int):
    """路由负责：接收 HTTP 参数，调用服务层，返回 HTMX 片段"""
    try:
        task = task_service.create(title=title, project_id=project_id)
    except ValidationError as e:
        return Div(P(f"参数错误: {e}"), cls="error")
    return render_task_card(task)


# services/task_service.py
def create(title: str, project_id: int) -> Task:
    """服务层负责：校验参数，调用数据层，返回数据对象
    
    输入：
        title: str — 任务标题，非空，最长 200 字
        project_id: int — 项目 ID，必须存在
    输出：
        Task — 创建后的任务对象
    异常：
        ValidationError — 参数校验失败
        NotFoundError — project_id 不存在
    """
    if not title or len(title) > 200:
        raise ValidationError("标题不合法")
    return task_repo.insert(title=title, project_id=project_id)
```

**服务层 → 数据层**

```python
# services/task_service.py
from models.task import task_repo

def list_by_date(date: str) -> list[Task]:
    """调用数据层查询，不涉及任何 UI 逻辑"""
    return task_repo(where="date(created_at) = ?", where_args=[date])


# models/task.py
class Task:
    id: int
    title: str
    project_id: int
    created_at: str
    done: bool

task_repo = db.create(Task, pk='id')
```

### 接口契约规范

| 规范 | 说明 | 违反的后果 |
|------|------|-----------|
| 每个函数必须有类型注解 | `def create(title: str, project_id: int) -> Task:` | 调用方不知道参数类型 |
| 每个函数必须有文档字符串 | 至少说明输入、输出、异常 | 调用方需要读实现代码才能理解 |
| 异常必须明确声明 | `raise ValidationError(...)` 而非 `except: pass` | 路由层不知道要捕获什么异常 |
| 服务层函数不能返回 UI 组件 | 返回数据对象（dict/class/list），不返回 Div/H1 | 服务层与 FastHTML 耦合，不可测试 |
| 路由层函数不能包含业务逻辑 | 只负责：收参数、调服务、渲染结果 | 业务逻辑散落在路由中，无法复用 |

---
