# 知识点 13 · 设计模式 GoF 23

## 一、核心概念

### SOLID 原则

| 原则 | 含义 |
|---|---|
| **S**RP | 单一职责 |
| **O**CP | **开闭原则**（开放扩展、关闭修改）|
| **L**SP | 里氏替换 |
| **I**SP | 接口隔离 |
| **D**IP | **依赖倒置**（高层不依赖低层，都依赖抽象） |

### GoF 23 分类速查

**创建型（5）**：
- 单例 Singleton · 工厂方法 · **抽象工厂** · 建造者 Builder · 原型 Prototype

**结构型（7）**：
- 适配器 Adapter · 桥接 Bridge · 组合 Composite · **装饰器 Decorator** · 外观 Facade · 享元 Flyweight · **代理 Proxy**

**行为型（11）**：
- **责任链** · 命令 Command · 解释器 · 迭代器 · 中介者 Mediator · 备忘录 · **观察者 Observer** · 状态 · **策略 Strategy** · **模板方法** · 访问者

## 二、关联资源

- 速查：[cheatsheets/design-patterns-gof23.md](../cheatsheets/design-patterns-gof23.md)
- 论文主题：[past-papers/paper-topics/10-design-patterns.md](../past-papers/paper-topics/10-design-patterns.md)

## 三、典型例题

### 📚 选择题 1（模式匹配）

支付系统支持微信/支付宝/银联多种方式，运行时可切换。最合适的模式：
- A. 工厂方法  B. **策略**  C. 观察者  D. 单例

**答案**：B

### 📚 选择题 2（代理模式）

Spring AOP 的底层原理属于：
- A. 装饰器  B. **代理**  C. 适配器  D. 外观

**答案**：B（JDK 动态代理 / CGLIB）

### 📚 选择题 3（观察者）

消息发布后自动通知所有订阅者：
- A. 责任链  B. **观察者**  C. 中介者  D. 迭代器

**答案**：B

### 📚 选择题 4（SOLID）

新增需求只扩展不修改原代码，符合：
- A. SRP  B. **OCP**  C. LSP  D. ISP

**答案**：B

### 🎯 案例填空：订单校验链

订单下单要依次校验：库存 → 价格 → 风控 → 用户状态，要求可灵活调整顺序。

**选用模式**：**责任链（Chain of Responsibility）**
**UML**：Handler 抽象类持有 next 引用，子类 InventoryHandler / PriceHandler / RiskHandler / UserHandler，sortBy(order) 动态组装链。

### ✍️ 论文场景

"新增支付渠道采用**策略模式**，符合 **OCP 开闭原则**；订单校验流程采用**责任链**，每个校验器**单一职责 SRP**；读写分离采用 **CQRS 架构模式**。"
