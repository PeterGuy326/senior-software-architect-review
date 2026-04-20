# 论文主题 13 · DevOps 与 Serverless

## 历年出题角度

- 论 DevOps 及其应用
- 论 Serverless（FaaS）架构
- 论持续交付与持续部署

## 一、核心理论

### DevOps 核心理念

**CALMS**：
- **C**ulture 文化（开发运维一体）
- **A**utomation 自动化
- **L**ean 精益
- **M**easurement 度量
- **S**haring 分享

### CI/CD 流水线

```
Commit → Build → Unit Test → SAST → Package
       → Deploy(Dev) → Integration Test
       → Deploy(Staging) → E2E Test
       → Deploy(Prod,灰度) → Monitoring
```

### 持续交付 vs 持续部署

- **持续交付（CD）**：随时可上线，需人工决策
- **持续部署（CD）**：自动上线生产

### 部署策略

| 策略 | 特点 |
|---|---|
| 蓝绿 | 两套环境切换，快速回滚 |
| 金丝雀 / 灰度 | 小流量验证 |
| 滚动 | K8s 默认，平滑 |
| 影子流量 | 复制生产流量到新版本 |

### Serverless / FaaS

- 代表：**AWS Lambda / 阿里函数计算 / 腾讯云函数**
- 特点：**按需付费、自动扩缩、无服务器运维**
- 适用：**事件驱动、短时任务**（图像处理、定时任务、Webhook）
- 局限：冷启动、执行时长限制、状态管理

### DORA 四大指标

1. **部署频率**
2. **变更前置时间**（Lead Time for Changes）
3. **变更失败率**
4. **服务恢复时间**（MTTR）

## 二、万能提纲（DevOps 建设）

```
1. 背景（350 字）
   - 发布周期月级、故障多、开发运维对立
2. 理论（350 字）
   - CALMS、CI/CD、DORA 四指标、Serverless
3. 实践论述（1600 字）⭐⭐⭐⭐⭐
   (1) 工具链：GitLab + Jenkins/Argo CD + K8s + Harbor
   (2) 自动化测试：单元 + 接口 + 性能 + 安全
   (3) IaC：Terraform + Ansible（基础设施即代码）
   (4) 监控可观测：Prometheus + Grafana + ELK + Jaeger
   (5) 部署策略：金丝雀 + 蓝绿（K8s）
   (6) Serverless：图片处理 / 定时任务 / Webhook 迁到 FaaS，成本降 40%
4. 成效（250 字）
   - 部署频率月 → 日，MTTR 小时 → 分钟
```

## 三、关键数据

- 部署频率：**每天 10+ 次**
- 变更前置：**< 1 天**
- 变更失败率：**< 5%**
- MTTR：**< 30 分钟**
- Serverless 成本：**降低 40%+**

## 四、万能句式

- "遵循 **CALMS** 理念，打通 Dev-Ops 文化墙"
- "基于 **DORA 四大指标**度量 DevOps 成熟度，达到 **Elite 级**"
- "非核心事件驱动场景迁移到 **Serverless（FaaS）**，成本降 40%"
- "采用 **Argo CD + GitOps** 模式，声明式部署 K8s"

## 五、避坑点

| ❌ | ✅ |
|---|---|
| DevOps = 自动化工具 | **文化 + 流程 + 工具**三位一体 |
| 无量化指标 | **DORA 四指标**必写 |
| Serverless 一把梭 | **冷启动、有状态**场景不适合 |
| 不讲可观测 | **Metrics/Logs/Traces** 三支柱 |
