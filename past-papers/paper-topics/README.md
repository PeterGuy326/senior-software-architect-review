# 论文主题分类索引（历年真题 + 万能提纲）

> 数据来源：[希赛网历年论文汇总](https://www.educity.cn/rk/5328329.html) + [CSDN 2009-2024 论文真题分析](https://blog.csdn.net/pccaiqq/article/details/134097142) + [xxlllq 真题库](https://github.com/xxlllq/system_architect)
>
> ⚠️ 下方"历年出现"是基于公开资料整理，具体年份请对照权威真题库核准。

## 论文考试套路（铁律）

- **1 场 4 题任选 1 题作答**
- **时长 120 分钟**
- **字数 ≥ 2500**
- **合格线 45 分**
- **近年趋势**：从"方法论"转向"场景应用"，新技术（云原生 / 大数据 / AI / 区块链）占比上升

## 13 大主题索引（按考频排序）

| # | 主题 | 出现频次（估计） | 难度 | 文件 |
|---|---|---|---|---|
| 01 | 软件架构设计（通用） | ⭐⭐⭐⭐⭐ | 中 | [01-architecture-design.md](./01-architecture-design.md) |
| 02 | 软件架构评估（ATAM） | ⭐⭐⭐⭐⭐ | 中 | [02-architecture-evaluation.md](./02-architecture-evaluation.md) |
| 03 | 系统可靠性设计 | ⭐⭐⭐⭐⭐ | 中 | [03-reliability-design.md](./03-reliability-design.md) |
| 04 | 系统安全性与保密性设计 | ⭐⭐⭐⭐⭐ | 中 | [04-security-design.md](./04-security-design.md) |
| 05 | 微服务与云原生架构 | ⭐⭐⭐⭐⭐ | 中 | [05-microservice-cloud-native.md](./05-microservice-cloud-native.md) |
| 06 | 大数据与 NoSQL 架构 | ⭐⭐⭐⭐ | 中高 | [06-big-data-nosql.md](./06-big-data-nosql.md) |
| 07 | 面向服务架构 SOA | ⭐⭐⭐⭐ | 中 | [07-soa.md](./07-soa.md) |
| 08 | 基于构件的软件开发 | ⭐⭐⭐⭐ | 中 | [08-component-based.md](./08-component-based.md) |
| 09 | 软件架构演化与维护 | ⭐⭐⭐⭐ | 中 | [09-architecture-evolution.md](./09-architecture-evolution.md) |
| 10 | 软件设计模式应用 | ⭐⭐⭐ | 中 | [10-design-patterns.md](./10-design-patterns.md) |
| 11 | 企业应用集成 EAI | ⭐⭐⭐ | 中 | [11-enterprise-integration.md](./11-enterprise-integration.md) |
| 12 | 软件测试与质量保证 | ⭐⭐⭐ | 低 | [12-testing-qa.md](./12-testing-qa.md) |
| 13 | DevOps 与无服务器架构 | ⭐⭐⭐（新增） | 中 | [13-devops-serverless.md](./13-devops-serverless.md) |

## 选题策略（考场实战）

### 按熟悉度优先级

1. **第一选择**：有真实项目经验的主题（写得出细节）
2. **备选 1**：理论体系最熟的（哪怕项目是"加工"的）
3. **备选 2**：近年新主题（避免老八股）

### 万能项目选型建议

准备 **1 个万能项目** 能覆盖以下 3–4 种主题最佳：

| 万能项目类型 | 可覆盖主题 |
|---|---|
| **电商交易系统** | 01/02/03/05/10 |
| **金融核心系统** | 01/03/04/07/11 |
| **大数据平台** | 01/06/09 |
| **物联网平台** | 01/03/05/13 |
| **政企应用系统** | 01/04/07/11 |

## 通用写作流程（120 分钟时间分配）

```
阅读 4 题选题             5  min
摘要起草                 15  min
提纲列出                 10  min
正文写作                 75  min
检查润色                 15  min
```

## 评分权重（经验估计）

| 部分 | 占比 | 关键 |
|---|---|---|
| 摘要 | 10–15% | 规模 + 角色 + 成果量化 |
| 背景 | 15% | 业务价值 + 团队 + 时间 |
| 理论 | 15–20% | 本主题核心理论（不要跑题） |
| **实践**（核心） | **40–50%** | 至少 3 条深入展开，量化数据 |
| 总结 | 10% | 成效 + 不足 + 改进 |
