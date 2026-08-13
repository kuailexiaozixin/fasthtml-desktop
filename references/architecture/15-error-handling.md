# 十五、统一错误处理

> 本文档由 `02-architecture.md` 自动拆分生成。
> 源文件：[../02-architecture.md](../02-architecture.md)

## 十五、统一错误处理

### 错误传递契约

```
路由层 → 服务层 → 数据层（或外部 API）
                        │
                  ┌─────┴──────┐
                  │            │
              校验失败     查询失败
            (Validation)(NotFound/Network)
                  │            │
                  ▼            ▼
            服务层抛异常 → 路由层捕获 → 渲染错误提示
```

### 错误类型定义

```python
# services/errors.py — 统一错误定义
class AppError(Exception):
    """基类，所有应用异常的父类"""
    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code
        super().__init__(message)

class ValidationError(AppError):
    """参数校验失败"""
    def __init__(self, message: str):
        super().__init__(message, code="VALIDATION")

class NotFoundError(AppError):
    """数据不存在"""
    def __init__(self, message: str):
        super().__init__(message, code="NOT_FOUND")

class NetworkError(AppError):
    """网络调用失败"""
    def __init__(self, message: str = "网络连接失败，请重试"):
        super().__init__(message, code="NETWORK")
```

### 路由层错误处理模式

```python
from services.errors import ValidationError, NotFoundError, NetworkError

@app.post
def safe_process(path: str):
    """带统一错误处理的路由"""
    try:
        result = file_service.process(path)
        return render_success(result)
    except ValidationError as e:
        return Div(P(f"输入错误：{e.message}"), cls="error")
    except NotFoundError as e:
        return Div(P(f"未找到：{e.message}"), cls="error")
    except NetworkError:
        return Div(P("网络连接失败，请检查网络后重试"), Button("重试", hx_get="/retry"), cls="error")
    except Exception as e:
        logger.exception("未预期的错误")
        return Div(P("系统错误，请重试"), cls="error")
```

### 错误处理装饰器（简化重复代码）

```python
def safe_run(func):
    """路由错误处理装饰器：捕获已知异常，统一返回提示"""
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            return Div(P(f"输入错误：{e}"), cls="error")
        except NotFoundError as e:
            return Div(P(f"未找到：{e}"), cls="error")
        except NetworkError:
            return Div(P("网络连接失败"), Button("重试", hx_get="..."), cls="error")
        except Exception as e:
            logger.exception("未预期的错误")
            return Div(P("系统错误，请重试"), cls="error")
    return wrapper

# 使用
@app.post
@safe_run
def process(file: UploadFile):
    # 只需要写正常路径，异常由装饰器处理
    return do_process(file)
```

---
