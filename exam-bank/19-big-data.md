# 大数据架构 · 20 题

> **高频考点**（每年 1-3 题）· Hadoop 生态（HDFS/MapReduce/YARN/Hive/HBase）· Spark/Flink 对比 · Lambda vs Kappa 架构 · 数据仓库 vs 数据湖 vs 湖仓一体 · OLTP vs OLAP · 星型/雪花模型 · ETL/ELT · NoSQL 四类选型 · CAP · 数据治理

---

### 1. 关于 HDFS 的体系结构，下列说法**错误**的是：

A. NameNode 负责管理文件系统的命名空间和数据块到 DataNode 的映射

B. DataNode 负责存储实际的数据块并周期性向 NameNode 上报块信息

C. 文件被切分为固定大小的数据块，默认保存 3 个副本

✅ **D. HDFS 适合存储海量小文件，且对低延迟随机访问有良好支持**

**答案**：D
**解析**：HDFS 为「一次写入、多次读取」的大文件批处理场景设计，海量小文件会撑爆 NameNode 内存，且其面向高吞吐而非低延迟随机访问；低延迟随机读写应选 HBase。

---

### 2. HDFS 中真正保存文件元数据（目录树、文件到块、块到 DataNode 的映射）的是：

✅ **A. NameNode**

B. DataNode

C. SecondaryNameNode

D. JournalNode

**答案**：A
**解析**：NameNode 管元数据，DataNode 存数据块；SecondaryNameNode 只负责定期合并 fsimage 与 editlog，不是热备；JournalNode 用于 HA 模式下共享 editlog。

---

### 3. MapReduce 作业的执行流程，正确的顺序是：

A. Reduce → Shuffle → Map

✅ **B. Map → Shuffle → Reduce**

C. Map → Reduce → Shuffle

D. Shuffle → Map → Reduce

**答案**：B
**解析**：Map 阶段对输入分片并行产出键值对；Shuffle 阶段做分区、排序、合并并把同一 key 的数据拉取到对应 Reduce；Reduce 阶段做聚合输出。Shuffle 是 Map 和 Reduce 之间的桥梁。

---

### 4. 在 YARN 中，负责整个集群**全局资源调度**的组件是：

✅ **A. ResourceManager**

B. NodeManager

C. ApplicationMaster

D. Container

**答案**：A
**解析**：ResourceManager 负责全局资源管理与调度；NodeManager 管理单个节点的资源与容器；ApplicationMaster 负责单个应用的任务协商与监控；Container 是 CPU/内存等资源的封装单位。

---

### 5. 关于 Hive 的描述，下列**错误**的是：

A. Hive 提供类 SQL 的查询语言 HiveQL，本质是「SQL on Hadoop」

B. Hive 常被用作离线数据仓库，底层可基于 HDFS 存储

C. Hive 的元数据（表结构、分区等）通常存放在 MySQL 等关系库中

✅ **D. Hive 是面向高并发、毫秒级响应的联机事务处理（OLTP）系统**

**答案**：D
**解析**：Hive 把 HiveQL 翻译为 MapReduce/Tez/Spark 作业执行，适合海量数据的离线批量分析（OLAP 倾向），延迟高、不支持高并发事务，不能当 OLTP 业务库用。

---

### 6. 下列关于 HBase 的说法，**正确**的是：

A. HBase 是关系型数据库，支持完整的多表 JOIN 和事务

B. HBase 不依赖任何分布式文件系统，自带存储引擎

✅ **C. HBase 是基于 HDFS 的列族（面向列）NoSQL 数据库，适合海量数据的随机读写**

D. HBase 的查询性能与 RowKey 设计无关

**答案**：C
**解析**：HBase 数据存于 HDFS、依赖 ZooKeeper 协调，按「行键 + 列族」组织，擅长海量稀疏数据的随机读写（用户画像宽表、日志、IoT），但不擅长复杂多表 JOIN；RowKey 设计直接决定读写性能与是否产生热点。

---

### 7. 关于 Spark 相比 MapReduce 更快的原因，下列说法**错误**的是：

A. Spark 基于内存计算，中间结果尽量驻留内存，减少磁盘 I/O

B. Spark 用 DAG 调度，可对宽窄依赖做流水线和优化

C. Spark 对迭代式计算（如机器学习、图计算）效率明显更高

✅ **D. Spark 完全没有 Shuffle 过程，因此一定比 MapReduce 快**

**答案**：D
**解析**：Spark 在宽依赖（如 groupByKey、join）处同样会触发 Shuffle，并非「没有 Shuffle」；它的优势在于内存缓存、DAG 优化、避免 MR 多个作业间反复落盘。

---

### 8. Spark 生态中，**不属于** Spark 内置组件的是：

A. Spark SQL（结构化数据处理）

B. Spark Streaming（微批流处理）

C. MLlib（机器学习库）

✅ **D. ZooKeeper（分布式协调服务）**

**答案**：D
**解析**：Spark 四大组件是 Spark SQL、Spark Streaming（微批）、MLlib、GraphX；ZooKeeper 是独立的分布式协调服务，不属于 Spark。

---

### 9. 下列计算引擎中，最符合「真正的流式处理（事件时间 + 水印 + 强状态 + Exactly-Once）」的是：

A. MapReduce

B. Spark Core

C. Spark Streaming

✅ **D. Flink**

**答案**：D
**解析**：Spark Streaming 本质是微批（Micro-Batch），延迟较高；Flink 是原生流式引擎，支持事件时间与水印（Watermark）、有状态计算（Checkpoint）、低延迟（毫秒至亚秒级）和 Exactly-Once 语义，并支持流批一体。

---

### 10. 在典型大数据采集与处理链路中，Kafka 主要承担的角色是：

A. 分布式文件存储，替代 HDFS

B. 联机分析查询引擎，替代 ClickHouse

✅ **C. 数据采集与计算之间的消息缓冲，提供削峰、解耦与回放能力**

D. 资源调度器，替代 YARN

**答案**：C
**解析**：Kafka 作为高吞吐分布式消息系统，位于「采集端（Flume/CDC）」与「计算端（Spark/Flink）」之间，起到流量削峰、上下游解耦、数据可重放（消费位点回退）的中枢作用。

---

### 11. Lambda 架构由哪三层构成？

✅ **A. 批处理层 + 速度层 + 服务层**

B. 采集层 + 计算层 + 展示层

C. 接入层 + 应用层 + 数据层

D. ODS 层 + DWD 层 + ADS 层

**答案**：A
**解析**：Lambda 架构 = 批处理层（Batch Layer，全量精确、T+1，作为「真相之源」）+ 速度层（Speed Layer，增量实时、牺牲精度换低延迟）+ 服务层（Serving Layer，合并批与流结果对外查询）。画 Lambda 漏掉服务层是严重失分点。

---

### 12. 关于 Lambda 架构与 Kappa 架构的对比，下列说法**正确**的是：

A. Kappa 架构保留批处理层，去掉速度层

✅ **B. Kappa 架构只保留流处理层，用「流重放历史数据」代替批处理**

C. Lambda 架构比 Kappa 架构运维更简单、代码更少

D. Kappa 架构在任何场景下都优于 Lambda 架构

**答案**：B
**解析**：Kappa 只保留一套流处理链路，需要重算历史时靠从消息系统（如 Kafka 长保留）重放数据完成，省掉了批层、消除了双套代码；但当历史数据规模达 PB 级时重放成本高，长周期复杂业务仍常用 Lambda 作为阶段性方案。

---

### 13. 关于数据仓库（DW）四大特征，下列**不属于**的是：

A. 面向主题（Subject-Oriented）

B. 集成的（Integrated）

C. 反映历史变化（Time-Variant）

✅ **D. 实时高频在线更新（Real-Time & Frequently Updated）**

**答案**：D
**解析**：数据仓库四特征是「面向主题、集成、相对稳定（非易失，Non-Volatile）、反映历史变化（随时间变化）」。它以批量加载为主、不做高频在线更新，因此不是实时系统。

---

### 14. 数据湖（Data Lake）与数据仓库（Data Warehouse）的核心区别在于：

✅ **A. 数据湖采用 Schema-on-Read（读时定义结构），数据仓库采用 Schema-on-Write（写时定义结构）**

B. 数据湖只能存储结构化数据，数据仓库只能存非结构化数据

C. 数据仓库完全不需要任何 ETL/ELT 处理

D. 数据湖的查询性能在所有场景下都优于数据仓库

**答案**：A
**解析**：数据湖先把原始数据（结构化、半结构化、非结构化混合）低成本存下来，读取分析时才解释其结构（灵活，利于 AI/ML 与探索）；数据仓库在写入时就强制约束结构（严格、可信，利于 BI 报表）。

---

### 15. 关于湖仓一体（Lakehouse）与数据中台，下列说法**错误**的是：

A. 湖仓一体试图在数据湖之上提供 ACID 事务、Schema 演进、Time Travel 等能力，常见实现有 Iceberg、Hudi、Delta Lake

B. 湖仓一体的目标是「一份存储，既能做 BI 报表又能做机器学习」

C. 数据中台强调数据资产化与服务化，常以 OneID/OneModel/OneService 对外输出

✅ **D. 数据中台的本质是把所有业务系统的数据库直接合并成一个大型 OLTP 库**

**答案**：D
**解析**：数据中台是一套把跨域数据资产盘点、整合、加工并以数据 API/服务对外复用的体系（含数仓分层、标签体系、统一 ID 等），不是把业务库物理合并成一个 OLTP 大库。

---

### 16. 关于 OLTP 与 OLAP 的对比，下列说法**错误**的是：

A. OLTP 面向事务（增删改查），OLAP 面向多维分析（聚合、钻取）

B. OLTP 多采用范式化（如 3NF）设计减少冗余，OLAP 多采用星型/雪花维度模型

C. OLTP 多用行式存储，OLAP 多用列式存储以提升压缩比和聚合速度

✅ **D. OLTP 系统的数据量通常远大于 OLAP 系统**

**答案**：D
**解析**：OLAP 系统保存大量历史数据与多维聚合结果，数据量通常远大于只保存当前业务数据的 OLTP 系统。其余三项均正确，是 OLTP/OLAP 的标准对比点。

---

### 17. 关于维度建模中星型模型与雪花模型的区别，下列说法**正确**的是：

A. 星型模型有事实表，雪花模型没有事实表

✅ **B. 雪花模型的维度表进一步规范化（拆成多级层次），星型模型的维度表保持非规范化**

C. 星型模型只能拥有一张维度表

D. 雪花模型由于 JOIN 更少，查询一定比星型模型快

**答案**：B
**解析**：星型模型是一张事实表直连多张「扁平、未规范化」的维度表，冗余多但 JOIN 少、查询快；雪花模型把维度表按层次（如 区→市→省）规范化拆分，减少冗余但增加 JOIN、查询通常更慢。多张事实表共享维度则称星座（事实星座）模型。

---

### 18. 湖仓时代常把传统 ETL 改造为 ELT，其核心变化是：

✅ **A. 先抽取并把原始数据加载（Load）入湖，再用湖内算力做转换（Transform），即「算力下沉」**

B. 取消数据转换（Transform）环节

C. 转换必须在源端关系数据库内完成

D. 加载（Load）必须发生在转换（Transform）之后

**答案**：A
**解析**：ETL = Extract→Transform→Load，转换由中间引擎（独立 ETL 服务器）完成；ELT = Extract→Load→Transform，先把原始数据落入数据湖/数仓保留，再借助湖内分布式引擎（Spark/Flink/MPP）做转换，弹性更好、保留原始数据可重算。

---

### 19. 下列 NoSQL 数据库与典型适用场景的对应，**错误**的是：

A. Redis（键值）—— 热点缓存、会话存储、排行榜、计数器

B. MongoDB（文档）—— 半结构化内容、灵活 Schema、聚合管道

C. HBase / Cassandra（列族）—— 海量稀疏宽表、日志/IoT、随机读写

✅ **D. Neo4j（图）—— 严格事务的银行核心账务系统**

**答案**：D
**解析**：图数据库（Neo4j 等）擅长多跳关系遍历，典型场景是社交关系、金融反欺诈/资金链路追踪、推荐、知识图谱；银行核心账务这种强一致事务场景应选关系型数据库（Oracle/MySQL 等），不是图数据库。

---

### 20. 关于 CAP 定理及其在大数据/分布式系统中的体现，下列说法**错误**的是：

A. CAP 指一致性（C）、可用性（A）、分区容错性（P）三者不可同时完全满足

B. 分布式系统必须容忍网络分区（P），因此实际是在 C 与 A 之间取舍

C. ZooKeeper、HBase 偏向 CP，Cassandra、Dynamo 偏向 AP

✅ **D. 通过足够好的工程实现，一个分布式系统可以同时完全满足 C、A、P 三者**

**答案**：D
**解析**：CAP 三者不可兼得，发生网络分区时只能在「保证一致性而牺牲可用性（CP）」与「保证可用性而返回可能不一致的数据（AP）」之间二选一；与之配套的 BASE（基本可用 + 软状态 + 最终一致）是 NoSQL 对 ACID 强一致的妥协。数据治理（元数据、血缘、数据质量、安全脱敏、主数据 MDM）则是数据湖/数据中台保证数据可信可用的支撑体系。

---
