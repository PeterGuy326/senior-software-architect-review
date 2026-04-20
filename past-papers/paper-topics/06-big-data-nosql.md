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
