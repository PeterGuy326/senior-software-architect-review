# 07 · 质量属性与架构评估（教材第 8 章）— 🔥 必考

## 一、六大质量属性（必背）

| 属性 | 含义 | 关键战术 |
|---|---|---|
| **可用性** (Availability) | 系统正常运行时间占比 | 冗余、心跳、主动监测、回滚、事务 |
| **性能** (Performance) | 响应时间、吞吐量 | 减少计算开销、并行、引入并发、增加资源、优先级、负载均衡 |
| **安全性** (Security) | CIA（机密、完整、可用） | 认证、授权、审计、加密、限制暴露 |
| **可修改性** (Modifiability) | 修改成本 | 模块化、信息隐藏、松耦合、延迟绑定 |
| **可测试性** (Testability) | 测试难度 | 记录/回放、内置监测、接口分离 |
| **易用性** (Usability) | 用户学习与使用成本 | 用户模型、运行时用户支持、界面一致性 |

## 二、质量属性场景（6 元组）

**刺激源 → 刺激 → 制品 → 环境 → 响应 → 响应度量**

例：
> 系统管理员（刺激源）在正常运行时（环境）修改安全规则（刺激），对认证系统（制品）生效（响应），不超过 1 小时（响应度量）。

## 三、架构评估方法

| 方法 | 全称 | 特点 | 输出 |
|---|---|---|---|
| **SAAM** | Scenario-Based Architecture Analysis Method | 最早，基于场景 | 场景集、冲突分析 |
| **ATAM** | Architecture Tradeoff Analysis Method | **最常考**，关注权衡点 | 敏感点、权衡点、风险点、非风险点 |
| **CBAM** | Cost Benefit Analysis Method | 基于 ATAM，引入经济考量 | 成本收益分析 |

### ATAM 四类关键点（必背）

- **敏感点**：为实现某质量属性而关键的架构决策
- **权衡点**：影响多个质量属性的决策（有正有负）
- **风险点**：可能导致风险的架构决策
- **非风险点**：已被确认安全的决策

## 速查

完整 cheatsheet → [cheatsheets/quality-attributes.md](../../cheatsheets/quality-attributes.md)
ATAM 案例题套路 → [cheatsheets/architecture-evaluation.md](../../cheatsheets/architecture-evaluation.md)

## TODO

- [ ] 历年 ATAM 案例题汇总
- [ ] 质量属性战术脑图
