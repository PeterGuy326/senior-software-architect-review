# DevOps / CI/CD 速查表

## DevOps 核心理念

| 维度 | 含义 |
|---|---|
| **文化** | Dev + Ops 一体化，消除部门墙 |
| **自动化** | 构建/测试/部署/监控全链路自动化 |
| **度量** | 数据驱动改进（DORA 4 指标） |
| **共享** | 知识、责任、目标共享（You build it, you run it） |

## CI / CD / CD 三层

```
Continuous Integration (CI)        每次提交自动构建 + 测试
Continuous Delivery (CD-Delivery)  通过测试后随时可部署到生产（人工触发）
Continuous Deployment (CD-Deploy)  通过测试后自动部署到生产（无人工）
```

## CI/CD Pipeline 标准阶段

```mermaid
graph LR
    A[代码提交] --> B[构建 Build]
    B --> C[单元测试]
    C --> D[静态扫描<br/>SonarQube/SAST]
    D --> E[制品打包]
    E --> F[部署到测试环境]
    F --> G[集成测试]
    G --> H[安全扫描 DAST]
    H --> I[部署到预发]
    I --> J[性能/UAT]
    J --> K[生产部署]
    K --> L[健康检查/回滚]
```

## 部署策略对比

| 策略 | 原理 | 优点 | 缺点 | 适用 |
|---|---|---|---|---|
| **重建（Recreate）** | 停旧版 → 启新版 | 简单 | 有停机 | 内部系统、小流量 |
| **滚动（Rolling）** | 逐批替换实例 | 无停机、资源占用低 | 回滚慢、两版本共存 | K8s 默认 |
| **蓝绿（Blue-Green）** | 两套环境切流量 | 切换快、回滚秒级 | 资源 ×2 | 关键交易、金融 |
| **金丝雀（Canary）** | 灰度小流量验证 | 风险最低 | 流程长、需路由控制 | 互联网产品迭代 |
| **A/B 测试** | 同时上多版本对比 | 数据驱动 | 复杂 | 产品功能实验 |
| **影子流量** | 复制真实流量到新版只读 | 真实环境验证 | 副作用控制难 | 性能/正确性验证 |

## IaC（Infrastructure as Code）

| 工具 | 范式 | 强项 |
|---|---|---|
| **Terraform** | 声明式 | 多云、生态强、HCL |
| **Ansible** | 命令式 / SSH | 无 Agent、配置管理 |
| **Pulumi** | 声明式 + 真实编程语言 | 工程化好、强类型 |
| **CloudFormation** | 声明式 | AWS 原生 |
| **ARM / Bicep** | 声明式 | Azure 原生 |
| **Chef / Puppet** | 命令式 | 传统配置管理 |

## GitOps 核心原则

1. **声明式**：基础设施和应用配置都用声明式表达
2. **版本化**：所有变更进 Git，可审计、可回滚
3. **自动应用**：Agent 持续拉取 Git 状态、自动 reconcile
4. **持续监控**：偏差告警、自动修复

工具：**ArgoCD / Flux**

## DORA 4 大指标

| 指标 | 含义 | 精英标准 |
|---|---|---|
| **部署频率** Deployment Frequency | 多久部署一次 | 按需 / 每天多次 |
| **变更前置时间** Lead Time for Changes | 从提交到上线 | < 1 小时 |
| **变更失败率** Change Failure Rate | 部署后需修复的比例 | 0%-15% |
| **恢复时间** MTTR / Mean Time to Recovery | 故障平均恢复时间 | < 1 小时 |

## 制品 vs 构建 vs 配置

```
源代码 (Source) ─[构建]─► 制品 (Artifact, 不可变)
                            ├── 镜像（Docker Image）
                            ├── jar / war
                            └── npm tarball
制品 + 配置（ConfigMap/Secret） ─[部署]─► 运行实例
```

**关键原则**：**Build once, deploy many**——一个制品流转所有环境，只换配置，不重新构建。

## 常用工具栈

| 环节 | 工具 |
|---|---|
| 版本控制 | Git / GitHub / GitLab / Bitbucket |
| CI 平台 | Jenkins / GitLab CI / GitHub Actions / CircleCI / Drone / Tekton |
| 构建 | Maven / Gradle / npm / Docker Buildx |
| 制品库 | Nexus / Artifactory / Harbor（容器） |
| 配置管理 | Ansible / Chef / Puppet / SaltStack |
| 编排 | Kubernetes / Docker Swarm / Nomad |
| 监控 | Prometheus / Grafana / Datadog / New Relic |
| 日志 | ELK (Elastic+Logstash+Kibana) / Loki / Fluentd |
| 追踪 | Jaeger / Zipkin / SkyWalking |
| 告警 | Alertmanager / PagerDuty / OnCall |
| 安全 | SonarQube (SAST) / OWASP ZAP (DAST) / Trivy（镜像扫描） |
| ChatOps | Slack / Teams + Hubot / Botkit |

## Serverless / FaaS

| 概念 | 说明 |
|---|---|
| **FaaS** | Function as a Service，函数级粒度（AWS Lambda、阿里 FC） |
| **事件驱动** | 由 HTTP/MQ/定时器/对象存储事件触发 |
| **冷启动** | 函数首次或空闲后调用需初始化，毫秒~秒级延迟 |
| **按需计费** | 按调用次数 + 执行时长 |
| **无状态** | 函数本身无状态，状态外置（DB/缓存/对象存储） |

### Serverless 适用 vs 不适用

| 适用 | 不适用 |
|---|---|
| 事件驱动 / 异步任务 | 长时间运行任务（> 15 分钟） |
| 流量波峰波谷大 | 持续稳定高负载（成本反而高） |
| 创业 / 早期 MVP | 对启动延迟敏感（实时交易） |
| 定时任务 / Webhook | 需要本地状态 / GPU |

## 经典口诀

- **CI**：每次提交自动构建测试
- **CD**：可一键随时上线 / 全自动上线
- **IaC**：基础设施像代码一样管理
- **GitOps**：Git 是唯一真理源
- **DORA 四指标**：频率 / 前置时间 / 失败率 / 恢复时间
- **蓝绿 vs 金丝雀**：蓝绿"切流量"、金丝雀"放流量"
