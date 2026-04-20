# 案例题型 09 · 大数据 / Web 架构设计

> 中频题型（新增趋势），近年考频上升，25 分。

## 考点分布

- 大数据**Lambda / Kappa** 架构选型
- 流式 vs 批处理
- NoSQL 选型（键值 / 列族 / 文档 / 图）
- Web 高并发架构（CDN / 反向代理 / 集群）
- 数据湖 vs 数据仓库

## 大数据架构核心

### Lambda vs Kappa

| 维度 | **Lambda** | **Kappa** |
|---|---|---|
| 层次 | 批 + 速度双层 | **仅流式** |
| 代表 | Hadoop + Storm/Flink | **Flink 统一** |
| 优势 | 准确 | **简化** |
| 劣势 | 两套代码 | 回填慢 |

### 大数据技术栈

| 环节 | 技术 |
|---|---|
| **采集** | Flume / Logstash / **Canal**（CDC） |
| **消息** | **Kafka** |
| **存储** | HDFS / S3 / **HBase** / **ClickHouse** |
| **计算批** | **Spark** / MapReduce |
| **计算流** | **Flink** / Storm |
| **OLAP** | **ClickHouse** / Druid / Kylin |
| **调度** | Airflow / DolphinScheduler |

### NoSQL 选型

| 类型 | 代表 | 适用 |
|---|---|---|
| 键值 | **Redis** | 缓存、排行榜 |
| 列族 | **HBase** / Cassandra | 海量稀疏数据（日志、IoT） |
| 文档 | **MongoDB** | 半结构化 JSON |
| 图 | **Neo4j** / JanusGraph | 社交、金融反欺诈 |
| 时序 | **InfluxDB** / TDengine | IoT、监控 |
| 搜索 | **Elasticsearch** | 全文检索 |

## Web 高并发架构

### 标准 4 层

```
客户端 → CDN → 接入层（Nginx/LVS）→ 应用层（微服务）
                                    → 数据层（缓存 + 库）
```

### 关键优化手段

| 层 | 优化 |
|---|---|
| **CDN** | 静态资源加速 |
| **接入** | LVS + Nginx + 限流（令牌桶） |
| **应用** | 集群 + 无状态 + 水平扩 |
| **缓存** | 多级（本地 Caffeine + Redis） |
| **DB** | 主从 + 分库分表（ShardingSphere） |
| **搜索** | ES |
| **异步** | MQ 削峰填谷 |

## 答题模板

### 问题 1：给出大数据架构

**标准答法**：
```
采集：业务日志 → Flume；DB 变更 → Canal
缓冲：Kafka（万级 QPS 削峰）
实时：Flink 流式计算 → 写入 ClickHouse
离线：Spark 夜间批处理 → HDFS / Hive
存储：冷数据 HDFS + 热数据 HBase + 实时查 ClickHouse
服务：Dubbo / gRPC 对外提供 API
调度：Airflow 管理批作业
治理：元数据（Atlas）+ 血缘 + 质量
```

### 问题 2：Lambda vs Kappa 选型

**套路**：
- 业务要求**历史回溯 + 实时**且接受复杂度 → **Lambda**
- 业务**主要看实时** + 简化运维 → **Kappa**
- 具体看**团队 Flink 成熟度**

### 问题 3：NoSQL 选型

**套路表**（答题时贴合场景）：
```
- 用户画像（海量稀疏）→ HBase
- 订单 JSON 文档 → MongoDB
- 社交关系 → Neo4j
- 实时热榜 → Redis
- IoT 监控 → InfluxDB
- 全文搜索 → Elasticsearch
```

### 问题 4：Web 高并发承载

**套路**：
```
QPS 10 万如何承载？
1. 接入层：Nginx 7 层 + LVS 4 层 → 5 万 QPS / 节点 × N 节点
2. 应用：无状态 + 集群 + 限流 1k QPS / 实例
3. 缓存：Redis Cluster 10 万 QPS / 分片 × 10 分片
4. DB：主从读写分离 + 分库分表
5. 异步：RocketMQ 削峰，秒级消化突增
```

## 万能高分句

- "采用 **Lambda 架构**：批层 Spark 保证准确，速度层 Flink 实时计算，**相互校正**"
- "OLAP 查询引擎选 **ClickHouse**，单查询 **亚秒级**，支持 **100 亿行**明细"
- "分库分表基于 **ShardingSphere**，按**用户 ID 哈希 64 库 × 8 表**，单表 < 500 万行"
- "通过 **CDN + 多级缓存 + 异步削峰** 支撑**双 11 峰值 QPS 50 万**"

## 常见陷阱

| ❌ | ✅ |
|---|---|
| 只讲 Hadoop | 必须 **实时 + 离线** 结合 |
| NoSQL 一把梭 | **按数据结构 + 场景** 选型 |
| 无治理 | **元数据 / 血缘 / 质量** 是核心 |
| Web 只讲缓存 | **接入 + 应用 + 缓存 + DB** 全链路 |
| 不谈容量估算 | QPS / TPS / 存储 要**量化**到分片 |
