# 系统架构设计师 · 论文历年真题汇总（2009-2026，部分考期缺失）

> **数据来源**：[CSDN pccaiqq 134097142](https://blog.csdn.net/pccaiqq/article/details/134097142) + [掘金 7144645783126540324](https://juejin.cn/post/7144645783126540324) + [xxlllq/system_architect](https://github.com/xxlllq/system_architect)。2026 上半年由用户提供的考生回忆版 PDF 补充，未提交原文件，且未与官方原卷交叉验证。
>
> ⚠️ 题目仅作主题映射使用，**不含答案**，避免版权风险。

## 速查使用说明

- **按年份反查题目** → 第 2 节
- **按主题统计高频** → 第 3 节
- **考场 5 分钟选题决策** → 第 4 节
- **新趋势观察（2020+）** → 第 5 节
- **每年 4 道题选 1 道作答**，120 分钟，≥ 2500 字，合格线 45 分

## 1. 仓库范文与真题对照

| 真题主题 | 配套范文 |
|---|---|
| 架构设计 | [01-architecture-design.md](paper-samples/01-architecture-design.md) + [01b-architecture-style.md](paper-samples/01b-architecture-style.md) |
| 架构评估 | [02-architecture-evaluation.md](paper-samples/02-architecture-evaluation.md) + [02b-architecture-evaluation-government.md](paper-samples/02b-architecture-evaluation-government.md) |
| 可靠性 | [03-reliability-design.md](paper-samples/03-reliability-design.md) + [03b-reliability-evaluation.md](paper-samples/03b-reliability-evaluation.md) |
| 安全 | [04-security-design.md](paper-samples/04-security-design.md) + [04b-network-security.md](paper-samples/04b-network-security.md) |
| 微服务/云原生 | [05-microservice-cloud-native.md](paper-samples/05-microservice-cloud-native.md) + [05b-microservice-2021.md](paper-samples/05b-microservice-2021.md) |
| 大数据 NoSQL | [06-big-data-nosql.md](paper-samples/06-big-data-nosql.md) |
| SOA | [07-soa.md](paper-samples/07-soa.md) |
| 基于构件 | [08-component-based.md](paper-samples/08-component-based.md) |
| 架构演化 | [09-architecture-evolution.md](paper-samples/09-architecture-evolution.md) |
| 设计模式 | [10-design-patterns.md](paper-samples/10-design-patterns.md) |
| 企业应用集成 EAI | [11-enterprise-integration.md](paper-samples/11-enterprise-integration.md) |
| 测试质量 | [12-testing-qa.md](paper-samples/12-testing-qa.md) |
| DevOps Serverless | [13-devops-serverless.md](paper-samples/13-devops-serverless.md) |

## 2. 历年真题全表（已整理考期，按年份倒序）

> 列表中的"主题"列对应 [paper-topics/](paper-topics/) 编号。"-"表示该题不属于本仓库 13 大主题。回忆版只用于主题映射，题名和小问可能与官方原卷存在差异。

### 2026 年上半年（回忆版）

| # | 题目方向 | 主题 | 配套资料 |
|---|---|---|---|
| 1 | 向量数据库在项目中的应用 | 06 / 新兴 AI | [06-big-data-nosql.md](paper-topics/06-big-data-nosql.md) / [前沿技术](../notes/23-frontier-tech/README.md) |
| 2 | 高并发系统设计与实践 | 05 | [05-microservice-cloud-native.md](paper-topics/05-microservice-cloud-native.md) |
| 3 | 六边形架构设计与应用 | 10 / 01 | [10-design-patterns.md](paper-topics/10-design-patterns.md) |
| 4 | 多模态大模型在移动智能测试中的应用 | 12 / 新兴 AI | [12-testing-qa.md](paper-topics/12-testing-qa.md) / [前沿技术](../notes/23-frontier-tech/README.md) |

完整性和教学结论见 [`2026上-recall-signals.md`](./2026上-recall-signals.md)。

### 2024 年（上半年）

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | Lambda 架构的应用与分析 | 06 | [06-big-data-nosql.md](paper-samples/06-big-data-nosql.md) |
| 2 | 云原生云上 DevOps 运维应用与分析 | 13 | [13-devops-serverless.md](paper-samples/13-devops-serverless.md) |
| 3 | 模型驱动软件开发方法与应用 | 01 | [01-architecture-design.md](paper-samples/01-architecture-design.md) |
| 4 | 论单元测试在软件回归测试中的应用和分析 | 12 | [12-testing-qa.md](paper-samples/12-testing-qa.md) |

### 2023 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论面向对象设计的应用与实现 | 10 | [10-design-patterns.md](paper-samples/10-design-patterns.md) |
| 2 | 论多数据源集成的应用与实现 | 11 | [11-enterprise-integration.md](paper-samples/11-enterprise-integration.md) |
| 3 | 论软件可靠性模型的设计与实现 | 03 | [03b-reliability-evaluation.md](paper-samples/03b-reliability-evaluation.md) |
| 4 | 论边缘计算技术的设计与实现 | - | （新趋势：见第 5 节） |

### 2022 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论基于构件的软件开发方法及其应用 | 08 | [08-component-based.md](paper-samples/08-component-based.md) |
| 2 | 论软件维护方法及其应用 | 09 | [09-architecture-evolution.md](paper-samples/09-architecture-evolution.md) |
| 3 | 论区块链技术及其应用 | - | （新趋势：见第 5 节） |
| 4 | 论湖仓一体架构及其应用 | 06 | [06-big-data-nosql.md](paper-samples/06-big-data-nosql.md) |

### 2021 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论面向方面的编程技术及其应用（AOP） | - | （冷门：套用设计模式 10） |
| 2 | 论系统安全架构设计及其应用 | 04 | [04-security-design.md](paper-samples/04-security-design.md) |
| 3 | 论企业集成平台的理解与应用 | 11 | [11-enterprise-integration.md](paper-samples/11-enterprise-integration.md) |
| 4 | 论微服务架构及其应用 | 05 | [05b-microservice-2021.md](paper-samples/05b-microservice-2021.md) |

### 2020 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论数据分片技术及其应用 | 06 | [06-big-data-nosql.md](paper-samples/06-big-data-nosql.md) |
| 2 | 论云原生架构及其应用 | 05 | [05-microservice-cloud-native.md](paper-samples/05-microservice-cloud-native.md) |
| 3 | 论软件测试中缺陷管理及其应用 | 12 | [12-testing-qa.md](paper-samples/12-testing-qa.md) |
| 4 | 论企业集成架构设计及其应用 | 11 | [11-enterprise-integration.md](paper-samples/11-enterprise-integration.md) |

### 2019 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论软件设计方法及其应用 | 01 | [01-architecture-design.md](paper-samples/01-architecture-design.md) |
| 2 | 论软件系统架构评估及其应用 | 02 | [02b-architecture-evaluation-government.md](paper-samples/02b-architecture-evaluation-government.md) |
| 3 | 论数据湖技术及其应用 | 06 | [06-big-data-nosql.md](paper-samples/06-big-data-nosql.md) |
| 4 | 论负载均衡技术在 Web 系统中的应用 | 05 | [05-microservice-cloud-native.md](paper-samples/05-microservice-cloud-native.md) |

### 2018 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论软件开发过程 RUP 及其应用 | - | （冷门：考过程方法论） |
| 2 | 论软件体系结构的演化 | 09 | [09-architecture-evolution.md](paper-samples/09-architecture-evolution.md) |
| 3 | 论面向服务架构设计及其应用 | 07 | [07-soa.md](paper-samples/07-soa.md) |
| 4 | 论 NoSQL 数据库技术及其应用 | 06 | [06-big-data-nosql.md](paper-samples/06-big-data-nosql.md) |

### 2017 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论软件系统建模方法及其应用 | 01 | [01-architecture-design.md](paper-samples/01-architecture-design.md) |
| 2 | 论软件架构风格 | 01 | [01b-architecture-style.md](paper-samples/01b-architecture-style.md) |
| 3 | 论无服务器架构（Serverless）及其应用 | 13 | [13-devops-serverless.md](paper-samples/13-devops-serverless.md) |
| 4 | 论软件质量保证及其应用 | 12 | [12-testing-qa.md](paper-samples/12-testing-qa.md) |

### 2016 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论软件系统架构评估 | 02 | [02-architecture-evaluation.md](paper-samples/02-architecture-evaluation.md) |
| 2 | 论软件设计模式及其应用 | 10 | [10-design-patterns.md](paper-samples/10-design-patterns.md) |
| 3 | 论数据访问层设计技术及其应用 | 06 | [06-big-data-nosql.md](paper-samples/06-big-data-nosql.md) |
| 4 | 论微服务架构及其应用 | 05 | [05b-microservice-2021.md](paper-samples/05b-microservice-2021.md) |

### 2015 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论应用服务器基础软件 | - | （冷门：考中间件原理） |
| 2 | 论软件系统架构风格 | 01 | [01b-architecture-style.md](paper-samples/01b-architecture-style.md) |
| 3 | 论面向服务的架构及其应用 | 07 | [07-soa.md](paper-samples/07-soa.md) |
| 4 | 论企业集成平台的技术与应用 | 11 | [11-enterprise-integration.md](paper-samples/11-enterprise-integration.md) |

### 2014 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论软件需求管理 | - | （冷门：需求工程） |
| 2 | 论非功能需求对企业应用架构设计的影响 | 02 | [02-architecture-evaluation.md](paper-samples/02-architecture-evaluation.md) |
| 3 | 论软件的可靠性设计 | 03 | [03-reliability-design.md](paper-samples/03-reliability-design.md) |
| 4 | 论网络安全体系设计 | 04 | [04b-network-security.md](paper-samples/04b-network-security.md) |

### 2013 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论软件架构建模技术与应用 | 01 | [01-architecture-design.md](paper-samples/01-architecture-design.md) |
| 2 | 论企业应用系统的分层架构风格 | 01 | [01b-architecture-style.md](paper-samples/01b-architecture-style.md) |
| 3 | 论软件可靠性设计技术的应用 | 03 | [03-reliability-design.md](paper-samples/03-reliability-design.md) |
| 4 | 论分布式存储系统架构设计 | 06 | [06-big-data-nosql.md](paper-samples/06-big-data-nosql.md) |

### 2012 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论基于架构的软件设计方法及应用（ABSD） | 01 | [01-architecture-design.md](paper-samples/01-architecture-design.md) |
| 2 | 论企业应用系统的数据持久层架构设计 | 06 | [06-big-data-nosql.md](paper-samples/06-big-data-nosql.md) |
| 3 | 论决策支持系统的开发与应用（DSS） | - | （冷门：BI/DSS） |
| 4 | 论企业信息化规划的实施与应用 | - | （冷门：信息化管理） |

### 2011 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论模型驱动架构在系统开发中的应用（MDA） | 01 | [01-architecture-design.md](paper-samples/01-architecture-design.md) |
| 2 | 论企业集成平台的架构设计 | 11 | [11-enterprise-integration.md](paper-samples/11-enterprise-integration.md) |
| 3 | 论企业架构管理与应用 | 01 | [01-architecture-design.md](paper-samples/01-architecture-design.md) |
| 4 | 论软件需求获取技术及应用 | - | （冷门：需求工程） |

### 2010 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论软件的静态演化和动态演化及其应用 | 09 | [09-architecture-evolution.md](paper-samples/09-architecture-evolution.md) |
| 2 | 论数据挖掘技术的应用 | 06 | [06-big-data-nosql.md](paper-samples/06-big-data-nosql.md) |
| 3 | 论大规模分布式系统缓存设计策略 | 06 | [06-big-data-nosql.md](paper-samples/06-big-data-nosql.md) |
| 4 | 论软件可靠性评价 | 03 | [03b-reliability-evaluation.md](paper-samples/03b-reliability-evaluation.md) |

### 2009 年

| # | 题目 | 主题 | 配套范文 |
|---|---|---|---|
| 1 | 论基于 DSSA 的软件架构设计与应用 | 01 | [01-architecture-design.md](paper-samples/01-architecture-design.md) |
| 2 | 论信息系统建模方法 | 01 | [01-architecture-design.md](paper-samples/01-architecture-design.md) |
| 3 | 论基于 REST 服务的 Web 应用系统设计 | 05 | [05-microservice-cloud-native.md](paper-samples/05-microservice-cloud-native.md) |
| 4 | 论软件可靠性设计与应用 | 03 | [03-reliability-design.md](paper-samples/03-reliability-design.md) |

## 3. 主题分布热力图（统计截点：2024）

> 2025 考期尚未补齐，2026 上半年又是不完整回忆版，因此下表暂不强行重算精确频次。

| 主题 | 出现次数 | 占比 | 频度 | 推荐准备度 |
|---|---|---|---|---|
| **01 软件架构设计** | 10 | 16% | ⭐⭐⭐⭐⭐ | 必备 |
| **06 大数据 + NoSQL** | 10 | 16% | ⭐⭐⭐⭐⭐ | 必备 |
| **03 系统可靠性设计** | 5 | 8% | ⭐⭐⭐⭐ | 重点 |
| **05 微服务/云原生** | 5 | 8% | ⭐⭐⭐⭐ | 重点 |
| **11 企业应用集成 EAI** | 5 | 8% | ⭐⭐⭐⭐ | 重点 |
| **02 软件架构评估** | 3 | 5% | ⭐⭐⭐ | 中等 |
| **04 系统安全设计** | 3 | 5% | ⭐⭐⭐ | 中等 |
| **07 SOA** | 3 | 5% | ⭐⭐⭐ | 中等 |
| **09 架构演化与维护** | 3 | 5% | ⭐⭐⭐ | 中等 |
| **12 测试质量保证** | 3 | 5% | ⭐⭐⭐ | 中等 |
| **10 设计模式** | 2 | 3% | ⭐⭐ | 备选 |
| **13 DevOps + Serverless** | 2 | 3% | ⭐⭐ | 备选（新兴↑） |
| **08 基于构件 CBSD** | 1 | 2% | ⭐ | 备选 |
| 不在 13 主题（需求/MDA/AOP/DSS/区块链/边缘计算等） | 11 | 17% | ⭐⭐ | 选作 |

**高频主题 Top 5（必备 + 重点）合计 35 题，占比 55%**：架构设计（10）+ 大数据 NoSQL（10）+ 可靠性（5）+ 微服务云原生（5）+ EAI（5）。

**重要洞察**：考前如时间紧张，**优先吃透 Top 5 主题** + **任选其他 2-3 个主题**作为备选，可覆盖全场命中率 70%+。

## 4. 考场选题决策树（5 分钟内完成）

```
拿到 4 道题（120 分钟开始）
   │
   ├─ Step 1（1 分钟）：按"是否有真实项目"筛
   │   有真实项目 → 进入 Step 2
   │   纯理论题 → 暂排到末位
   │
   ├─ Step 2（1 分钟）：按"主题熟悉度"评分（5-10 分制）
   │   熟悉度 ≥ 8 → 优先候选
   │   熟悉度 5-7 → 备选
   │   熟悉度 < 5 → 直接淘汰
   │
   ├─ Step 3（1.5 分钟）：按"实践细节可量化度"打分
   │   能写 ≥ 5 个量化数据（QPS / 延迟 / 团队 / 周期 / 成本）→ 加分
   │   只能写口号没有数据 → 减分
   │
   ├─ Step 4（1 分钟）：按"避坑提醒"检查
   │   能避开主题对应的避坑点 → 加分
   │   有踩雷风险（如设计模式罗列 23 种）→ 减分
   │
   └─ Step 5（0.5 分钟）：综合得分最高者 → 锁定！

⚠️ 选题原则
- "熟悉度 8 + 量化数据 5+" 是优秀作文的底线
- "新兴技术题"（如 2024 Lambda、2022 区块链、2023 边缘计算）= 区分度高，但写不深易翻车
- "经典题"（架构设计、可靠性、SOA、设计模式）= 安全牌，套用万能模板
- 万能项目准备：1 个主项目可覆盖 3-4 个主题（见 paper-topics/README.md）
```

## 5. 新趋势观察（2020+ 出现的非传统主题）

| 年份 | 题目 | 类别 | 备考策略 |
|---|---|---|---|
| 2020 | 数据分片 | 大数据/数据库 | 套主题 06 |
| 2020 | 云原生架构 | 云原生 | 套主题 05 |
| 2021 | AOP 面向方面编程 | 编程范式 | 套主题 10（设计模式延伸）|
| 2022 | 区块链技术 | 新兴技术 | 单独准备：联盟链/智能合约/去中心化账本/共识算法 |
| 2022 | 湖仓一体（Lakehouse） | 大数据 | 套主题 06（已涵盖 Iceberg/Delta） |
| 2023 | 多数据源集成 | EAI | 套主题 11 |
| 2023 | 边缘计算 | 新兴技术 | 单独准备：边-云协同/IoT 网关/低延迟/带宽优化 |
| 2024 | Lambda 架构 | 大数据 | 套主题 06（已涵盖） |
| 2024 | 云原生 DevOps 运维 | DevOps | 套主题 13 |
| 2024 | 模型驱动开发 MDD | 架构设计 | 套主题 01（MDA 延伸） |
| 2026 | 向量数据库 | 大数据 / AI 工程化 | 套主题 06，补 embedding、向量索引和召回权衡 |
| 2026 | 高并发系统 | 微服务 / 性能 / 可靠性 | 套主题 05，仍是最安全的项目复用方向 |
| 2026 | 六边形架构 | 架构设计 / 设计模式 | 套主题 10/01，重点写端口与适配器及可测试性 |
| 2026 | 多模态大模型移动测试 | 测试质量 / AI 工程化 | 套主题 12，补模型误判、路径规划和执行闭环 |

**趋势总结**：
1. **大数据相关题目持续高频**（2018-2024 几乎每年都有）
2. **云原生 / DevOps 上升**（2017 Serverless → 2020 云原生 → 2024 云原生 DevOps）
3. **AI 工程化已直接进入题面**（2026 回忆版出现向量数据库和多模态大模型），但仍需等待更多来源确认稳定性
4. **基础架构题目稳定出现**（架构设计、SOA、可靠性、设计模式 16 年间反复）

**后续重点观察方向**：AI 系统架构 / 大模型应用集成 / 数据中台 / 多云架构 / 零信任安全 / FinOps 成本优化。

## 6. 备考建议（基于真题统计）

1. **必背 5 篇范文**：01 架构设计 / 06 大数据 NoSQL / 03 可靠性 / 05 微服务 / 11 EAI（覆盖 55% 真题）
2. **变体范文重点研读**：01b（架构风格 2017/2015） / 02b（架构评估 2019） / 03b（可靠性评价 2010/2023） / 04b（网络安全 2014） / 05b（微服务治理 2021/2016）
3. **冷门主题至少看提纲**：08（构件）/ 10（设计模式）/ 13（DevOps Serverless），考前 1 周快速过 paper-topics/0X-*.md
4. **新兴技术准备 1 个万能模板**：区块链/边缘计算/AI 各准备 1 套实践案例素材，作为冷门题应急
5. **考前 1 周默写**：选 1 篇主范文 + 1 篇变体范文，120 分钟限时手写训练

---

> 📌 题目数据持续更新。如发现年份缺失或题目偏差，请提 PR 修正。新真题数据可参考 [xxlllq/system_architect](https://github.com/xxlllq/system_architect) 同步。
