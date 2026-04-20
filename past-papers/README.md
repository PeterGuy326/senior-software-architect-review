# Past Papers · 历年真题

## ⚠️ 原则声明

本目录**只存放自己的真题整理 / 错题本 / 解析**。

- **不存储**原始试卷（版权归软考办）
- 原题请从权威开源库获取：
  - [xxlllq/system_architect](https://github.com/xxlllq/system_architect) — 2009–2025 全套
  - [xiaomabenten/system_architect](https://github.com/xiaomabenten/system_architect)
- 商业教辅（《32 小时通关》等）自行购买

## 目录结构

```
past-papers/
├── README.md                 # 本文件
├── analysis-template.md      # 真题解析模板
├── paper-topics/             # ⭐ 论文 13 大主题（按题型分类）
│   ├── README.md             #   索引 + 选题策略 + 评分权重
│   ├── 01-architecture-design.md
│   ├── 02-architecture-evaluation.md
│   └── ... (13 个主题)
├── case-types/               # ⭐ 案例 9 大题型（按题型分类）
│   ├── README.md             #   索引 + 答题铁律 + 时间分配
│   ├── 01-architecture-evaluation.md
│   ├── 02-database-design.md
│   └── ... (9 个题型)
├── 2024-05/                  # 按年份组织（原题解析）
│   ├── comprehensive.md      # 综合知识解析
│   ├── case-analysis.md      # 案例分析解析
│   └── paper.md              # 论文复盘
├── 2024-11/
├── 2025-05/
└── wrong-questions.md        # 错题本（跨年份汇总）
```

## ⭐ 按题型复习（推荐）

- **论文提纲** → [paper-topics/README.md](./paper-topics/README.md)（13 大主题 + 万能提纲）
- **论文范文** → [paper-samples/README.md](./paper-samples/README.md)（**真实案例改编 · 2800 字完整范文**）
- **案例题型** → [case-types/README.md](./case-types/README.md)（9 大题型 + 答题模板）

## 近年考试节奏（核对用）

| 年份 | 上半年 | 下半年 |
|---|---|---|
| 2023 | 5 月 | 11 月（首次机考） |
| 2024 | 5 月 | 11 月 |
| 2025 | 5 月 | 11 月 |

## 真题使用建议

### 阶段 1：按章节刷

- 利用 xxlllq 仓库的**章节分类真题**功能
- 学完每章立即刷对应题目

### 阶段 2：按年份全真模考

- 近 3 年（2023 / 2024 / 2025）6 套
- **严格计时**：综合 150min + 案例 90min + 论文 120min

### 阶段 3：错题本

- 每套题后录入 `wrong-questions.md`
- 重点：错因分析（知识盲区 / 审题错误 / 计算失误）

## 常考主题频次（经验估计，需对照真题核准）

| 主题 | 综合知识 | 案例 | 论文 |
|---|---|---|---|
| 架构风格 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 质量属性 ATAM | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 数据库范式 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| 云原生 / 微服务 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| UML | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| 安全 / 等保 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 可靠性 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
