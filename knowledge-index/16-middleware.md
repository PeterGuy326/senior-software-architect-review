# 知识点 16 · 中间件

## 一、核心概念

### 消息队列对比

| 维度 | Kafka | RabbitMQ | RocketMQ | Pulsar |
|---|---|---|---|---|
| 吞吐 | **百万级** | 万级 | 十万级 | 百万级 |
| 时延 | ms | **μs** | ms | ms |
| 可靠 | 高 | 高 | **金融级** | 高 |
| 特色 | 日志 / 流 | AMQP 丰富 | **事务消息 / 顺序** | 存算分离 |

### RPC 框架对比

| 框架 | 语言 | 协议 | 特点 |
|---|---|---|---|
| **gRPC** | 多语言 | HTTP/2 + protobuf | 云原生标配 |
| **Dubbo** | Java 主 | Dubbo/Triple | 阿里生态 |
| **Thrift** | 多语言 | 自定义 | Facebook |
| **REST** | 通用 | HTTP/JSON | 最通用 |

### 网关

- **Nginx**：反向代理、负载均衡
- **Spring Cloud Gateway**：Java 生态
- **Kong**：Lua 扩展、插件丰富
- **APISIX**：云原生、动态路由

### 服务注册与发现

| 组件 | 一致性模型 | 特点 |
|---|---|---|
| **Nacos** | AP + CP 可切换 | 阿里出品，主流 |
| **ZooKeeper** | CP | 一致性强 |
| **Consul** | CP | Multi-DC |
| **Eureka** | AP | Netflix，简单 |

## 二、关联资源

- 速查：[cheatsheets/middleware-comparison.md](../cheatsheets/middleware-comparison.md)
- 案例题型：[past-papers/case-types/06-messaging-caching.md](../past-papers/case-types/06-messaging-caching.md)

## 三、典型例题

### 📚 选择题 1（MQ 选型）

金融交易要求**零消息丢失 + 事务消息**，应选：
- A. Kafka  B. RabbitMQ  C. **RocketMQ**  D. ActiveMQ

**答案**：C

### 📚 选择题 2（注册中心）

要求**金融级强一致**，应选：
- A. Eureka  B. Nacos AP  C. **ZooKeeper / Nacos CP**  D. Redis

**答案**：C

### 📚 选择题 3（RPC 性能）

gRPC 性能高的主要原因：
- A. HTTP/1.1  B. **HTTP/2 多路复用 + protobuf 二进制**  C. JSON  D. 同步阻塞

**答案**：B

### 🎯 案例填空：消息可靠性三要素

| 要素 | 手段 |
|---|---|
| **不丢** | 生产 ACK + Broker 多副本持久化 + 消费手动 ACK |
| **不重** | 业务幂等（唯一键 / Redis setnx / 状态机） |
| **有序** | 单分区全局有序；按 key hash 局部有序 |

### ✍️ 论文场景

"选型 **RocketMQ** 作为核心消息中间件：同步双写 + 手动 ACK + 本地幂等表，实现 **at-least-once + 业务幂等 = exactly-once** 的效果。"
