# 论文主题 06 · 大数据架构与 NoSQL 应用

## 历年出题角度

- 论大数据处理架构及其应用
- 论 Lambda / Kappa 架构
- 论 NoSQL 数据库的应用
- 论数据湖与数据仓库

## 一、核心理论

### 大数据 5V 特征

**V**olume 体量 · **V**elocity 速度 · **V**ariety 多样 · **V**eracity 真实 · **V**alue 价值

### Lambda vs Kappa 架构

| 架构 | 批层 | 速度层 | 特点 |
|---|---|---|---|
| **Lambda** | Hadoop/Spark | Storm/Flink | 双链路、复杂但准确 |
| **Kappa** | — | **Flink 统一** | 单链路、简化 |

### NoSQL 四大类

| 类型 | 代表 | 场景 |
|---|---|---|
| 键值 | Redis / Memcached | 缓存、会话 |
| 列族 | HBase / Cassandra | 海量稀疏数据 |
| 文档 | MongoDB / CouchDB | 半结构化 JSON |
| 图 | Neo4j / JanusGraph | 关系网络 |

### 数据湖 vs 数据仓库

- **数仓**：结构化、schema-on-write、BI 报表
- **数据湖**：原始数据、schema-on-read、AI/ML
- **湖仓一体**：Databricks Delta / Apache Iceberg

### CAP / BASE

- **CAP**：一致性 / 可用性 / 分区容错（三选二）
- **BASE**：基本可用 / 软状态 / 最终一致（NoSQL 典型）

## 二、万能提纲

```
1. 背景（350 字）
   - 【电商用户行为 / 日志分析 / 实时大屏】系统
   - 数据规模：日 100 亿条，PB 级存储
2. 理论（350 字）
   - 5V、Lambda/Kappa、NoSQL 分类、CAP
3. 实践论述（1600 字）⭐⭐⭐⭐⭐
   (1) 采集：Flume / Canal / Kafka
   (2) 存储：HDFS（冷）+ HBase（热）+ Redis（热点）
   (3) 计算：Flink 实时流 + Spark 批处理（Lambda）
   (4) 查询：ClickHouse / Druid（OLAP）
   (5) 调度：Airflow / DolphinScheduler
   (6) 数据治理：元数据 + 血缘 + 质量
4. 成效（250 字）
   - 实时延迟 < 1s，离线 T+1
```

## 三、关键数据

- 数据量：**日增 100 亿条 / 10TB**
- 实时延迟：**秒级（< 1s）**
- 离线：**T+1 / T+H**
- 查询 QPS：**10 万**
- 压缩比：**Parquet/ORC 5–10 倍**

## 四、万能句式

- "采用 **Lambda 架构**：批层 Spark 保证准确性，速度层 Flink 保证时效性"
- "选用 **HBase** 存海量明细（PB 级），**ClickHouse** 支持亚秒级 OLAP 查询"
- "基于 **Kappa 架构**用 **Flink** 统一流批，简化运维"

## 五、避坑点

| ❌ | ✅ |
|---|---|
| 只提 Hadoop | 必须讲 **实时（Flink）+ 离线（Spark）** 结合 |
| 不谈治理 | **元数据 / 血缘 / 质量** 是数据湖核心 |
| NoSQL 混用 | 说清 **为什么选**（场景匹配） |
| 无数据量 | 必须量化：**日增 X 亿条、X TB** |

---

## 模拟论文题

> ⚠️ **自主命题**：题目为基于公开考点和历年真题方向改编的仿真模拟题，避免版权风险。建议**严格 120 分钟限时**写完整 2500 字论文，再对照提纲答案与评分维度复盘。

### 模拟论文题 1 · 论 Lambda / Kappa 大数据架构在实时分析场景中的应用

**【完整题目】**（约 410 字）

随着移动互联网、IoT、实时业务的快速发展，企业数据呈现 5V 特征——Volume（海量）、Velocity（高速）、Variety（多样）、Veracity（真实性挑战）、Value（低密度高价值）。如何在 PB 级数据规模下同时支撑**实时分析（秒级延迟）**和**离线分析（T+1 准确）**，成为架构师面临的关键挑战。Lambda 架构通过批处理层（Spark/Hadoop）+ 速度层（Storm/Flink）双链路保证准确性与时效性兼得，但代码维护双份；Kappa 架构则用 Flink 统一流批，简化运维但对状态管理要求高。同时 NoSQL 数据库（HBase、ClickHouse、Druid 等）在存储与查询层各擅其长，需要架构师按 CAP 与 BASE 原则做取舍。

请围绕"**论大数据处理架构及其应用**"论述以下三个问题：

1. **概要叙述**你参与设计与开发的大数据系统项目，以及你担任的主要工作（约 300 字应答）。
2. **简要说明**大数据 5V 特征、Lambda/Kappa 架构的差异以及主流 NoSQL 数据库分类（约 400 字应答）。
3. **详细论述**你在项目中如何设计采集、存储、计算、查询四层架构以及具体技术选型，最终实现何种业务效果（约 1500-1800 字应答）。

**【提纲式参考答案】**（约 1400 字提纲）

#### 摘要框架（300 字模板）

"我于 {2023} 年参与了 {电商用户行为分析 / 工业 IoT 监控 / 金融实时风控} 平台建设，担任 {大数据架构师}。系统接入 {日增 100 亿条事件 / 10TB 数据 / 1000 万 DAU}，要求实时延迟 {< 1 秒}、离线 T+1 准确。本文论述 Lambda 架构在该项目的落地：采集层 Flume + Kafka、存储层 HDFS + HBase + Redis、计算层 Spark 批 + Flink 流、查询层 ClickHouse OLAP，最终实时大屏延迟 800ms、离线报表 T+1 凌晨 6 点完成、查询 QPS 12 万、整体压缩比 7 倍。"

#### 一、项目背景（350 字提纲）

- **业务背景**：电商日 100 亿用户行为日志，需支撑实时大屏 + 离线报表 + AI 推荐
- **团队规模**：20 人（数据架构 2 + 开发 12 + 数仓 4 + 运维 2）
- **关键质量属性**：吞吐、延迟、准确性、可扩展性、成本
- **业务约束**：实时 < 1s、离线 T+1、5 年存储、PB 级容量

#### 二、核心理论（400 字提纲）

- 大数据 5V：Volume / Velocity / Variety / Veracity / Value
- Lambda 架构：批层（Spark/Hadoop）+ 速度层（Flink/Storm）+ 服务层（合并查询）
- Kappa 架构：Flink 统一流批，单链路，简化运维但状态管理复杂
- NoSQL 四类：键值（Redis）/ 列族（HBase/Cassandra）/ 文档（MongoDB）/ 图（Neo4j）
- 数据湖 vs 数仓 vs 湖仓一体（Iceberg/Delta）
- CAP 三选二、BASE 最终一致

#### 三、实践论述（1500 字提纲，分 4 节）

##### 3.1 采集层
- Flume 采日志，Canal 采 MySQL binlog
- Kafka 集群（10 节点、200 分区、副本因子 3）
- 数据契约：Avro Schema Registry 强约束
- 量化：日吞吐 100 亿条、峰值 50 万 EPS

##### 3.2 存储层（按热度分级）
- 热（Redis）：用户画像、热点商品（TTL 1 小时）
- 温（HBase）：明细数据、按 RowKey 哈希
- 冷（HDFS Parquet）：历史归档，压缩比 7 倍
- OLAP（ClickHouse）：聚合宽表、亚秒级查询
- 量化：存储成本降 60%

##### 3.3 计算层（Lambda）
- 批层：Spark 凌晨跑全量统计，T+1 准确
- 速度层：Flink 消费 Kafka，5s 窗口计算
- 服务层：合并批+实时结果，对外统一查询
- 状态管理：Flink Checkpoint + RocksDB 持久化

##### 3.4 风险与应对（必有）
- 风险 1：双链路代码维护成本高 → 抽象 SQL 层（Flink SQL + Spark SQL 共用语义）
- 风险 2：Kafka 数据倾斜 → Key 预处理 + 自定义 Partitioner
- 风险 3：实时口径与离线不一致 → 数据血缘 Atlas + 每日对账

#### 四、总结与展望（250 字提纲）

- 项目结果：实时延迟 800ms、离线 T+1 6 点完成、查询 QPS 12 万、零数据丢失
- 经验教训：①Lambda 双链路是阶段性方案，未来 Kappa 化 ②数据治理（血缘/质量/安全）是核心 ③NoSQL 选型必须按场景
- 未来演进：Flink 统一流批 (Kappa) + Iceberg 湖仓一体 + AI 数据资产平台

**【加分关键词清单】**

| 类别 | 必写术语 |
|---|---|
| 理论术语 | 5V、Lambda、Kappa、CAP、BASE、数据湖、数仓、湖仓一体、Schema-on-Read |
| 方法论 | Flume、Kafka、HDFS、HBase、Spark、Flink、ClickHouse、Druid、Iceberg、Atlas |
| 量化范围 | 日 100 亿条 / 10TB / 实时 < 1s / 离线 T+1 / 查询 QPS 10 万 / 压缩比 7x |
| 业界案例点缀 | 阿里 MaxCompute、字节 ByteHouse、网易猛犸、Netflix Iceberg、Databricks Delta Lake |

**【评分维度对照表】**

| 维度 | 占比 | 评分要点 |
|---|---|---|
| 项目真实性 | 25% | 数据规模量化 / 团队规模 / 业务时效要求 |
| 理论深度 | 25% | 5V / Lambda vs Kappa / NoSQL 四类全 |
| 实践细节 | 35% | 四层架构齐 / 选型有理由 / 数据治理可见 |
| 文笔与结构 | 15% | 采集-存储-计算-查询逻辑清晰 / 字数 ≥ 2500 |

**【避坑提醒】**

- ❌ 只提 Hadoop → ✅ 必须实时（Flink）+ 离线（Spark）结合
- ❌ NoSQL 混用不说理由 → ✅ 每个 NoSQL 必须给场景匹配理由（Redis 热点、HBase 海量明细、ClickHouse OLAP）
- ❌ 不谈治理 → ✅ 元数据 / 血缘 / 质量是数据湖核心
- ❌ 无数据量 → ✅ 必须量化：日 X 亿条、X TB
- ❌ Lambda vs Kappa 写成"二选一" → ✅ 实际 Lambda 是阶段性，Kappa 是演进方向

---

### 模拟论文题 2 · 论 NoSQL 数据库的选型与应用

**【完整题目】**（约 400 字）

传统关系型数据库在面对海量、稀疏、半结构化、高并发场景时存在明显瓶颈，NoSQL 数据库应运而生。NoSQL 按数据模型可分为四大类：键值数据库（Redis、Memcached）适合缓存与会话；列族数据库（HBase、Cassandra）适合海量稀疏数据；文档数据库（MongoDB、CouchDB）适合半结构化 JSON；图数据库（Neo4j、JanusGraph）适合关系网络分析。CAP 定理指出一致性、可用性、分区容错三者不可兼得，NoSQL 通常采用 BASE（基本可用、软状态、最终一致）原则。架构师需要根据数据特征、访问模式、一致性要求做合理选型，并搭配 SQL 数据库形成"多模存储"架构。

请围绕"**论 NoSQL 数据库的应用**"论述以下三个问题：

1. **概要叙述**你参与设计与开发的软件项目以及你担任的主要工作（约 300 字应答）。
2. **简要说明** NoSQL 四大类型的特征、适用场景，以及 CAP/BASE 理论（约 400 字应答）。
3. **详细论述**你在项目中如何针对不同业务场景选用多种 NoSQL，遇到的挑战与最终效果（约 1500-1800 字应答）。

**【提纲式参考答案】**（约 1400 字提纲）

#### 摘要框架（300 字模板）

"我于 {2023} 年参与了 {社交关系平台 / 内容推荐 / 物联网监控} 系统建设，担任 {数据架构师}。系统服务 {2000 万 DAU / 日增 50 亿条数据 / 关系图谱 80 亿边}。本文论述多模 NoSQL 在该项目的选型与落地：Redis Cluster 做热点缓存（命中率 95%）、HBase 存用户行为明细（PB 级）、MongoDB 存半结构化内容（灵活 Schema）、Neo4j 做社交关系推荐（毫秒级深度遍历）、ClickHouse 做实时 OLAP。最终查询 QPS 15 万、关系遍历 P99 30ms、存储成本降 50%。"

#### 一、项目背景（350 字提纲）

- **业务背景**：社交+内容平台，用户、内容、关系、行为四类数据规模 PB 级
- **团队规模**：18 人（DBA 3 + 开发 12 + 架构 3）
- **关键质量属性**：吞吐、延迟、扩展性、一致性、成本
- **业务约束**：DAU 2000 万、读写比 5:1、热点访问占 80% 流量

#### 二、核心理论（400 字提纲）

- NoSQL 四类：
  - 键值：Redis（高性能缓存）、Memcached（无持久化）
  - 列族：HBase（强一致 + HDFS）、Cassandra（最终一致 + 无主）
  - 文档：MongoDB（灵活 Schema、聚合管道）、CouchDB（多主复制）
  - 图：Neo4j（Cypher）、JanusGraph（HBase/Cassandra 后端）
- CAP 三选二：CP（HBase/Zookeeper）vs AP（Cassandra/Dynamo）
- BASE：基本可用、软状态、最终一致
- 一致性级别：强 / 因果 / 读自己写 / 单调读 / 最终

#### 三、实践论述（1500 字提纲，分 5 节）

##### 3.1 Redis Cluster — 热点缓存
- 16384 槽分片、6 节点 3 主 3 从
- 数据结构选型：String 用户会话、Hash 商品详情、ZSet 排行榜、Bitmap 签到
- Cache Aside 模式 + 缓存击穿/穿透/雪崩防护
- 量化：命中率 95%、P99 2ms

##### 3.2 HBase — 海量明细
- RowKey 设计：用户 ID 反转 + 时间戳，避免热点
- 列族 ≤ 3、TTL + 多版本
- Coprocessor 实现二级索引
- 量化：PB 级存储、写入 50 万/s

##### 3.3 MongoDB — 半结构化内容
- 副本集 PSS 三节点、按 hashed 分片
- 嵌入文档减少 Join
- 索引策略：复合索引 + TTL 索引
- 量化：写入 5 万/s、查询 P99 50ms

##### 3.4 Neo4j — 关系推荐
- 图模型：用户-关注-用户、用户-喜欢-内容
- Cypher 三度好友推荐
- 量化：80 亿关系、深度遍历 P99 30ms

##### 3.5 风险与应对（必有）
- 风险 1：多模存储一致性 → CDC（Debezium）双写 + 对账
- 风险 2：Redis 雪崩 → 错峰过期 + 多级降级 + 本地缓存
- 风险 3：HBase 热点 → RowKey 加盐 + 预分区

#### 四、总结与展望（250 字提纲）

- 项目结果：综合查询 QPS 15 万、缓存命中 95%、关系 P99 30ms、成本降 50%
- 经验教训：①不存在银弹，多模才是王道 ②CAP 必须按场景取舍 ③数据一致性靠 CDC + 对账，不能完全靠数据库
- 未来演进：HTAP（TiDB/OceanBase）减少多模复杂度、Vector DB 接入 AI 检索

**【加分关键词清单】**

| 类别 | 必写术语 |
|---|---|
| 理论术语 | NoSQL 四类、CAP、BASE、一致性级别、CRDT、向量时钟、Bloom Filter |
| 方法论 | Cache Aside、Sharding、Replica Set、Coprocessor、CDC、Cypher、RowKey 设计 |
| 量化范围 | DAU 2000 万 / QPS 15 万 / 命中率 95% / 关系 80 亿 / 存储 PB 级 / 节点 6 个 |
| 业界案例点缀 | Twitter Manhattan、Facebook Cassandra、LinkedIn Voldemort、阿里 Tair、字节 Abase |

**【评分维度对照表】**

| 维度 | 占比 | 评分要点 |
|---|---|---|
| 项目真实性 | 25% | 多类数据规模 / 业务读写比 / 团队配置 |
| 理论深度 | 25% | 四类 NoSQL 全 + CAP/BASE 准确 |
| 实践细节 | 35% | 每类 NoSQL 落地具体配置 + 选型有理由 |
| 文笔与结构 | 15% | 多模存储逻辑清晰 / 字数 ≥ 2500 |

**【避坑提醒】**

- ❌ 只用一种 NoSQL → ✅ 多模存储按场景选型（4 类至少出现 3 类）
- ❌ 不谈 CAP 取舍 → ✅ 每种 NoSQL 必须说明它在 CAP 中的位置
- ❌ Redis 当数据库用 → ✅ 缓存 + 持久化分清，主存数据放 MySQL/HBase
- ❌ 不谈一致性 → ✅ CDC/双写/对账机制必写
- ❌ RowKey 设计随便 → ✅ HBase RowKey 是性能命脉，必须讲反转/加盐/预分区
