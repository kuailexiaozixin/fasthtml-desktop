# 四、数据架构

> 本文档由 `02-architecture.md` 自动拆分生成。
> 源文件：[../02-architecture.md](../02-architecture.md)

## 四、数据架构

### 数据的存储位置

| 数据类型 | 存储位置 | 说明 |
|---------|---------|------|
| 应用配置 | `BASE_DIR / config.json` 或环境变量 | 用户可修改 |
| 业务数据 | SQLite（Fastlite） | `BASE_DIR / data / app.db` |
| 日志 | `BASE_DIR / logs / app.log` | 按日期滚动，保留 30 天 |
| 临时文件 | Python tempfile 或 `BASE_DIR / temp` | 退出时清理 |
| 用户文件 | 用户在本地选择的路径 | 不复制到应用目录 |

### Fastlite 数据模型设计步骤

**第一步：列实体**

写下系统中的名词。以任务管理工具为例：

```
Task（任务）、Project（项目）、Tag（标签）、Comment（评论）
```

**第二步：画关系**

```
Project 1 ──── N Task
Task    N ──── M Tag
Task    1 ──── N Comment
```

**第三步：定读写路径**

列出频率最高、最重要的数据操作：

| 操作 | 类型 | 数据表 | 查询方式 |
|------|------|--------|---------|
| 列出今天的任务 | 读 | Task | WHERE date = today |
| 按项目分组 | 读 | Task, Project | JOIN + GROUP BY project_id |
| 按标签筛选 | 读 | Task, Tag | JOIN 中间表 |
| 创建任务 | 写 | Task | INSERT |
| 批完成 | 写 | Task | UPDATE WHERE ids IN (...) |

**第四步：确定索引**

根据读写路径确定索引：

```python
class Task:
    id: int            # 主键索引（自动）
    title: str
    project_id: int    # 需要索引：经常按 project_id 查
    tag_id: int
    created_at: str    # 需要索引：经常按日期排序和筛选
    done: bool
```

### 路径适配（打包安全）

```python
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent

DB_PATH = BASE_DIR / "data" / "app.db"
```

---
