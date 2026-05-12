# 中间件（MQ / RPC / ESB / 事务 / 对象 / JMS / AMQP） · 12 题

> **高频考点**（每年 1-2 题）· **中间件分类**：**通信中间件（MOM/RPC）/ 事务中间件（TPM）/ 数据访问中间件 / 对象中间件 / 应用服务器 / 消息中间件 / 集成中间件（ESB）**· **MQ 对比**：RabbitMQ（AMQP，企业级）/ Kafka（高吞吐、流处理）/ RocketMQ（金融级、事务消息）/ ActiveMQ（JMS）/ Pulsar（云原生、存算分离）· **JMS（Java 规范）vs AMQP（跨语言协议）vs MQTT（IoT）vs STOMP**· **RPC 框架**：gRPC（Protobuf+HTTP/2）/ Dubbo / Thrift / Hessian · **对象中间件**：CORBA / DCOM / RMI / EJB · **ESB 与 SOA**

---

### 1. 关于**中间件的本质**，下列描述**错误**的是：

A. 中间件是位于操作系统与应用之间的软件层，为应用提供通用服务

B. 中间件屏蔽了底层异构性（OS、网络、硬件、数据库）

C. 中间件促进了应用的可移植性、互操作性、可扩展性

✅ **D. 中间件只能用于单机内部，不能跨网络**

**答案**：D
**解析**：中间件的**根本价值就是跨网络、跨平台、跨语言的互操作**——典型场景就是分布式异构环境下的应用集成。Gartner 定义：中间件是"位于平台（OS+DB+网络）和应用之间的通用服务的连接软件"。中间件 = **解耦 + 通信 + 服务**。

---

### 2. 关于 **MOM（Message-Oriented Middleware，面向消息的中间件）** 与 **RPC（远程过程调用）**，下列描述**错误**的是：

A. RPC 是**同步、点对点**调用，模拟本地函数调用语义

B. MOM 是**异步、解耦**通信，通过队列/主题中转消息

C. MOM 提供更好的**时间解耦、空间解耦、流量削峰**

✅ **D. MOM 性能一定高于 RPC，应优先选 MOM**

**答案**：D
**解析**：**RPC 在低延迟实时调用场景性能更好**（毫秒级，无中转开销）；**MOM 在吞吐量、削峰、异步、解耦场景更优**。选型原则：**强实时同步用 RPC（gRPC/Dubbo）；可异步、解耦、削峰用 MQ（Kafka/RocketMQ）**。两者互补、不是替代关系。微服务架构中两者都用。

---

### 3. 下列对**主流 MQ**的特征描述，**错误**的是：

A. **Kafka** 高吞吐（百万级 TPS）、顺序消息、日志型存储、流处理首选

B. **RabbitMQ** 基于 AMQP 协议、路由灵活（Exchange）、企业集成场景常用

C. **RocketMQ** 阿里开源、支持事务消息、定时消息、金融级稳定性

✅ **D. **ActiveMQ** 是 Apache 顶级项目、性能为 MQ 中最高、互联网公司主流选择**

**答案**：D
**解析**：**ActiveMQ 性能反而是主流 MQ 中较低的**——它是早期 JMS 标准实现的代表，**功能全但性能与吞吐量较弱**，已逐步被 ActiveMQ Artemis（新一代）或 Kafka/RocketMQ 取代。互联网公司主流是 **Kafka（日志/流）+ RocketMQ/RabbitMQ（业务消息）**。

---

### 4. 关于 **JMS（Java Message Service）** 与 **AMQP（Advanced Message Queuing Protocol）**，下列描述**错误**的是：

A. JMS 是 Java 的消息 API 规范、只能 Java 应用使用

B. AMQP 是**线缆级协议（wire-level）**、跨语言、跨平台

C. RabbitMQ 实现了 AMQP 0-9-1 协议

✅ **D. JMS 与 AMQP 是同层规范、可以无缝互换**

**答案**：D
**解析**：**JMS 是 API 规范（接口）**，**AMQP 是协议规范（线缆格式）**——层次不同。可以有"实现了 AMQP 协议、暴露 JMS API"的客户端，但反之不可。**JMS 两种模型**：**Queue（P2P 点对点，每条消息只被一个消费者消费）** 和 **Topic（发布/订阅，每条消息被所有订阅者消费）**。**AMQP 通过 Exchange + Queue + Binding 路由**，更灵活（fanout/direct/topic/headers）。

---

### 5. **RPC 框架**的核心组成，下列**不属于** RPC 必备要素的是：

A. 序列化/反序列化（Protobuf / JSON / Hessian）

B. 网络传输（HTTP / TCP / HTTP/2）

C. 服务注册与发现（ZK / Nacos / Eureka）

✅ **D. 关系数据库**

**答案**：D
**解析**：RPC 与 DB 无直接依赖。RPC 框架核心要素：**①接口定义（IDL：Protobuf/Thrift IDL）→ ②代理生成（Stub/Skeleton）→ ③序列化 → ④网络传输 → ⑤服务注册发现 → ⑥负载均衡 → ⑦容错（超时/重试/熔断）**。主流框架：**gRPC（Google、Protobuf+HTTP/2，多语言）/ Dubbo（Alibaba，Java 生态）/ Thrift（Facebook，跨语言）/ Hessian（轻量二进制）**。

---

### 6. 关于**对象请求代理中间件**，下列对应**错误**的是：

A. **CORBA**（OMG 标准）—— 跨语言、跨平台对象中间件，使用 IDL + ORB

B. **DCOM**（微软）—— Windows 平台分布式对象，已被 .NET Remoting / WCF 取代

C. **RMI**（Java）—— Java 平台间远程对象调用

✅ **D. **EJB** —— 微软的分布式对象规范，只能在 Windows 上运行**

**答案**：D
**解析**：**EJB（Enterprise JavaBeans）是 Java EE 规范，不是微软的**——由 Sun 提出，跨平台运行在任何符合 Java EE 的应用服务器（WebLogic、WebSphere、JBoss）上。EJB 三类：**Session Bean（会话）/ Entity Bean（实体，3.0 后被 JPA 替代）/ Message-Driven Bean（消息驱动）**。重型企业应用框架，现代项目多被 Spring 取代。

---

### 7. **ESB（Enterprise Service Bus，企业服务总线）** 的核心职责，下列描述**错误**的是：

A. 在异构系统间提供消息路由、协议转换、数据格式转换

B. 是 SOA（面向服务架构）的关键基础设施

C. 支持服务编排（Orchestration）和事件处理

✅ **D. ESB 是去中心化架构，没有任何中心组件**

**答案**：D
**解析**：**ESB 是中心化的总线**——所有服务通过总线交互，由总线做路由/转换/编排。**这恰恰是 ESB 被微服务质疑的原因**：单点、性能瓶颈、配置中心化。**微服务推崇"智能端点 + 哑管道"**——业务逻辑放服务里、通信通道只做转发（如轻量 MQ、HTTP）。所以业界从 SOA+ESB 演化到微服务+API Gateway+Service Mesh。

---

### 8. 关于 **API Gateway（API 网关）** 与 **ESB** 的区别，下列描述**错误**的是：

A. API Gateway 主要面向**对外暴露 API**——做认证、限流、路由、协议转换

B. ESB 主要面向**企业内部异构系统集成**——做服务编排、协议适配、数据转换

C. API Gateway 是微服务时代的产物，强调高性能、轻量级

✅ **D. API Gateway 完全替代 ESB 功能，新项目应一律选 API Gateway**

**答案**：D
**解析**：**两者解决问题不同、可共存**——API Gateway 在系统**边界**（南北流量）做统一入口；ESB 在系统**内部**做集成总线（东西流量）。微服务架构中**用 API Gateway 暴露对外、用 Service Mesh 处理内部通信**，ESB 在传统企业集成（连接 ERP/CRM/SAP/Mainframe）仍有价值。**新项目**：互联网类用 API Gateway，企业集成（多遗留系统）仍可用 ESB 或现代版（如 Camel、MuleSoft）。

---

### 9. 关于 **Kafka** 的核心机制，下列描述**错误**的是：

A. Topic 分 Partition，分区是并行单元；Partition 内消息有序、Partition 间无序

B. Producer 通过 key 决定 Partition；Consumer Group 内每个分区只被一个 Consumer 消费

C. 通过 ISR（In-Sync Replicas）+ acks=all 保证不丢消息

✅ **D. Kafka 消息消费后会立即从磁盘删除以释放空间**

**答案**：D
**解析**：**Kafka 消息消费后不删除**——按**保留策略**（默认 7 天 或 大小阈值）批量清理。这与传统 MQ（消费后删）的根本区别——**Kafka 本质是分布式日志（commit log）**，可重放、可多 Consumer Group 独立消费、可"时间穿越"重放历史。这是 Kafka 适合流处理和事件驱动架构的根本原因。

---

### 10. 在**消息中间件**中，**消息消费的两种语义**及其实现，下列描述**错误**的是：

A. **At-most-once（最多一次）**——发完不重试，可能丢消息

B. **At-least-once（至少一次）**——失败重试，可能重复消费 → 消费端需幂等

C. **Exactly-once（精确一次）**——理想态，分布式系统中难严格保证

✅ **D. 互联网 MQ 普遍默认 exactly-once 语义，开发者无需处理重复消费**

**答案**：D
**解析**：分布式系统中严格的 exactly-once 在通用网络下不可达——**At-least-once + 消费端幂等**是工业界主流稳定方案。Kafka 0.11+ 提供"事务性 exactly-once"也只在 Kafka 内部的"producer→broker→consumer"链路成立，跨业务系统仍需消费端做幂等去重。

---

### 11. 关于**消息中间件的"死信队列（DLQ）"**，下列描述**错误**的是：

A. 死信队列存放**多次消费失败、无法正常处理**的消息

B. 死信常见来源：消费超时、超过最大重试次数、消息过期、队列长度溢出

C. 应有专门的处理流程（人工介入 / 告警 / 补偿）

✅ **D. 进入死信队列的消息一定是 MQ Broker 自身的 bug 导致的**

**答案**：D
**解析**：**死信是业务/消费侧问题为主，与 Broker bug 无关**。常见原因：①消费逻辑有 bug 反复抛异常；②外部依赖（DB/第三方）持续不可用；③消息格式不对（兼容性问题）；④业务规则拒绝。**DLQ 治理实践**：①开告警（DLQ 增长 = 业务问题信号）；②自动重试 N 次再进 DLQ；③DLQ 消费器 + 人工处理工作台；④定期复盘 DLQ 找根因。

---

### 12. 关于**事务中间件（TPM, Transaction Processing Monitor）**，下列描述**错误**的是：

A. 典型代表：**Tuxedo（BEA/Oracle）、CICS（IBM 大型机）**

B. 提供高并发、高可靠的事务处理能力，常用于银行/电信核心系统

C. 支持 **XA 分布式事务**协调多个资源管理器

✅ **D. 在云原生微服务时代，TPM 已被微服务架构完全替代，不再使用**

**答案**：D
**解析**：**TPM 在传统金融、电信、政务的核心交易系统仍广泛使用**——银行的核心账户、电信的计费系统至今运行在 Tuxedo / CICS 上。这些系统**对极致可靠性和性能要求超高**，且历史投资巨大、稳定性高，**不会轻易迁移**。新业务可能上微服务，但核心交易保留 TPM 是常态——这就是"双模 IT（Bimodal IT）"模式。

---

## 速查表

### 中间件分类（Gartner / 教材）

| 类别 | 典型产品 |
|---|---|
| **数据访问中间件** | ODBC / JDBC / Hibernate |
| **远程过程调用 RPC** | gRPC / Dubbo / Thrift / Hessian |
| **消息中间件 MOM** | Kafka / RocketMQ / RabbitMQ / ActiveMQ / Pulsar |
| **对象请求代理 ORB** | CORBA / DCOM / RMI / EJB |
| **事务处理监控 TPM** | Tuxedo / CICS |
| **应用服务器** | WebLogic / WebSphere / Tomcat / JBoss |
| **企业服务总线 ESB** | MuleSoft / WSO2 / Camel / IBM IIB |
| **API 网关** | Kong / Apigee / Spring Cloud Gateway / Zuul |
| **服务网格** | Istio / Linkerd / Consul Connect |

### MQ 选型速查

| MQ | 吞吐 | 延迟 | 强项 | 典型场景 |
|---|---|---|---|---|
| **Kafka** | 百万级 TPS | 毫秒级 | 高吞吐、流处理、日志 | 大数据流、埋点、日志 |
| **RocketMQ** | 十万级 TPS | 毫秒级 | 事务消息、定时、金融级 | 电商、金融业务消息 |
| **RabbitMQ** | 万级 TPS | 微秒级 | 灵活路由、AMQP、易用 | 企业集成、任务队列 |
| **ActiveMQ** | 万级 TPS | 毫秒级 | JMS 标准、传统系统 | 传统 Java EE 项目 |
| **Pulsar** | 百万级 TPS | 毫秒级 | 存算分离、多租户、云原生 | 新一代云原生项目 |

### JMS 两种模型

```
P2P（Queue）：    Producer → [Queue] → Consumer（一对一，消费即删）
Pub/Sub（Topic）：Producer → [Topic] → Subscriber 1, 2, 3...（一对多）
```

### AMQP Exchange 类型

- **fanout**：广播到所有绑定 Queue
- **direct**：按 routing key 精确匹配
- **topic**：按 routing key 模式匹配（`*` `#` 通配）
- **headers**：按消息头匹配
