# 知识点 10 · 架构风格

## 一、核心概念

### 5 大类（必背）

| 分类 | 代表风格 | 例子 |
|---|---|---|
| **数据流** | 批处理、**管道-过滤器** | UNIX、编译器、ETL |
| **调用-返回** | 主程序-子程序、OO、**分层**、C/S、B/S | Web 分层 |
| **独立构件** | 进程通信、**事件驱动（发布-订阅）** | GUI、MQ |
| **虚拟机** | 解释器、规则系统 | JVM、规则引擎 |
| **数据中心** | 数据库仓库、**黑板** | 数仓、AI 推理 |

### 现代扩展风格

- **MVC / MVP / MVVM**：UI 层分离
- **SOA / 微服务**：服务化
- **REST**：资源 + HTTP
- **事件溯源 / CQRS**：读写分离

## 二、关联资源

- 笔记：[notes/09-architecture-styles/](../notes/09-architecture-styles/)
- 速查：[cheatsheets/architecture-styles.md](../cheatsheets/architecture-styles.md)
- 案例题型：[past-papers/case-types/03-style-comparison.md](../past-papers/case-types/03-style-comparison.md)
- 论文主题：[past-papers/paper-topics/01-architecture-design.md](../past-papers/paper-topics/01-architecture-design.md)

## 三、典型例题

### 📚 选择题 1（风格归类）

UNIX Shell 的 `cat | grep | sort` 属于哪种架构风格？
- A. 分层  B. **管道-过滤器**  C. 事件驱动  D. 黑板

**答案**：B

### 📚 选择题 2（风格对比）

发布-订阅模式属于：
- A. 数据流  B. 调用-返回  C. **独立构件（事件驱动）**  D. 虚拟机

**答案**：C

### 📚 选择题 3（MVC）

MVC 中负责接收用户请求并调度 Model 和 View 的是：
- A. Model  B. View  C. **Controller**  D. Service

**答案**：C

### 🎯 案例填空：风格选型

**场景**：日志处理系统，日 10 亿条，要求高吞吐、可并行。

**选型**：**管道-过滤器**
**理由**：数据流顺序处理、天然可**并行**、**可复用过滤器**；Flume → Kafka → Flink 即为典型管道实现。

### ✍️ 论文场景

"针对【高并发 / 低延迟 / 高可用】需求，综合采用**微服务 + 事件驱动 + 分层**混合风格：服务间解耦（事件驱动），服务内分层（表现/业务/数据），兼顾性能与可维护性。"
