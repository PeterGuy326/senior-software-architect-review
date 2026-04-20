# 知识点 18 · 缓存

## 一、核心概念

### 缓存模式

| 模式 | 流程 | 代表 |
|---|---|---|
| **Cache Aside** | 读：查缓存→未中回源→回填；写：更库→**删缓存** | **最主流** |
| **Read/Write Through** | 应用只打缓存，缓存组件负责回源 | EhCache |
| **Write Behind** | 写先入缓存，异步刷库 | 性能高但有丢失风险 |

### 三大问题（必考）

| 问题 | 含义 | 对策 |
|---|---|---|
| **穿透** | **不存在的数据**反复查（攻击） | **布隆过滤器** + 缓存空值 |
| **击穿** | **热点 key 过期瞬间**，请求直打 DB | **互斥锁** + 永不过期 + 异步刷新 |
| **雪崩** | **大量 key 同时过期** | **TTL 加随机** + 多级缓存 + 熔断降级 |

### 缓存一致性

**Cache Aside 主流方案**：**先更新 DB，再删除缓存**

| 方案 | 问题 |
|---|---|
| 先删缓存再更 DB | 并发下读请求把旧值写回缓存 |
| **先更 DB 再删缓存** ✅ | 极小窗口读旧值，可接受 |
| 延迟双删 | 更新前删 + sleep + 再删 |
| 订阅 binlog（Canal）| **强一致兜底方案** |

### Redis 数据结构

**String / List / Hash / Set / Zset / Bitmap / HyperLogLog / Geo / Stream**

### Redis 持久化

- **RDB**：快照，恢复快，可能丢数据
- **AOF**：追加日志，fsync 策略（always/everysec/no）
- **混合持久化**（4.0+）：RDB + AOF 增量

## 二、关联资源

- 速查：[cheatsheets/cache-patterns.md](../cheatsheets/cache-patterns.md)
- 案例题型：[past-papers/case-types/06-messaging-caching.md](../past-papers/case-types/06-messaging-caching.md)

## 三、典型例题

### 📚 选择题 1（三大问题）

黑客用大量**不存在的 ID** 攻击系统，属于：
- A. 击穿  B. **穿透**  C. 雪崩  D. 一致性

**答案**：B

### 📚 选择题 2（一致性）

Cache Aside 模式下推荐的写顺序：
- A. 先删缓存后更 DB  B. **先更 DB 后删缓存**  C. 先更 DB 后更缓存  D. 只更缓存

**答案**：B

### 📚 选择题 3（持久化）

Redis 默认恢复速度**最快**的持久化方式：
- A. AOF always  B. AOF everysec  C. **RDB**  D. 不持久化

**答案**：C

### 🎯 案例填空：防雪崩方案

- **TTL 加随机**：TTL = base + rand(0, 300s)
- **多级缓存**：本地 **Caffeine** + 分布式 **Redis**
- **熔断降级**：Sentinel 触发降级返回默认值
- **预热**：启动时批量加载热点 key

### ✍️ 论文场景

"采用**多级缓存（Caffeine + Redis Cluster）+ 布隆过滤器**防穿透；热点 Key **永不过期 + 异步刷新**防击穿；**TTL 随机化**防雪崩；通过 **Canal 监听 binlog** 做最终一致性兜底。"
