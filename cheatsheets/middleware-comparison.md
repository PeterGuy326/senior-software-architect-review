# 中间件对比速查（🎯 案例 + ✍️ 论文极高频）

## 一、消息队列（MQ）对比

| 维度 | **Kafka** | **RabbitMQ** | **RocketMQ** | **Pulsar** | **ActiveMQ** |
|---|---|---|---|---|---|
| 开发语言 | Scala/Java | Erlang | Java | Java | Java |
| 协议 | 自定义 | AMQP / STOMP / MQTT | 自定义 | 自定义 | JMS / AMQP |
| 吞吐量 | **极高**（百万级/s） | 万级/s | 十万级/s | 极高 | 万级/s |
| 延迟 | ms 级 | μs 级（最低） | ms 级 | ms 级 | ms 级 |
| 可靠性 | 高（副本） | 高 | **极高**（金融级） | 极高 | 中 |
| 顺序消息 | 分区内有序 | 队列有序 | **严格顺序** | 支持 | 一般 |
| 事务消息 | 支持 | 不支持 | **原生支持** | 支持 | 不支持 |
| 延迟消息 | 需自实现 | 插件 | **原生支持** | 原生 | — |
| 典型场景 | 大数据日志、流处理 | 企业应用、异步解耦 | 电商交易、金融 | 云原生、多租户 | 传统企业 |

## 二、RPC 框架对比

| 框架 | 语言 | 协议 | 序列化 | 特点 |
|---|---|---|---|---|
| **Dubbo** | Java | Dubbo/HTTP/gRPC | Hessian/JSON/PB | 阿里开源，Java 生态 |
| **gRPC** | 多语言 | HTTP/2 | Protobuf | Google，跨语言 |
| **Thrift** | 多语言 | 二进制 | Thrift IDL | Facebook，高性能 |
| **Spring Cloud** | Java | HTTP/REST | JSON | 生态完整 |

## 三、缓存对比

| 维度 | **Redis** | **Memcached** | **Caffeine**（本地） |
|---|---|---|---|
| 数据结构 | 丰富（String/Hash/List/Set/ZSet/Stream） | 仅 KV | — |
| 持久化 | RDB + AOF | 不支持 | 进程内 |
| 分布式 | Cluster / 主从 / 哨兵 | 客户端分片 | 否 |
| 事务 | 支持（MULTI/EXEC） | 不支持 | — |
| 脚本 | Lua | — | — |
| 内存管理 | LRU / LFU / TTL | LRU | W-TinyLFU |
| 典型场景 | 会话、排行、分布式锁、消息 | 简单缓存 | JVM 本地缓存 |

## 四、数据库中间件

| 中间件 | 用途 |
|---|---|
| **ShardingSphere** | 分库分表、读写分离（推荐） |
| **MyCat** | 分库分表（老牌） |
| **Vitess** | MySQL 集群（YouTube 开源） |
| **TiDB** | 分布式 NewSQL |
| **Canal** | MySQL binlog 订阅 |

## 五、服务注册与发现

| 中间件 | 一致性 | 特点 |
|---|---|---|
| **Eureka** | AP | Netflix，简单，已停止更新 |
| **Consul** | CP | HashiCorp，支持多数据中心 |
| **Nacos** | AP/CP 可切 | 阿里，配置 + 注册一体 |
| **ZooKeeper** | CP | 老牌，写性能一般 |
| **etcd** | CP | Kubernetes 标配 |

## 六、API 网关

| 网关 | 语言 | 特点 |
|---|---|---|
| **Spring Cloud Gateway** | Java | Spring 生态 |
| **Zuul** | Java | Netflix 老牌（Zuul 2 响应式） |
| **Kong** | Lua + Nginx | 插件丰富，企业级 |
| **Apache APISIX** | Lua + Nginx | 动态路由、云原生 |
| **Envoy** | C++ | CNCF，Service Mesh 数据面 |

## 七、注册中心 / 配置中心 / 服务网格 生态图

```
服务注册发现：Nacos / Eureka / Consul / etcd
配置中心：Apollo / Nacos Config / Spring Cloud Config
网关：Spring Cloud Gateway / Kong / APISIX
熔断限流：Sentinel / Hystrix / Resilience4j
链路追踪：SkyWalking / Jaeger / Zipkin
日志收集：ELK / Loki
监控：Prometheus + Grafana
服务网格：Istio / Linkerd
```

## 八、中间件选型答题模板（案例 + 论文通用）

当题目问"选 Kafka 还是 RabbitMQ"，按这 5 点写：

1. **业务特征**：数据量大小、是否要求顺序、是否事务
2. **性能要求**：吞吐量 vs 延迟优先
3. **可靠性要求**：金融级（RocketMQ/事务）vs 一般（Kafka）
4. **团队技能**：已有栈
5. **成本**：运维复杂度、硬件成本
