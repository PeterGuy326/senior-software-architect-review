# 案例分析题型分类索引

> 数据来源：近 10 年真题统计 + [xxlllq/system_architect](https://github.com/xxlllq/system_architect) 案例集 + 希赛 / 软考通

## 案例考试套路（铁律）

- **5 大题任选 3 题作答**（每题 25 分，共 75 分）
- **时长 90 分钟**
- **合格线 45 分**
- **必考题 1**：架构评估（ATAM / 质量属性场景，**几乎每年都考**）
- **必考题 2**：数据库 / 建模（ER / 关系模式 / 规范化）
- **3–5 题**：从微服务、缓存、消息、安全、嵌入式、大数据中选 3 题

## 9 大题型索引（按考频排序）

| # | 题型 | 出现频次 | 必考度 | 文件 |
|---|---|---|---|---|
| 01 | 架构评估（效用树 + 四类点） | ⭐⭐⭐⭐⭐ | **必考** | [01-architecture-evaluation.md](./01-architecture-evaluation.md) |
| 02 | 数据库设计（ER + 规范化） | ⭐⭐⭐⭐⭐ | **必考** | [02-database-design.md](./02-database-design.md) |
| 03 | 架构风格对比与选型 | ⭐⭐⭐⭐ | 高频 | [03-style-comparison.md](./03-style-comparison.md) |
| 04 | UML 建模与分析 | ⭐⭐⭐⭐ | 高频 | [04-uml-modeling.md](./04-uml-modeling.md) |
| 05 | 微服务拆分与重构 | ⭐⭐⭐⭐ | 高频 | [05-microservice-refactor.md](./05-microservice-refactor.md) |
| 06 | 消息中间件 / 缓存应用 | ⭐⭐⭐⭐ | 高频 | [06-messaging-caching.md](./06-messaging-caching.md) |
| 07 | 安全架构分析 | ⭐⭐⭐ | 中频 | [07-security-architecture.md](./07-security-architecture.md) |
| 08 | 嵌入式 / 构件组装 | ⭐⭐⭐ | 中频 | [08-embedded-components.md](./08-embedded-components.md) |
| 09 | 大数据 / Web 架构 | ⭐⭐⭐ | 中频（新增） | [09-big-data-architecture.md](./09-big-data-architecture.md) |

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

- **必做第 1 题**（架构评估）—— 套路最稳
- **次选第 2 题**（数据库）—— 理论题得分稳
- **第 3 题**从熟悉的技术栈挑一道（微服务 / 消息 / 缓存）

## 通用评分逻辑

| 维度 | 占比 |
|---|---|
| 关键词 / 术语 | 40% |
| 技术细节 / 量化 | 30% |
| 权衡与理由 | 20% |
| 表达与条理 | 10% |
