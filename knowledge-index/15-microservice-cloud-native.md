# 知识点 15 · 微服务 + DDD + 云原生

## 一、核心概念

### 云原生 4 要素

**容器化** · **微服务** · **DevOps** · **持续交付**

### 12-Factor 应用

代码库 / 依赖 / 配置 / 后端服务 / 构建发布运行 / 进程 / 端口绑定 / 并发 / 易处理 / 开发生产一致 / **日志** / 管理进程

### DDD 核心概念

- **限界上下文**（Bounded Context）
- **聚合根 / 实体 / 值对象 / 领域服务**
- **分层**：表现 → 应用 → 领域 → 基础设施

### 微服务拆分原则

1. 单一职责
2. **限界上下文**
3. 业务能力驱动
4. **Database Per Service**
5. 团队自治（Two-Pizza）

### 治理组件栈

| 组件 | 代表 |
|---|---|
| 注册 | **Nacos** / Eureka |
| 网关 | **Spring Cloud Gateway** / Kong |
| 熔断限流 | **Sentinel** / Hystrix |
| 配置 | **Apollo** / Nacos |
| 追踪 | **SkyWalking** / Jaeger |
| 服务网格 | **Istio** |
| 编排 | **Kubernetes** |

## 二、关联资源

- 速查：[cheatsheets/middleware-comparison.md](../cheatsheets/middleware-comparison.md)
- 案例题型：[past-papers/case-types/05-microservice-refactor.md](../past-papers/case-types/05-microservice-refactor.md)
- 论文主题：[past-papers/paper-topics/05-microservice-cloud-native.md](../past-papers/paper-topics/05-microservice-cloud-native.md)

## 三、典型例题

### 📚 选择题 1（DDD）

下列**不属于** DDD 战术建模要素的是：
- A. 聚合根  B. 实体  C. 值对象  D. **ESB**

**答案**：D

### 📚 选择题 2（微服务特征）

下列**不是**微服务典型特征的是：
- A. 独立部署  B. 去中心化治理  C. **共享数据库**  D. 轻量通信

**答案**：C（**Database Per Service** 是红线）

### 📚 选择题 3（K8s 组件）

K8s 中负责维持 Pod 期望副本数的是：
- A. Service  B. **Deployment / ReplicaSet**  C. ConfigMap  D. Ingress

**答案**：B

### 🎯 案例填空：电商拆分

按 DDD 限界上下文拆分电商系统：**用户、商品、订单、支付、库存、物流**（6 个业务域）+ **配置中心、注册中心、网关、监控、日志**（5 个基础设施）。

### ✍️ 论文场景

"基于 **DDD 限界上下文**将单体拆分为 **10 个业务微服务 + 5 个基础服务**；通过 **Nacos（注册）+ Sentinel（熔断）+ SkyWalking（追踪）** 做治理；采用 **K8s + Istio** 做编排与服务网格。"
