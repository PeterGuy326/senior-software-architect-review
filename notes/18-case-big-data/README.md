# 18 · 案例：大数据架构（教材第 19 章）

## 核心概念

- **5V 特性**：Volume / Velocity / Variety / Value / Veracity
- **Lambda 架构**：Batch + Speed + Serving 三层
- **Kappa 架构**：仅流式（简化 Lambda）
- **数据湖** vs **数据仓库**：Schema-on-Read vs Schema-on-Write
- **Data Mesh**（数据网格，新兴）

## 技术栈

| 层 | 代表组件 |
|---|---|
| 采集 | Flume / Logstash / Canal |
| 存储 | HDFS / HBase / S3 |
| 计算（批） | MapReduce / Spark / Hive |
| 计算（流） | Flink / Spark Streaming / Storm |
| 消息 | Kafka / Pulsar |
| OLAP | Druid / ClickHouse / Doris |
| 调度 | Airflow / DolphinScheduler |

## 案例题常见问法

- Lambda vs Kappa 选型
- 数据倾斜如何解决
- 实时 + 离线一致性保证

## TODO

- [ ] 数据湖架构图
