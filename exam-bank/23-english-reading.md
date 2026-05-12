# 英语阅读（综合知识固定最后 5 题） · 25 题（5 套）

> **高频考点**（每年**固定 5 题、占 7%、是最稳的送分区**）· 一篇 IT 英语短文（200-300 词）+ 5 个**选词填空**（4 选 1）· 主题集中在：云计算 / 微服务 / 容器 / AI 与大数据 / DevOps / 软件架构 / 信息安全 / 敏捷与项目管理
> **答题套路**：①先看选项词性（名/动/形/副）排错；②精读空格上下句（80% 单句可解）；③主题/逻辑一致原则；④拿不准时选"教材式"高频词。

---

## Passage 1 — Cloud Computing & Service Models

Cloud computing has fundamentally changed the way enterprises consume IT resources. Instead of purchasing hardware upfront, organizations can now **__(1)__** computing power, storage, and networking on-demand over the Internet. Three service models dominate the market: Infrastructure as a Service (IaaS) provides virtualized hardware, Platform as a Service (PaaS) offers a managed runtime, and Software as a Service (SaaS) delivers complete applications.

A key benefit of cloud platforms is **__(2)__** — the ability to automatically add or remove resources in response to changing workloads. During traffic spikes, additional virtual machines are spun up; when demand falls, they are released to save cost. This pay-as-you-go model significantly lowers the **__(3)__** cost of entry for startups, while large enterprises gain operational flexibility.

However, cloud adoption is not without challenges. Concerns about data **__(4)__**, regulatory compliance, and vendor lock-in have led many organizations to adopt hybrid or multi-cloud strategies. To minimize lock-in risk, architects increasingly choose open standards such as Kubernetes for container **__(5)__**, which provides a consistent abstraction layer across different cloud providers.

---

### 1. (1)

A. purchase

✅ **B. provision**

C. develop

D. install

**答案**：B
**解析**：on-demand 是云计算的核心特征，**provision**（按需供给/配置）是云上下文的高频动词。purchase（购买）与 on-demand 矛盾——云不是一次性买断。develop（开发）、install（安装）都不是消费计算资源的动词。

---

### 2. (2)

A. virtualization

B. consistency

✅ **C. elasticity**

D. portability

**答案**：C
**解析**：题干"automatically add or remove resources in response to changing workloads"是 **elasticity（弹性）** 的标准定义。virtualization（虚拟化）是基础技术不是按需伸缩；consistency（一致性）是分布式系统术语；portability（可移植性）是跨平台能力。

---

### 3. (3)

A. operational

✅ **B. upfront**

C. recurring

D. marginal

**答案**：B
**解析**：上一段提到"Instead of purchasing hardware upfront"，本句呼应——pay-as-you-go 显著降低了**前期/一次性（upfront）** 投入门槛。operational 是日常运营成本（云反而是 operational 形态）；recurring（经常性）逻辑相反；marginal（边际）经济学术语不贴切。

---

### 4. (4)

A. compression

B. integration

✅ **C. privacy**

D. duplication

**答案**：C
**解析**：与"regulatory compliance（合规）、vendor lock-in（厂商锁定）"并列的云担忧——**data privacy（数据隐私）** 是教材原话。data compression（压缩）/integration（集成）/duplication（重复）都不是 cloud adoption 的核心 concern。

---

### 5. (5)

A. compilation

B. distribution

✅ **C. orchestration**

D. simulation

**答案**：C
**解析**：Kubernetes 的标准定语是 **container orchestration（容器编排）**——管理容器集群的部署、调度、伸缩、自愈。compilation（编译）/distribution（分发）/simulation（仿真）都不是 K8s 定义。

---

## Passage 2 — Microservices Architecture

Microservices architecture has emerged as a popular alternative to the traditional **__(6)__** application style. Instead of building a single, large codebase, developers decompose the system into a set of small, independently deployable services, each focused on a specific business capability. Services communicate with each other through lightweight protocols, typically REST APIs or message queues.

One major advantage of this approach is **__(7)__** — different services can be developed, deployed, and scaled independently, allowing teams to release new features faster. Each service may even use a different programming language or database, a property often described as polyglot persistence.

However, microservices introduce significant operational complexity. Distributed systems are inherently harder to debug, and ensuring data **__(8)__** across service boundaries requires careful design — patterns such as Saga and TCC are commonly used to handle distributed transactions. To manage the increased number of services, teams often adopt a **__(9)__**, which handles cross-cutting concerns such as service discovery, load balancing, and circuit breaking.

Successful adoption of microservices typically requires a strong DevOps culture, automated testing, and continuous deployment pipelines. Without these foundations, the architecture's benefits can quickly be overshadowed by its operational **__(10)__**.

---

### 6. (6)

A. layered

✅ **B. monolithic**

C. distributed

D. event-driven

**答案**：B
**解析**："single, large codebase"和"alternative to"是**monolithic（单体）** 的标准对照。layered（分层）和 microservices 不对立；distributed（分布式）反而和 microservices 同类；event-driven（事件驱动）是另一种风格。

---

### 7. (7)

A. consistency

✅ **B. agility**

C. simplicity

D. centralization

**答案**：B
**解析**："developed, deployed, and scaled independently...release new features faster"是 **agility（敏捷性）** 的核心收益。consistency 反而是微服务的难题；simplicity（简单性）单体更胜；centralization（集中化）与微服务理念相反。

---

### 8. (8)

A. integrity

✅ **B. consistency**

C. visibility

D. portability

**答案**：B
**解析**：跨服务边界的数据问题、Saga/TCC 处理的是**分布式事务的 data consistency（数据一致性）**——这是教材原话。integrity（完整性）侧重不被篡改/损坏，与事务语境不完全契合；visibility/portability 都不贴。

---

### 9. (9)

A. data warehouse

✅ **B. service mesh**

C. message broker

D. load balancer

**答案**：B
**解析**："service discovery, load balancing, circuit breaking"等横切关注点（cross-cutting concerns）是 **service mesh（服务网格，如 Istio/Linkerd）** 的标准职责。data warehouse 是数据仓库；message broker（消息中间件）只解决异步通信；load balancer 只是 service mesh 的一个子能力。

---

### 10. (10)

A. benefits

✅ **B. overhead**

C. revenue

D. capacity

**答案**：B
**解析**：与 benefits（收益）对照的是 **operational overhead（运营开销/负担）**——这是微服务的核心代价。revenue（收入）/capacity（容量）都不是与"benefits be overshadowed by"搭配的对立词。

---

## Passage 3 — Software Quality & Security

Software quality is not a single attribute but a multi-dimensional concept. According to ISO/IEC 25010, quality is decomposed into eight characteristics including functional suitability, performance efficiency, compatibility, usability, reliability, security, maintainability, and **__(11)__**. Architects must make trade-offs among these attributes because optimizing one often degrades another — for example, adding strong encryption improves security but hurts performance.

Security has become particularly critical as systems become more **__(12)__** to the public Internet. The CIA triad — Confidentiality, Integrity, and Availability — remains the foundation of information security. Threat modeling frameworks such as STRIDE help architects systematically identify risks: Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, and Elevation of privilege.

To protect against unauthorized access, modern systems rely on a combination of **__(13)__** (verifying who you are) and authorization (determining what you can do). Multi-factor authentication, encrypted communication via TLS, and regular security audits are now considered baseline requirements.

Maintainability is another long-term concern. Code that is hard to understand or change accumulates **__(14)__** debt, slowing future development. Practices such as code reviews, automated testing, and clear documentation help control this debt. Tools that measure code complexity — for example, cyclomatic complexity computed via McCabe's formula — provide quantitative **__(15)__** for refactoring decisions.

---

### 11. (11)

A. simplicity

B. cost

C. delivery

✅ **D. portability**

**答案**：D
**解析**：ISO/IEC 25010 八大质量特性是教材高频考点：**功能适合性 / 性能效率 / 兼容性 / 易用性 / 可靠性 / 安全性 / 可维护性 / 可移植性（portability）**。其他三项都不在 25010 的八特性内。

---

### 12. (12)

✅ **A. exposed**

B. hidden

C. limited

D. opposed

**答案**：A
**解析**："systems become more **exposed** to the public Internet"——暴露在公网，因此安全更关键。hidden 与 critical 安全语境相反；limited/opposed 词义不通。

---

### 13. (13)

A. authorization

✅ **B. authentication**

C. encryption

D. validation

**答案**：B
**解析**：题干已经括号点明"verifying who you are"是 **authentication（认证/身份验证）** 的定义；后半句的 authorization（授权）回答"what you can do"。这两个词是软考高频对照考点：**AuthN（认证你是谁）vs AuthZ（授权你能做什么）**。

---

### 14. (14)

A. financial

✅ **B. technical**

C. credit

D. business

**答案**：B
**解析**：**technical debt（技术债务）** 是软件工程标准术语——为了短期交付而牺牲代码质量，未来要"还利息"。financial/credit/business debt 都不在软件工程语境。

---

### 15. (15)

A. evidence

B. opinion

✅ **C. basis**

D. promise

**答案**：C
**解析**："provide quantitative **basis** for refactoring decisions"——为重构决策提供**量化依据**。evidence 偏证据链；opinion 是主观意见与 quantitative 矛盾；promise 不通。

---

## Passage 4 — DevOps & Continuous Delivery

DevOps is a cultural and technical movement that aims to bridge the gap between software development and IT operations. The core idea is to enable teams to deliver software faster, more frequently, and with higher quality, by **__(16)__** the boundary between Dev and Ops teams and automating the entire software delivery lifecycle.

A central practice of DevOps is Continuous Integration (CI), in which developers merge their changes into a shared trunk multiple times a day. Each commit triggers an automated build and test pipeline, allowing problems to be detected **__(17)__** rather than during late-stage integration. This shifts testing to the left, reducing the cost of fixing defects.

Building on CI, Continuous Deployment automatically releases every passing build to production. To reduce release risk, teams employ deployment strategies such as blue-green and **__(18)__** releases. The latter gradually shifts traffic from the old version to the new one, allowing problems to be detected and rolled back before they affect all users.

Infrastructure as Code (IaC) is another DevOps **__(19)__**. Tools like Terraform and Ansible allow infrastructure to be defined declaratively in version-controlled files, making environments reproducible and changes auditable. Combined with GitOps, even production infrastructure changes go through pull-request review.

DORA, the well-known DevOps research program, identifies four key metrics for delivery performance: deployment frequency, lead time for changes, change failure rate, and mean time to **__(20)__**. High-performing teams excel on all four.

---

### 16. (16)

✅ **A. removing**

B. defining

C. enforcing

D. respecting

**答案**：A
**解析**：DevOps 的核心精神就是**消除（remove）** Dev 与 Ops 之间的壁垒。defining/enforcing/respecting 都是强化边界，与 DevOps 文化相反。

---

### 17. (17)

✅ **A. early**

B. eventually

C. randomly

D. silently

**答案**：A
**解析**："shifts testing to the left, reducing the cost of fixing defects"——**早期（early）** 发现问题。eventually（最终）/randomly（随机）/silently（无声）都不符合"快速反馈"的 CI 理念。**shift-left testing** 是 DevOps 高频术语。

---

### 18. (18)

A. parallel

B. waterfall

✅ **C. canary**

D. cascading

**答案**：C
**解析**："gradually shifts traffic from the old version to the new"是 **canary（金丝雀）** 发布的定义。与 blue-green（蓝绿）并列的就是 canary。parallel/waterfall/cascading 都不是发布策略名词。

---

### 19. (19)

A. obstacle

✅ **B. pillar**

C. burden

D. exception

**答案**：B
**解析**：IaC 与 CI/CD 并列，是 DevOps 的**支柱（pillar）/ 核心实践**。obstacle（障碍）/burden（负担）/exception（例外）都是负面词，与"another...practice"的语境矛盾。

---

### 20. (20)

A. failure

✅ **B. recovery**

C. deployment

D. release

**答案**：B
**解析**：DORA 四大指标是教材标准考点——**部署频率（deployment frequency）、变更前置时间（lead time for changes）、变更失败率（change failure rate）、平均恢复时间（mean time to recovery，MTTR）**。题干前三个已点名，第四个必然是 recovery。

---

## Passage 5 — Big Data & Artificial Intelligence

The explosive growth of data has driven the rise of big data architectures. The classic "3V" definition characterizes big data by **__(21)__**, velocity, and variety — though additional V's such as veracity and value are often added. To handle such workloads, organizations have moved beyond traditional relational databases to embrace distributed storage like HDFS and parallel processing frameworks like MapReduce and Spark.

Two architectural patterns dominate big data design. The Lambda architecture combines a batch layer for accurate historical results with a speed layer for low-latency real-time views. The Kappa architecture simplifies this by treating everything as a **__(22)__** of events, processed by a single stream engine. Choosing between them is a classic trade-off between completeness and simplicity.

Closely related is the emergence of artificial intelligence and machine learning. Modern AI systems are typically **__(23)__** on massive labeled datasets, then deployed to perform inference on new inputs. Deep learning, powered by neural networks with many layers, has achieved remarkable results in image recognition, natural language processing, and speech synthesis.

However, deploying ML in production introduces new challenges. Models can suffer from data **__(24)__** as the real-world distribution shifts over time, requiring continuous monitoring and retraining. Practices around the lifecycle of ML models — versioning, testing, deployment, and monitoring — have crystallized into a discipline called MLOps.

As AI permeates more domains, **__(25)__** concerns such as bias, fairness, transparency, and accountability have moved to the forefront. Architects designing AI-driven systems must consider not only technical performance but also social and regulatory implications.

---

### 21. (21)

A. validity

B. visibility

✅ **C. volume**

D. virtuality

**答案**：C
**解析**：大数据**3V** 是教材原话：**Volume（体量）、Velocity（速度）、Variety（多样）**——后续才扩展出 Veracity（真实性）和 Value（价值）。题干已给出 velocity、variety，缺的必然是 volume。

---

### 22. (22)

A. table

B. snapshot

✅ **C. stream**

D. batch

**答案**：C
**解析**：Kappa 架构的核心思想是"**一切皆流（stream）**"——用单一流处理引擎统一批和实时。batch 反而是 Lambda 的特征；table/snapshot 都是静态数据形式与 Kappa 思想矛盾。

---

### 23. (23)

✅ **A. trained**

B. compiled

C. encrypted

D. translated

**答案**：A
**解析**：机器学习的标准动词组合——模型先在数据上**训练（trained）**，然后部署做**推理（inference）**。compiled（编译）/encrypted（加密）/translated（翻译）都不是 ML 生命周期动词。

---

### 24. (24)

A. backup

✅ **B. drift**

C. compression

D. encryption

**答案**：B
**解析**：**data drift / concept drift（数据漂移）** 是 MLOps 高频术语——真实世界数据分布随时间偏离训练分布，导致模型性能下降。题干"real-world distribution shifts over time"就是 drift 的定义。

---

### 25. (25)

A. financial

B. technical

✅ **C. ethical**

D. spatial

**答案**：C
**解析**："bias, fairness, transparency, and accountability"是 **ethical AI（AI 伦理）** 的四大议题，已成为软考新趋势考点。financial（财务）/technical（技术）/spatial（空间）都不能涵盖偏见、公平、问责这类社会维度。

---

## 高频词汇速记（按主题）

| 主题 | 高频词 |
|---|---|
| **云计算** | provision, elasticity, on-demand, pay-as-you-go, IaaS/PaaS/SaaS, virtualization, hypervisor, multi-tenancy, hybrid, vendor lock-in |
| **容器 / K8s** | container, orchestration, image, pod, cluster, namespace, declarative, immutable |
| **微服务** | monolithic, decompose, polyglot, service mesh, API gateway, circuit breaker, service discovery, observability |
| **DevOps** | CI/CD, pipeline, shift-left, blue-green, canary, rollback, IaC, GitOps, MTTR, DORA |
| **架构 / 质量** | scalability, availability, reliability, maintainability, portability, coupling, cohesion, abstraction, trade-off, refactoring, technical debt |
| **安全** | confidentiality, integrity, availability (CIA), authentication, authorization, encryption, TLS, threat modeling, STRIDE, vulnerability, audit |
| **大数据 / AI** | volume/velocity/variety, batch, stream, MapReduce, Spark, Lambda/Kappa, training, inference, neural network, drift, MLOps, bias, fairness |
| **方法 / 项目** | agile, scrum, sprint, backlog, iteration, retrospective, stakeholder, requirement, milestone |

## 答题黄金 4 步

1. **先看 4 个选项的词性**——空后是名词找形容词/动词；空后是动词找主语/副词；先排错词性。
2. **精读空格上下句**——80% 单句解；如果上下句有并列、转折、因果连接词（and/but/because/so/therefore）就找语义呼应。
3. **主题一致**——这是 IT 英语，选项中只要有 IT 高频词（virtualization, orchestration, elasticity, monolithic 等），优先考虑。
4. **教材原话优先**——拿不准就选最像"教材定义"的那个；CIA/STRIDE/3V/DORA 这类是固定搭配，必须背。
