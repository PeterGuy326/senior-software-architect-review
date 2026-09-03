# 案例分析题型分类索引

> 数据来源：近 10 年真题统计 + [xxlllq/system_architect](https://github.com/xxlllq/system_architect) 案例集 + 希赛 / 软考通

## 案例考试套路（铁律）

- **5 大题任选 3 题作答**（每题 25 分，共 75 分）
- **时长 90 分钟**
- **合格线 45 分**
- **第 1 题固定必做，但题型不固定**：2026 上半年回忆版为 IoT + 时序数据库 + MQTT
- **高频核心**：架构评估 / 质量属性、数据库 / 建模仍需优先掌握，但不得绑定固定题号
- **3–5 题**：从微服务、缓存、消息、安全、嵌入式、大数据中选 3 题

## 13 大题型索引（按考频排序）

> ⭐ 01-09 含**完整模拟题**；10-13 为**答题套路精华版**（核心考点 + 模板 + 高分句 + 陷阱）。

| # | 题型 | 出现频次 | 必考度 | 文件 |
|---|---|---|---|---|
| 01 | 架构评估（效用树 + 四类点） | ⭐⭐⭐⭐⭐ | 高频核心 | [01-architecture-evaluation.md](./01-architecture-evaluation.md) |
| 02 | 数据库设计（ER + 规范化 + 缓存/NoSQL 混合） | ⭐⭐⭐⭐⭐ | 高频核心 | [02-database-design.md](./02-database-design.md) |
| 03 | 架构风格对比与选型 | ⭐⭐⭐⭐ | 高频 | [03-style-comparison.md](./03-style-comparison.md) |
| 04 | UML 建模与分析 | ⭐⭐⭐⭐ | 高频 | [04-uml-modeling.md](./04-uml-modeling.md) |
| 05 | 微服务拆分与重构 | ⭐⭐⭐⭐ | 高频 | [05-microservice-refactor.md](./05-microservice-refactor.md) |
| 06 | 消息中间件 / 缓存应用 | ⭐⭐⭐⭐ | 高频 | [06-messaging-caching.md](./06-messaging-caching.md) |
| 07 | 安全架构分析 | ⭐⭐⭐ | 中频 | [07-security-architecture.md](./07-security-architecture.md) |
| 08 | 嵌入式 / 构件组装 | ⭐⭐⭐ | 中频 | [08-embedded-components.md](./08-embedded-components.md) |
| 09 | 大数据 / Web 架构 | ⭐⭐⭐ | 中频（新增） | [09-big-data-architecture.md](./09-big-data-architecture.md) |
| **10** | **SOA 与企业应用集成** | ⭐⭐⭐ | 中频 | **[10-soa-integration.md](./10-soa-integration.md)** |
| **11** | **架构演化与系统改造** | ⭐⭐⭐ | 中高频（2024 高频） | **[11-architecture-evolution.md](./11-architecture-evolution.md)** |
| **12** | **DevOps 部署与 CI/CD** | ⭐⭐⭐ | 中频（云原生新增） | **[12-devops-deployment.md](./12-devops-deployment.md)** |
| **13** | **可靠性与容灾设计** | ⭐⭐⭐⭐ | 高频（金融/医疗） | **[13-reliability-design.md](./13-reliability-design.md)** |

## 答题铁律

### 1. **三段式**每小问

```
结论（1 句） → 理由（2–3 点） → 量化 / 技术名词
```

### 2. **优先抓关键词**

题干里"**每天 X 万订单**"/"**99.9% 可用**"/"**响应 < 200ms**"/"**异地容灾**"—— 这些数字是**得分提示**。

### 3. **必写技术名词**

- 架构评估 → **效用树 / 敏感点 / 权衡点 / 风险点**
- 数据库 → **范式 / 候选键 / 外键 / 参照完整性**
- 微服务 → **限界上下文 / DDD / CAP**
- 消息 → **ACK / 幂等 / 死信 / 顺序消息**
- 缓存 → **Cache Aside / 穿透击穿雪崩**
- 安全 → **STRIDE / CIA / 等保**

## 90 分钟时间分配

```
读题 + 选题             10 min
第 1 题                 25 min
第 2 题                 25 min
第 3 题                 25 min
检查                     5 min
```

## 选题策略

- **必做第 1 题**—— 先识别题型，再按小问分值调用对应模板
- **选做优先数据库 / 质量属性**—— 理论结构稳定，但仍以当场题目和个人证据为准
- **第 3 题**从熟悉的技术栈挑一道（微服务 / 消息 / 缓存）

## 通用评分逻辑

| 维度 | 占比 |
|---|---|
| 关键词 / 术语 | 40% |
| 技术细节 / 量化 | 30% |
| 权衡与理由 | 20% |
| 表达与条理 | 10% |

---

## 2024 真题归位索引

> 真题原题与参考答案已按主题归位到下述文件末尾。考前**先做模拟题再对真题**效果最佳。

| 真题年份 + 题号 | 主题 | 归位文件 |
|---|---|---|
| **2024 下半年 T1** | AI 智能平台质量属性 + Ping/Echo + 心跳 | [01-architecture-evaluation.md](./01-architecture-evaluation.md) |
| **2024 下半年 T2** | Cache-Aside 缓存一致性 | [06-messaging-caching.md](./06-messaging-caching.md) |
| **2024 下半年 T3** | ROS 机器人操作系统升级 | [08-embedded-components.md](./08-embedded-components.md) |
| **2024 上半年 T3** | 系统可靠性 + 恢复块 vs N 版本 | [13-reliability-design.md](./13-reliability-design.md) |
| **2024 上半年 T4** | 3NF 分解 + 读写锁并发控制 | [02-database-design.md](./02-database-design.md) |
| **2024 上半年 T5** | Web 综合（缓存雪崩 + 读写分离） | [06-messaging-caching.md](./06-messaging-caching.md) |

来源：公开真题回忆版（CSDN、博客园等），仅供学习参考。

---

## 2026 上半年回忆版归位索引

> 来源不完整，以下只做主题归位，不提交原题全文或把参考答案当官方答案。详情见 [`../2026上-recall-signals.md`](../2026上-recall-signals.md)。

| 题号 | 主题 | 归位文件 |
|---|---|---|
| **T1（必做）** | 智慧养老 IoT + 时序数据库 + MQTT QoS | [06-messaging-caching.md](./06-messaging-caching.md) / [08-embedded-components.md](./08-embedded-components.md) |
| **T2** | 自适应学习 + 推荐冷启动 + 知识图谱 | [09-big-data-architecture.md](./09-big-data-architecture.md)（待继续专题化） |
| **T3** | 秒杀并发控制 + Redis | [02-database-design.md](./02-database-design.md) |
| **T4** | AIoT 四层架构 + 边缘 AI 权衡 | [08-embedded-components.md](./08-embedded-components.md) |
| **T5** | 质量属性场景 + 管道-过滤器 | [01-architecture-evaluation.md](./01-architecture-evaluation.md) / [03-style-comparison.md](./03-style-comparison.md) |

---

## 2022 下半年真题归位索引

| 真题年份 + 题号 | 主题 | 归位文件 |
|---|---|---|
| **2022 下半年 T1** | 电商质量属性效用树 + OO vs 解释器风格 | [01-architecture-evaluation.md](./01-architecture-evaluation.md) |
| **2022 下半年 T2** | 煤矿安全预警 DFD + ER + 数据字典 | [04-uml-modeling.md](./04-uml-modeling.md) |
| **2022 下半年 T3** | 宇航嵌入式心跳 vs 超时探测 + 数据驱动 | [08-embedded-components.md](./08-embedded-components.md) |
| **2022 下半年 T4** | 仓储缓存同步 + 一致性哈希 + 布隆过滤器 | [06-messaging-caching.md](./06-messaging-caching.md) |
| **2022 下半年 T5** | 边缘计算门禁 + MQTT 协议选型 | [06-messaging-caching.md](./06-messaging-caching.md) |

来源：公开真题回忆版（CSDN、博客园等），仅供学习参考。
