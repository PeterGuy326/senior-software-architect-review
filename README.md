# 系统架构设计师（软考高级）复习仓库

> 面向「全国计算机技术与软件专业技术资格（水平）考试 — 系统架构设计师」的自用复习资料库。

## 考试基本信息

> ⚠️ 以下数据依据《计算机技术与软件专业技术资格（水平）考试实施办法》第六条及 2022 审定通过的《系统架构设计师考试大纲》。完整权威骨架见 [`SYLLABUS.md`](./SYLLABUS.md)。

| 项 | 内容 |
|---|---|
| 资格等级 | 高级 |
| 考试频次 | 一年两次：**5 月 / 11 月** |
| 考试形式 | **机考**（2023 下半年起计算机化考试） |
| 科目 1：综合知识 | 客观选择题 75 道，**150 分钟**（2.5 小时），75 分 |
| 科目 2：案例分析 | 主观问答 5 道，**第 1 题必做 + 后 4 题选 2 = 共答 3 题**，**90 分钟**（1.5 小时），75 分 |
| 科目 3：论文 | 4 道论文题选 1 道，**120 分钟**（2 小时），≥ 2500 字，75 分 |
| 合格线 | **三科同一次考试均 ≥ 45 分**，成绩不跨期保留 |
| 官方指定教材 | 《系统架构设计师教程（第 2 版）》叶宏等，清华大学出版社，2022-11，ISBN 978-7-302-61992-5 |
| 官方指定大纲 | 《系统架构设计师考试大纲》全国计算机专业技术资格考试办公室编，清华大学出版社，2022-11 审定通过，ISBN 978-7-302-62003-7 |

### 大纲结构一览（2022 审定版）

- **科目一 综合知识**：13 大知识域 —— 计算机系统 / 信息系统 / 信息安全 / 软件工程 / 数据库 / 系统架构 / 质量属性与评估 / 软件可靠性 / 架构演化维护 / **未来信息综合技术**（CPS/AI/机器人/边缘计算/数字孪生/云大）/ 标准化与知识产权 / 应用数学 / 专业英语
- **科目二 案例分析**：9 大主题 —— 系统计划 / 信息系统架构 / 层次式 / 云原生 / SOA / 嵌入式 / 通信 / 安全 / 大数据
- **科目三 论文**：5 大方向 —— 系统建模 / 软件架构设计 / 系统设计 / 可靠性 / 安全性与保密性

## 目录结构

```
├── SYLLABUS.md                 # ⭐ 官方 2022 大纲蒸馏（权威骨架，所有目录以此为准）
├── notes/                      # 按官方大纲 13 知识域 + 9 案例主题的知识笔记
├── mind-maps/                  # 核心知识域 Mermaid 脑图
├── past-papers/
│   ├── paper-topics/           # ⭐ 论文 13 大主题分类（万能提纲 + 21 道仿真模拟题）
│   ├── paper-samples/          # ⭐ 18 篇真实项目改编范文（13 主题全覆盖 + 5 篇高频变体，3000+ 字）
│   ├── case-types/             # ⭐ 案例 9 大题型分类（答题套路 + 26 道完整模拟题）
│   ├── essay-questions-by-year.md  # ⭐ 2009-2024 历年论文真题清单 + 主题映射 + 选题决策树
│   ├── analysis-template.md    # 历年真题解析模板
│   └── wrong-questions.md      # 错题本
├── exam-bank/                  # ⭐ 综合选择题题库（自主命题 320+ 题，17 章高频考点）
├── knowledge-index/            # ⭐ 22 个知识点 → 对应例题索引
├── cheatsheets/                # 高频考点速查表（质量属性/UML/模式等）
└── resources.md                # 外部权威资源索引
```

### 📊 题库规模一览

| 科目 | 题型 | 题数 | 位置 |
|---|---|---|---|
| 综合知识 | **历年真题结构化 md**（431 题带 §N.M 知识点标签） | **7 年 × 75 题** | [`past-papers/comprehensive-by-year/`](./past-papers/comprehensive-by-year/) |
| 综合知识 | 选择题题库（自主命题 + 解析） | **320+** | [`exam-bank/`](./exam-bank/) |
| 案例分析 | 完整模拟题（题干+答案+评分） | **26** | [`past-papers/case-types/`](./past-papers/case-types/) |
| 论文 | 仿真模拟论文题（题目+提纲答案） | **21** | [`past-papers/paper-topics/`](./past-papers/paper-topics/) |
| 论文 | 完整范文（3000+ 字/篇，13 主题全覆盖 + 5 高频变体） | **18** | [`past-papers/paper-samples/`](./past-papers/paper-samples/) |
| 论文 | 历年真题清单（2009-2024，64+ 题）+ 主题映射 + 选题决策树 | **1 份** | [`past-papers/essay-questions-by-year.md`](./past-papers/essay-questions-by-year.md) |

> 需要历年真题原卷 PDF？从公开源 [xiaomabenten/system_architect](https://github.com/xiaomabenten/system_architect/tree/main/03、历年真题(2009年-2025年)%2B答案解析) 自行下载（含 2018-2025 完整卷 + 答案详解）。本仓库不重复存放大 PDF 二进制文件。

### 🎯 只求过线？直接走最短路径

**综合科目 45/75 保命三件套**（按顺序读）：

1. [`past-papers/HIGH_FREQ.md`](./past-papers/HIGH_FREQ.md) — 431 道真题实测的高频统计，告诉你时间该花在哪
2. [`past-papers/SURVIVAL_CARD.md`](./past-papers/SURVIVAL_CARD.md) — 272 条核心考点保命卡，考前 3 天翻这一份
3. [`past-papers/comprehensive-by-year/`](./past-papers/comprehensive-by-year/) — 逐年真题 md，对着 HIGH_FREQ 的 Top 20 直接搜真题练手

**过线策略**（数据来自 7 年真题）：只抓 §4 软件工程（21.8%）+ §6 系统架构（17.6%）+ §1 计算机系统（13.7%）+ §7 质量属性（10.0%）= **63% ≈ 47 题**。这 4 板块打到 85% 正确 = 40 题稳过，其他 28 题蒙对 7 题即可达到 47/75 保过。

### 三科对应速查入口

| 科目 | 主用目录 |
|---|---|
| 📚 **综合知识**（75 选 1） | [`past-papers/comprehensive-by-year/`](./past-papers/comprehensive-by-year/) 历年真题 + [`past-papers/SURVIVAL_CARD.md`](./past-papers/SURVIVAL_CARD.md) 保命卡 + [`cheatsheets/`](./cheatsheets/) 速查表 |
| 🎯 **案例分析**（5 选 3） | [`past-papers/case-types/`](./past-papers/case-types/) |
| ✍️ **论文**（4 选 1） | [`past-papers/paper-topics/`](./past-papers/paper-topics/) |

## 按知识点索引例题（强烈推荐）

> 考前复习最短路径：**知识点 → 例题**，一个点吃透一组题。

入口：[`knowledge-index/`](./knowledge-index/)
