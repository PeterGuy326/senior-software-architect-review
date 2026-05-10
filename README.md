# 系统架构设计师（软考高级）复习仓库

> 面向「全国计算机技术与软件专业技术资格（水平）考试 — 系统架构设计师」的自用复习资料库。

## 考试基本信息（需自行与最新官网通知核对）

| 项 | 内容 |
|---|---|
| 资格等级 | 高级 |
| 考试频次 | 一年两次：**5 月 / 11 月** |
| 考试形式 | **机考**（2023 下半年起计算机化考试） |
| 科目 1：综合知识 | 选择题 75 道，**最短 120 分钟 / 最长 150 分钟** |
| 科目 2：案例分析 | 问答题 5 道选 3，与综合连考，合计 240 分钟 |
| 科目 3：论文 | 4 选 1，**120 分钟**，≥ 2500 字 |
| 合格线 | **三科均 ≥ 45 分**，成绩不跨期保留 |
| 官方指定教材 | 《系统架构设计师教程（第 2 版）》叶宏等，清华大学出版社，2022-11，ISBN 9787302619925 |

## 目录结构

```
├── notes/                      # 按教材 20 章 + 新技术的知识笔记（含 11-18 案例章节完整笔记）
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
| 综合知识 | 选择题（含答案+解析） | **320+** | [`exam-bank/`](./exam-bank/) |
| 案例分析 | 完整模拟题（题干+答案+评分） | **26** | [`past-papers/case-types/`](./past-papers/case-types/) |
| 论文 | 仿真模拟论文题（题目+提纲答案） | **21** | [`past-papers/paper-topics/`](./past-papers/paper-topics/) |
| 论文 | 完整范文（3000+ 字/篇，13 主题全覆盖 + 5 高频变体） | **18** | [`past-papers/paper-samples/`](./past-papers/paper-samples/) |
| 论文 | 历年真题清单（2009-2024，64+ 题）+ 主题映射 + 选题决策树 | **1 份** | [`past-papers/essay-questions-by-year.md`](./past-papers/essay-questions-by-year.md) |

### 三科对应速查入口

| 科目 | 主用目录 |
|---|---|
| 📚 **综合知识**（75 选 1） | [`exam-bank/`](./exam-bank/)（选择题题库）+ [`cheatsheets/`](./cheatsheets/) + [`notes/`](./notes/) |
| 🎯 **案例分析**（5 选 3） | [`past-papers/case-types/`](./past-papers/case-types/) |
| ✍️ **论文**（4 选 1） | [`past-papers/paper-topics/`](./past-papers/paper-topics/) |

## 按知识点索引例题（强烈推荐）

> 考前复习最短路径：**知识点 → 例题**，一个点吃透一组题。

入口：[`knowledge-index/`](./knowledge-index/)
