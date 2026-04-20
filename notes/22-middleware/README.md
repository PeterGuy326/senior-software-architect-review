# 22 · 中间件专题（🎯 案例 + ✍️ 论文极高频）

## 核心考点

### 一、消息队列（MQ）

- Kafka / RabbitMQ / RocketMQ / Pulsar 对比
- 应用：异步解耦、削峰填谷、可靠投递、顺序消息、事务消息
- 问题：消息丢失、重复消费、积压、顺序性

### 二、RPC 框架

- Dubbo / gRPC / Thrift
- 序列化：Protobuf / Hessian / JSON
- 服务治理：注册发现、负载均衡、熔断降级

### 三、缓存

- Redis / Memcached / Caffeine 对比
- 三大问题：穿透、击穿、雪崩
- 一致性模式：Cache Aside / Write Through / Write Behind
- 分布式锁、热点 key、大 key

### 四、数据库中间件

- 分库分表：ShardingSphere / MyCat
- binlog 订阅：Canal
- NewSQL：TiDB / OceanBase

### 五、服务注册与配置

- 注册中心：Nacos / Eureka / Consul / ZK / etcd
- 配置中心：Apollo / Nacos Config

### 六、网关

- Spring Cloud Gateway / Kong / APISIX / Envoy

### 七、分布式事务

- 2PC / 3PC / TCC / Saga / 本地消息表 / MQ 事务

## 速查

→ [cheatsheets/middleware-comparison.md](../../cheatsheets/middleware-comparison.md)
→ [cheatsheets/distributed-transactions.md](../../cheatsheets/distributed-transactions.md)
→ [cheatsheets/cache-patterns.md](../../cheatsheets/cache-patterns.md)

## 考频

- 综合知识：偶尔（概念题）
- **案例分析：几乎每年都有**（技术选型 / 问题诊断）
- **论文：极高频**（尤其可靠性、性能主题）
