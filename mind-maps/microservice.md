# 微服务与云原生脑图

```mermaid
mindmap
  root((微服务 + 云原生))
    设计原则
      DDD 领域驱动
        Bounded Context
        Aggregate 聚合根
        Domain Event
        Anti-Corruption Layer
      12-Factor App
        代码库 / 依赖 / 配置
        后端服务 / 构建发布运行
        进程 / 端口 / 并发
        易处理 / 开发生产对等
        日志 / 管理进程
      高内聚 低耦合
      围绕业务能力
      去中心化治理
      智能端点 哑管道
      故障容忍
      演进式设计
    通信
      同步 RPC
        gRPC HTTP/2
        Dubbo
        REST
      异步 MQ
        Kafka
        RocketMQ
        RabbitMQ
      Service Mesh
        Istio
        Sidecar 模式
        Envoy
    治理
      服务注册发现
        Eureka / Nacos / Consul
      配置中心
        Apollo / Nacos
      API Gateway
        Kong / Spring Cloud Gateway
      熔断 降级
        Hystrix / Sentinel / Resilience4j
      限流
        令牌桶 / 漏桶
      链路追踪
        SkyWalking / Jaeger / Zipkin
      日志聚合
        ELK / Loki
      指标监控
        Prometheus / Grafana
    容器与编排
      Docker
        镜像 / 容器
        Dockerfile / Compose
      Kubernetes
        Pod / Service / Ingress
        Deployment / StatefulSet
        ConfigMap / Secret
        Volume / PV / PVC
        Namespace / RBAC
        Operator / CRD
      镜像仓库 Harbor
    部署与发布
      CI/CD Pipeline
      蓝绿部署
      金丝雀发布
      A/B 测试
      滚动更新
      回滚机制
    云原生
      CNCF 生态
      Serverless / FaaS
      IaC Terraform / Ansible
      GitOps ArgoCD / Flux
      可观测性 三柱
        Metrics
        Logs
        Traces
    数据
      Database per Service
      Saga / TCC 分布式事务
      事件溯源 Event Sourcing
      CQRS 读写分离
      最终一致性
```

## 单体 → SOA → 微服务演进

```mermaid
graph LR
    A[单体 Monolith<br/>简单 难扩展] --> B[垂直拆分<br/>按业务模块]
    B --> C[SOA + ESB<br/>中心化集成]
    C --> D[微服务<br/>独立部署 去中心]
    D --> E[Service Mesh<br/>基础设施下沉]
    E --> F[Serverless<br/>事件驱动 按需付费]
```

## 何时选微服务

```mermaid
graph TD
    Q{业务复杂度} -->|低 单产品| M[单体即可]
    Q -->|高 多团队| Big{团队规模}
    Big -->|< 10 人| MM[模块化单体]
    Big -->|10-50 人| MS[微服务]
    Big -->|> 50 人 多业务| MS2[微服务 + Service Mesh]
```

## K8s 核心对象关系

```mermaid
graph TB
    D[Deployment] -->|管理| RS[ReplicaSet]
    RS -->|创建| P[Pod]
    P -->|包含| C[Container]
    S[Service] -->|路由到| P
    I[Ingress] -->|外部入口| S
    P -->|挂载| CM[ConfigMap]
    P -->|挂载| Sec[Secret]
    P -->|挂载| V[Volume]
    V -.-> PVC[PVC] -.-> PV[PV]
```

## 速记口诀

- **DDD 四要素**：限界上下文 / 聚合根 / 领域事件 / 防腐层
- **12-Factor**：12 条戒律记不全没事，**配置外化 / 无状态 / 日志即流**这三条最关键
- **微服务通信**：同步用 gRPC，异步用 Kafka，治理用 Service Mesh
- **可观测三柱**：Metrics（聚合指标）/ Logs（事件流水）/ Traces（请求链路）
