# 十、设计检查清单


- [ ] 场景已确认，架构类型已选型
- [ ] 架构模式已选型，并追溯到硬约束
- [ ] 系统上下文和边界已明确（什么是系统内的，什么在系统外）
- [ ] MVP 边界表已定义（Includes / Excludes）
- [ ] 核心业务流的主路径、异常路径已列出
- [ ] 页面/任务状态机已定义（就绪→处理中→成功/失败）
- [ ] 模块划分合理（routes/services/models + 可选扩展模块）
- [ ] 存储选择已确定（SQLite / JSON / 文件路径）
- [ ] 数据模型根据读写路径设计，关键字段有索引
- [ ] 技术债已记录（当前选了什么，计划什么时候换）
- [ ] 层间接口有类型注解和文档
- [ ] 依赖方向单向（routes → services → models）
- [ ] 错误处理统一（使用自定义异常 + 装饰器或 try/except）
- [ ] Agent 等外部集成模块未导入 fasthtml
- [ ] CSS/JS 已内联
- [ ] 路径代码使用了 sys.frozen 检测
- [ ] SOLID 五大设计原则
  - [ ] 单一职责原则（Single Responsibility Principle，SRP）：一个模块/类只承担单一职责，只做一件事
  - [ ] 开放-闭合原则（Open-Closed Principle，OCP）：确保系统行为的修改可通过新增代码实现，而非修改现有代码
  - [ ] 里氏替换原则（Liskov Substitution Principle，LSP）：要构建由可互换组件组成的软件系统，组件必须遵循统一契约，确保可相互替换
  - [ ] 接口分离原则（Interface Segregation Principle，ISP）：不强迫客户端依赖它用不到的方法，接口小而专
  - [ ] 依赖倒置原则（Dependency Inversion Principle，DIP）：实现高层级策略的代码不应依赖实现低层级细节的代码；相反，低层级细节应依赖高层级策略

---
