# 知识地图（Notes Index）

按官方教材《系统架构设计师教程（第 2 版）》20 章结构组织。上篇为综合知识基础，下篇为案例分析常考的 8 类架构。

> ⚠️ 本目录为骨架，先建立知识地图框架，具体内容逐章填充。请对照官方教材精读。

## 上篇 · 综合知识

| # | 章节 | 教材章 | 考频 | 笔记入口 |
|---|---|---|---|---|
| 01 | 计算机系统基础 | 第 2 章 | ⭐⭐ | [01-computer-systems](./01-computer-systems/) |
| 02 | 信息系统 | 第 3 章 | ⭐⭐ | [02-information-systems](./02-information-systems/) |
| 03 | 信息安全技术 | 第 4 章 | ⭐⭐⭐ | [03-information-security](./03-information-security/) |
| 04 | 软件工程 | 第 5 章 | ⭐⭐⭐ | [04-software-engineering](./04-software-engineering/) |
| 05 | 数据库设计 | 第 6 章 | ⭐⭐⭐⭐ | [05-database-design](./05-database-design/) |
| 06 | 系统架构设计（核心） | 第 7 章 | ⭐⭐⭐⭐⭐ | [06-system-architecture-design](./06-system-architecture-design/) |
| 07 | 质量属性与架构评估 | 第 8 章 | ⭐⭐⭐⭐⭐ | [07-quality-attributes-and-evaluation](./07-quality-attributes-and-evaluation/) |
| 08 | 软件可靠性 | 第 9 章 | ⭐⭐⭐ | [08-software-reliability](./08-software-reliability/) |
| 09 | 软件架构演化与维护 | 第 10 章 | ⭐⭐⭐ | [09-architecture-evolution](./09-architecture-evolution/) |
| 10 | 未来信息综合技术（云原生/AI/区块链） | 第 11 章 | ⭐⭐⭐⭐（新考点） | [10-emerging-tech](./10-emerging-tech/) |

## 下篇 · 案例分析（8 类架构）

| # | 架构类型 | 教材章 | 典型场景 | 笔记入口 |
|---|---|---|---|---|
| 11 | 信息系统架构 | 第 12 章 | 企业信息化、OA/ERP | [11-case-info-system](./11-case-info-system/) |
| 12 | 层次式架构 | 第 13 章 | 三/四层 Web 应用 | [12-case-layered](./12-case-layered/) |
| 13 | 云原生架构 | 第 14 章 | K8s / 微服务 / Serverless | [13-case-cloud-native](./13-case-cloud-native/) |
| 14 | 面向服务架构（SOA） | 第 15 章 | ESB、服务编排 | [14-case-soa](./14-case-soa/) |
| 15 | 嵌入式系统架构 | 第 16 章 | 物联网、车载、工控 | [15-case-embedded](./15-case-embedded/) |
| 16 | 通信系统架构 | 第 17 章 | 电信级高可用 | [16-case-communication](./16-case-communication/) |
| 17 | 安全架构 | 第 18 章 | 纵深防御、零信任 | [17-case-security](./17-case-security/) |
| 18 | 大数据架构 | 第 19 章 | Lambda/Kappa、数据湖 | [18-case-big-data](./18-case-big-data/) |

## 补充专题（教材外常考）

| # | 专题 | 覆盖科目 | 笔记入口 |
|---|---|---|---|
| 19 | 计算机网络 | 📚 综合 4–6 题 | [19-networking](./19-networking/) |
| 20 | 数学与运筹学 | 📚 综合 2–3 题 | [20-math-foundations](./20-math-foundations/) |
| 21 | 知识产权与标准化 | 📚 综合 2–3 题必考 | [21-law-and-standards](./21-law-and-standards/) |
| 22 | 中间件专题 | 🎯 案例 + ✍️ 论文极高频 | [22-middleware](./22-middleware/) |
| 23 | 前沿技术与合规 | 🎯 案例 + ✍️ 论文高频 | [23-frontier-tech](./23-frontier-tech/) |

## 学习顺序建议

1. **先打地基**（01 → 05、19、21）：计算机/信息系统/安全/软工/数据库/网络/法规
2. **再攻核心**（06 → 07）：架构设计 + 质量属性/评估 —— **必考重点**
3. **再补延伸**（08 → 10、22、23）：可靠性、演化、中间件、新技术
4. **案例分析**（11 → 18）：对照历年真题按高频顺序（云原生 / 层次式 / SOA / 安全优先）
5. **论文准备**：cheatsheets 4 类论文模板 + 摘要模板 × 手写训练
6. **考前冲刺**（20、英语）：数学 + 英语 5 题是锦上添花
