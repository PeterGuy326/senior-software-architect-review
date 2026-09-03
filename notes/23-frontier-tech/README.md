# 23 · 前沿技术（大纲外补充专题）

> ⚠️ **本章为大纲外补充**。2022 官方大纲第 10 章"未来信息综合技术"仅包含 CPS / AI / 机器人 / 边缘计算 / 数字孪生 / 云计算+大数据 **6 项**，请见 [`../10-emerging-tech/`](../10-emerging-tech/)。
>
> 本目录收录那些**未在官方大纲第 10 章内**、但**在案例题（云原生 §4、通信 §7、安全 §8、大数据 §9）或论文题（"软件架构设计""系统设计""系统安全性"三大方向）中作为背景高频出现**的前沿技术。三种典型用法：
> 1. 综合知识科目一：偶尔以名词辨析题出现（1–2 分）；
> 2. 案例科目二：作为选做大题背景板（云原生案例、安全案例、大数据案例）；
> 3. 论文科目三：作为"改造/创新类"论题的技术选型素材。
>
> **考试作答铁律**：作答时若引用本章内容，务必明确说明是"扩展实践"，避免与大纲混淆。

---

## 一、云原生细化（衔接 [`../13-case-cloud-native/`](../13-case-cloud-native/) 案例章）

### 12-Factor App 十二要素

面向 SaaS/云原生的应用设计准则（Heroku 提出）：

| # | 要素 | 要点 |
|---|---|---|
| 1 | Codebase | 一份代码库，多份部署 |
| 2 | Dependencies | 显式声明依赖 |
| 3 | Config | 配置存于环境变量 |
| 4 | Backing Services | 后端服务视为附加资源 |
| 5 | Build/Release/Run | 严格三阶段分离 |
| 6 | Processes | 无状态进程 |
| 7 | Port Binding | 端口绑定对外暴露 |
| 8 | Concurrency | 通过进程模型水平扩展 |
| 9 | Disposability | 快速启动优雅关闭 |
| 10 | Dev/Prod Parity | 开发生产一致 |
| 11 | Logs | 日志作为事件流 |
| 12 | Admin Processes | 后台管理任务单独运行 |

### Kubernetes 核心对象速查

| 对象 | 作用 |
|---|---|
| **Pod** | 最小调度单元，一个或多个共享网络/存储的容器 |
| **Deployment** | 无状态工作负载，支持滚动/回滚 |
| **StatefulSet** | 有状态工作负载（DB、ZK），稳定网络标识 |
| **DaemonSet** | 每节点一个（日志/监控 Agent） |
| **Job / CronJob** | 一次性 / 定时任务 |
| **Service** | 稳定的服务访问入口（ClusterIP/NodePort/LB） |
| **Ingress** | 七层入口路由 |
| **ConfigMap / Secret** | 配置 / 敏感信息 |
| **PV / PVC / StorageClass** | 持久化存储 |
| **Namespace** | 逻辑隔离 |
| **HPA / VPA** | 水平/垂直自动伸缩 |

### Service Mesh 服务网格

- **数据面 + 控制面分离**；每 Pod 注入 **Sidecar 代理**（Envoy），接管服务间流量
- **Istio**（Google/IBM/Lyft）：控制面 Istiod，功能全，学习曲线陡
- **Linkerd**（CNCF 毕业）：轻量、Rust 数据面、上手快
- 解决问题：**微服务治理与业务代码解耦**（熔断/限流/重试/mTLS/灰度/可观测）
- **考点角度**：云原生案例题常问"为什么用 Service Mesh 替换 Spring Cloud Netflix 全家桶"

### Serverless / FaaS

- **FaaS 函数即服务**：AWS Lambda、阿里云 FC —— 只写函数，按调用次数计费
- **BaaS 后端即服务**：数据库/鉴权/存储作为托管服务
- **优势**：极致弹性、无运维、成本按用量；**劣势**：冷启动、状态管理难、供应商锁定
- **考点角度**：论文"高并发弹性架构"常见选型

### GitOps

- **Git 作为唯一可信真源**（Single Source of Truth）
- 声明式配置 + 自动 Reconcile（**ArgoCD、Flux**）
- 部署 = git push；回滚 = git revert
- 与传统 DevOps 区别：**Pull 模式**（集群拉取期望态） vs 传统 **Push 模式**

---

## 二、DevOps 与 CI/CD

> 详见 [`../../cheatsheets/devops-cicd.md`](../../cheatsheets/devops-cicd.md)。

### 核心实践栈

| 环节 | 主流工具 |
|---|---|
| 版本控制 | Git、GitLab、GitHub |
| CI 持续集成 | Jenkins、GitLab CI、GitHub Actions、Tekton |
| 制品仓库 | Nexus、Harbor、Artifactory |
| CD 持续部署 | ArgoCD、Flux、Spinnaker |
| IaC 基础设施即代码 | Terraform、Ansible、Pulumi |
| 配置管理 | Chef、Puppet、SaltStack |

### DORA 四大指标（考点必背）

1. **部署频率** Deployment Frequency
2. **变更前置时间** Lead Time for Changes
3. **变更失败率** Change Failure Rate
4. **服务恢复时间** MTTR / Time to Restore

### 考点角度

- 案例题：云原生改造案例常问"引入 DevOps 后度量指标怎么变"
- 论文："软件架构演化"方向可写 DevOps 支撑演化

---

## 三、可观测性 Observability 三支柱

| 支柱 | 数据类型 | 代表工具 |
|---|---|---|
| **Metrics 指标** | 数值时序（CPU/QPS/RT） | Prometheus + Grafana |
| **Logs 日志** | 离散事件文本 | ELK / EFK、Loki |
| **Traces 链路追踪** | 分布式调用链 Span | Jaeger、Zipkin、SkyWalking |

- **OpenTelemetry (OTel)**：CNCF 统一标准，覆盖 Metrics/Logs/Traces 数据模型 + SDK + Collector，**取代 OpenTracing 与 OpenCensus**
- 与传统监控区别：**监控回答"发生了什么"**；**可观测性回答"为什么发生"**（未知未知问题）
- **考点角度**：案例题问"如何定位分布式系统偶发慢调用" → Trace + Metric 联查

---

## 四、微服务治理

### 治理五大能力

| 能力 | 主流方案 |
|---|---|
| **服务注册发现** | Nacos、Eureka、Consul、ZooKeeper、etcd |
| **配置中心** | Nacos、Apollo、Spring Cloud Config |
| **熔断 / 限流 / 降级** | Sentinel、Hystrix（EOL）、Resilience4j |
| **API 网关** | Spring Cloud Gateway、Kong、APISIX、Zuul |
| **分布式追踪** | SkyWalking、Jaeger、Zipkin |

### 熔断 vs 限流 vs 降级（易混）

| 概念 | 触发条件 | 效果 |
|---|---|---|
| **熔断** Circuit Breaker | 失败率超阈值 | 快速失败，避免雪崩 |
| **限流** Rate Limit | QPS 超阈值 | 拒绝多余请求（漏桶/令牌桶） |
| **降级** Degrade | 系统压力大 / 依赖故障 | 关闭非核心功能，保核心链路 |

### 考点角度

- 案例题：SOA/云原生大题必问服务治理方案选型
- 论文："SOA 及分布式系统总体设计"方向常写

---

## 五、信创与国产化替代（案例常见背景）

### 全栈国产替代对照

| 层次 | 国产方案 |
|---|---|
| **CPU** | 鲲鹏（ARM）、飞腾（ARM）、龙芯（LoongArch）、海光/兆芯（x86 授权）、申威 |
| **服务器 OS** | 麒麟 KylinOS、统信 UOS、openEuler、openAnolis |
| **桌面 OS** | 麒麟桌面、统信 UOS、鸿蒙 HarmonyOS |
| **数据库** | 达梦 DM、GaussDB（华为）、OceanBase（蚂蚁）、TiDB、人大金仓 KingbaseES、南大通用 GBase |
| **中间件** | 东方通 TongWeb、金蝶 Apusic、宝兰德 |
| **虚拟化 / 云** | 华为 FusionCompute、深信服、阿里飞天、腾讯 TStack |
| **办公套件** | WPS、永中 Office |

### 考点角度

- 案例题：**政务云 / 金融行业**案例背景（"该系统需符合信创要求"）—— 数据库/OS 选型必答国产
- 论文：可作为"约束条件"素材

---

## 六、零信任安全架构 Zero Trust（对接 [`../17-case-security/`](../17-case-security/)）

### 核心理念

**"Never Trust, Always Verify"** —— 打破"内网可信"假设，每次访问都验证身份、设备、上下文。

### 三大原则（NIST SP 800-207）

1. **验证并持续验证**：每个请求独立鉴权，不基于位置
2. **最小权限**：动态权限、按需授权（Just-In-Time）
3. **假设已被攻破**：微隔离、纵深防御、可疑立即阻断

### 关键组件（BeyondCorp / SDP 架构）

- **策略引擎 PE**、**策略管理器 PA**、**策略执行点 PEP**
- **身份中心 IdP**（SSO / MFA）
- **设备状态评估**（EDR/端点合规）
- **微隔离 Micro-Segmentation**

### 与传统边界防御对比

| 维度 | 边界防御 | 零信任 |
|---|---|---|
| 信任模型 | 内网可信 | 默认不信任 |
| 边界 | 网络边界（防火墙） | 身份边界 |
| 授权 | 一次授权长期使用 | 每次请求动态评估 |
| 适用 | 传统企业内网 | 云 / 远程办公 / SaaS |

### 考点角度

- 案例题：**安全案例大题**（§8）背景板，问"如何设计新一代访问控制"
- 论文："系统安全性和保密性设计"方向直接可写

---

## 七、AIGC / 大模型工程化（⚠️ 2022 官方大纲未点名）

> **重要声明**：AIGC 与大模型未被 2022 版官方大纲单独列项，但 2026 上半年回忆版已出现向量数据库、多模态大模型、Transformer、世界模型、知识图谱和 AI 安全等题面。应把它视为**新增考情信号**，同时继续与官方大纲的 AI、云计算和大数据知识域区分。

### 大模型应用架构典型分层

```
用户 → Prompt 网关 → Agent 编排 → LLM 推理服务 → 向量库 / 工具 / RAG 知识库
                      ↑                      ↑
                     可观测/审计            微调模型仓库
```

### 关键技术要点

| 技术 | 说明 |
|---|---|
| **RAG 检索增强生成** | Query → Embedding → 向量库检索 → 拼接上下文 → LLM 生成；解决幻觉、时效性、私域知识 |
| **向量数据库** | Milvus、Pinecone、Qdrant、pgvector；存储 embedding 支持相似度检索 |
| **Prompt 工程** | Zero-shot / Few-shot / CoT 思维链 / ReAct |
| **模型微调** | LoRA / QLoRA / P-Tuning（PEFT 参数高效微调） |
| **模型服务化** | vLLM、TGI、TensorRT-LLM、Triton Inference Server |
| **Agent 架构** | Planner + Executor + Memory + Tools；ReAct / AutoGPT / LangGraph 编排 |
| **MLOps** | 数据管理 → 训练 → 评估 → 部署 → 监控（数据漂移 / 模型漂移）→ 持续训练 |

### 考点角度

- 综合知识：掌握 Transformer、自注意力、知识图谱本体、多模态对齐和常见 AI 安全风险的概念辨析
- 案例题：可能以推荐、知识图谱、AIoT 或智能测试为背景，最终仍考分层、数据、性能、可靠性和安全权衡
- 论文：2026 上半年回忆版出现向量数据库和多模态大模型方向；必须结合真实项目，不能只堆模型名词
- 来源边界：见 [`../../past-papers/2026上-recall-signals.md`](../../past-papers/2026上-recall-signals.md)，回忆版不等于官方原卷

---

## 八、区块链（⚠️ 官方大纲未覆盖）

> **重要声明**：区块链**不在软考架构师官方大纲第 10 章内**。仅作为行业背景收录。

### 共识机制对比

| 机制 | 全称 | 代表 | 类型 | 特点 |
|---|---|---|---|---|
| **PoW** | Proof of Work | 比特币、以太坊 1.0 | 公链 | 算力竞争，去中心强，耗能高 |
| **PoS** | Proof of Stake | 以太坊 2.0 | 公链 | 权益质押，节能 |
| **DPoS** | Delegated PoS | EOS | 公链 | 投票选代表节点，效率高 |
| **PBFT** | 实用拜占庭容错 | Fabric | 联盟链 | 3f+1 节点容 f 恶意，高吞吐低延迟 |
| **Raft** | Raft 一致性 | 私有链 / etcd | 私有 | 不抗拜占庭，仅容故障，强一致 |

### 智能合约

- 在链上自动执行的代码（图灵完备），代表：以太坊 Solidity、Fabric Chaincode（Go/Java）
- 特性：**去中心执行、不可篡改、可审计**；风险：**代码即法律**，漏洞不可回滚

### 链型对比

| 类型 | 参与 | 代表 | 典型场景 |
|---|---|---|---|
| **公链** | 无准入 | BTC、ETH | 加密资产 |
| **联盟链** | 准入制多组织 | Fabric、FISCO BCOS、长安链 | 供应链金融、溯源、数字凭证 |
| **私有链** | 单一组织 | 企业内部 | 内部审计追溯 |

### 考点角度

- 案例题：几乎不考。若真出现属于"扩展知识"扣分点少
- 论文：**"信息系统总体架构设计"**方向的"数据可信追溯"章节可点缀

---

## 学习建议与红线

1. **优先掌握 [`../10-emerging-tech/`](../10-emerging-tech/) 官方大纲 6 项**，本章仅作二级补充。
2. 综合知识科目答题时，**若题目问"未来信息综合技术包含以下哪几项"**，务必按官方 6 项选择，**不要选区块链/AIGC**。
3. 论文素材：本章内容**必须结合真实项目**改造，不要空谈概念；写作时用"扩展实践"过渡词避免和大纲直接冲突。
4. 与相关章节的引用：
   - [`../13-case-cloud-native/`](../13-case-cloud-native/) — 云原生案例章
   - [`../14-case-soa/`](../14-case-soa/) — SOA/微服务案例
   - [`../17-case-security/`](../17-case-security/) — 安全案例（零信任）
   - [`../18-case-big-data/`](../18-case-big-data/) — 大数据案例
   - [`../../cheatsheets/devops-cicd.md`](../../cheatsheets/devops-cicd.md) — DevOps 速查
   - [`../../cheatsheets/middleware-comparison.md`](../../cheatsheets/middleware-comparison.md) — 中间件对比
