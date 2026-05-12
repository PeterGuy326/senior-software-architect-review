# 大数据架构脑图

```mermaid
mindmap
  root((大数据架构))
    特征 5V
      Volume 体量
      Velocity 速度
      Variety 多样
      Veracity 真实
      Value 价值
    存储
      HDFS 分布式文件
        NameNode 元数据
        DataNode 块存储
        副本 默认3
      对象存储
        S3 / OSS / Ceph
      列存储
        HBase
        Cassandra
        ClickHouse
      数据湖
        Hudi
        Iceberg
        Delta Lake
    计算
      批处理
        MapReduce 经典
        Spark 内存
        Hive SQL on Hadoop
      流处理
        Flink 真流
        Spark Streaming 微批
        Kafka Streams
        Storm 早期
      OLAP
        ClickHouse
        Doris / StarRocks
        Druid
        Kylin Cube
        Presto / Trino
    架构模式
      Lambda
        批处理层 准确
        速度层 实时
        服务层 合并
        缺点 双链路维护
      Kappa
        统一流处理
        简化运维
      湖仓一体
        Lakehouse
        Iceberg / Hudi / Delta
    数据仓库
      OLTP vs OLAP
      ETL / ELT
      维度建模
        星型模型
        雪花模型
        星座模型
      事实表 / 维度表
      分层
        ODS 贴源层
        DWD 明细
        DWS 汇总
        ADS 应用
      数据集市 / 数据中台
    NoSQL 分类
      Key-Value
        Redis Memcached
      Document
        MongoDB CouchDB
      Column
        HBase Cassandra
      Graph
        Neo4j JanusGraph
      Time-Series
        InfluxDB Prometheus
    生态组件
      Hadoop
      Spark
      Flink
      Kafka
      Zookeeper
      YARN 资源调度
      Hive Metastore
      Airflow / DolphinScheduler
    应用
      数据中台
      实时数仓
      用户画像
      推荐系统
      风控反欺诈
      机器学习平台
```

## Lambda vs Kappa 对比

```mermaid
graph TB
    subgraph Lambda
        L1[数据源] --> L2[批处理层<br/>HDFS+MR/Spark]
        L1 --> L3[速度层<br/>Storm/Flink]
        L2 --> L4[服务层<br/>合并展示]
        L3 --> L4
    end

    subgraph Kappa
        K1[数据源] --> K2[流处理<br/>Flink/Kafka Streams]
        K2 --> K3[服务层]
    end
```

| 维度 | Lambda | Kappa |
|---|---|---|
| 复杂度 | 高（双链路） | 低（单链路） |
| 准确性 | 高（批层兜底） | 依赖流处理稳定性 |
| 运维成本 | 高 | 低 |
| 历史回溯 | 自然支持 | 通过重放 Kafka 实现 |
| 适用 | 已有批处理积累 | 新建系统 / 实时要求高 |

## 数仓分层

```mermaid
graph TB
    ODS[ODS 贴源层<br/>原始数据] --> DWD[DWD 明细层<br/>清洗+维度退化]
    DWD --> DWS[DWS 汇总层<br/>主题汇总]
    DWS --> ADS[ADS 应用层<br/>面向报表/BI]
    DIM[DIM 维度表] -.-> DWD
    DIM -.-> DWS
```

## 选型决策

```mermaid
graph TD
    Q{数据特征} -->|大量结构化 离线分析| H[Hadoop + Hive]
    Q -->|实时流| F[Flink + Kafka]
    Q -->|交互式 OLAP 查询| CK[ClickHouse / Doris]
    Q -->|海量列式 随机读写| HB[HBase]
    Q -->|湖仓一体 ACID| LH[Iceberg / Hudi]
    Q -->|图关系| Neo[Neo4j]
    Q -->|时序| TS[InfluxDB / Prometheus]
```

## 速记口诀

- **5V**：体量 / 速度 / 多样 / 真实 / 价值
- **HDFS 三件套**：NameNode（元数据）/ DataNode（块）/ 副本数 3
- **Lambda 双链路、Kappa 单流**
- **数仓四层**：ODS → DWD → DWS → ADS
- **NoSQL 4 类**：KV / Doc / Col / Graph
