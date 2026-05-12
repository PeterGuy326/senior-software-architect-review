# 数据库脑图

```mermaid
mindmap
  root((数据库))
    数据模型
      概念模型
        E-R 图
        实体 属性 联系
        1:1 / 1:N / M:N
      逻辑模型
        关系模型
        层次模型
        网状模型
        面向对象
      物理模型
        存储结构
        索引
    关系理论
      函数依赖
        平凡 / 非平凡
        完全 / 部分依赖
        传递依赖
        Armstrong 公理
          自反 增广 传递
      候选键 / 主键 / 外键
      闭包 与 最小函数依赖集
    范式
      1NF 属性不可分
      2NF 消除部分依赖
      3NF 消除传递依赖
      BCNF 主属性不依赖主属性
      4NF 消除多值依赖
      5NF 消除连接依赖
    事务 ACID
      原子性 Atomicity
      一致性 Consistency
      隔离性 Isolation
        读未提交
        读已提交
        可重复读
        串行化
      持久性 Durability
    并发控制
      锁
        共享锁 S
        排它锁 X
        意向锁 IS IX
        两阶段封锁 2PL
      多版本 MVCC
      时间戳排序
      乐观锁 / 悲观锁
      死锁预防 / 检测
    分布式数据库
      CAP 定理
      BASE 理论
      分库分表
        垂直 水平
        Sharding Key
      读写分离
      主从复制
      一致性哈希
    NoSQL
      Key-Value Redis
      Document MongoDB
      Column HBase Cassandra
      Graph Neo4j
      搜索 Elasticsearch
    数据仓库
      OLTP vs OLAP
      星型 / 雪花模型
      ETL / ELT
      数据湖 / 湖仓一体
```

## 范式分解决策树

```mermaid
graph TD
    A[原始关系 R] -->|属性是否原子| B{1NF}
    B -->|是| C{有无部分依赖?}
    C -->|有| D[分解消除部分依赖<br/>→ 2NF]
    C -->|无| E{有无传递依赖?}
    D --> E
    E -->|有| F[分解消除传递依赖<br/>→ 3NF]
    E -->|无| G{主属性是否依赖主属性?}
    F --> G
    G -->|否| H[BCNF 达成]
    G -->|是| I[进一步分解]
```

## 隔离级别 vs 并发问题

```mermaid
graph LR
    A[读未提交] -->|脏读 不可重复读 幻读| Bug
    B[读已提交] -->|不可重复读 幻读| Bug
    C[可重复读] -->|幻读 MySQL默认| Bug
    D[串行化] -->|无并发问题 性能最低| OK
```

## 索引选型

```mermaid
graph LR
    Q{查询模式} -->|等值/范围/排序| BTree
    Q -->|等值 + 高频| Hash
    Q -->|全文检索| Inverted[倒排索引]
    Q -->|地理位置| RTree
    Q -->|前缀匹配| Trie
    Q -->|大量列 OLAP| Columnar[列存]
```

## 速记口诀

- 范式：**1NF 原子 · 2NF 全依赖 · 3NF 非传递 · BCNF 主属性纯洁**
- 锁兼容：**S-S 兼容、S-X / X-X 互斥**
- 隔离 4 级：**读未 → 读已 → 可重复 → 串行**（MySQL InnoDB 默认可重复读）
- ACID 与 BASE：强一致 → 最终一致
