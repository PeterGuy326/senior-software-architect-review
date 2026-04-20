# 知识点 19 · 大数据架构

## 一、核心概念

### 5V 特征

**V**olume · **V**elocity · **V**ariety · **V**eracity · **V**alue

### Lambda vs Kappa

| 架构 | 层次 | 特点 |
|---|---|---|
| **Lambda** | 批（Spark）+ 速度（Flink） | 准确但维护两套代码 |
| **Kappa** | **仅流式（Flink 统一）** | 简化但回填慢 |

### NoSQL 四大类

| 类型 | 代表 | 适用 |
|---|---|---|
| 键值 | **Redis** | 缓存、会话 |
| 列族 | **HBase / Cassandra** | 海量稀疏（日志、IoT） |
| 文档 | **MongoDB** | 半结构化 JSON |
| 图 | **Neo4j** | 社交、反欺诈 |

### 数据湖 vs 数据仓库

| 维度 | 数据湖 | 数据仓库 |
|---|---|---|
| 数据形态 | 原始 / 多结构 | 结构化 |
| Schema | **Schema-on-Read** | Schema-on-Write |
| 用途 | AI / 探索 | BI / 报表 |
| 代表 | S3 + Iceberg / Delta | Hive / Greenplum |

### 技术栈速查

| 环节 | 代表 |
|---|---|
| 采集 | Flume / Canal |
| 消息 | **Kafka** |
| 批计算 | **Spark** / MapReduce |
| 流计算 | **Flink** |
| OLAP | **ClickHouse** / Druid / Kylin |
| 存储 | HDFS / HBase / S3 |
| 调度 | Airflow / DolphinScheduler |

## 二、关联资源

- 论文主题：[past-papers/paper-topics/06-big-data-nosql.md](../past-papers/paper-topics/06-big-data-nosql.md)
- 案例题型：[past-papers/case-types/09-big-data-architecture.md](../past-papers/case-types/09-big-data-architecture.md)

## 三、典型例题

### 📚 选择题 1（架构选型）

要求实时 + 准确回溯历史，应采用：
- A. Kappa  B. **Lambda**  C. 单点  D. MapReduce

**答案**：B

### 📚 选择题 2（NoSQL 选型）

社交关系网络分析应选：
- A. Redis  B. MongoDB  C. **Neo4j**  D. HBase

**答案**：C

### 📚 选择题 3（OLAP）

亚秒级分析 100 亿行明细，应选：
- A. MySQL  B. **ClickHouse**  C. HBase  D. Redis

**答案**：B

### 🎯 案例填空：日志分析管道

```
业务 → Flume → Kafka → Flink（实时）→ ClickHouse
                   └→ Spark（离线 T+1）→ HDFS / Hive
```

**治理三件套**：**元数据（Atlas）+ 血缘 + 数据质量**

### ✍️ 论文场景

"采用 **Lambda 架构**：批层 **Spark** 保证准确性，速度层 **Flink** 保证时效性；OLAP 选 **ClickHouse**，支持 **100 亿行明细的亚秒级查询**，日均处理 **100 亿条日志**。"
