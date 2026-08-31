# 私教进度协议 v1

本协议规定“学到哪里”如何被记录和判断。它是教学系统的事实来源，禁止用资料阅读量、聊天轮数或一次答对冒充掌握度。

## 1. 不可变目标

- 合格线：综合、案例、论文**分别 ≥ 45/75**，不能求平均。
- 安全目标：日常测量以 **52/75** 为默认目标，可在 50–55 范围调整。
- 优化目标：最大化三科同时过线概率，而不是最大化总分。
- 分配原则：先补瓶颈科目，再选该科收益最高的考点。

## 2. 私有文件

`.study/` 是每位考生的私人状态目录，必须被 Git 忽略：

| 文件 | 用途 |
|---|---|
| `profile.json` | 考期、每日时间、匿名技术背景 |
| `state.json` | 可重建的当前状态与三科证据摘要 |
| `attempts.jsonl` | 只追加的原始作答事件 |
| `postmortems.jsonl` | 只追加的考后错因补充，与可信交卷记录关联 |
| `dashboard.md` | 便于人阅读的进度面板 |
| `paper-project.md` | 论文项目素材，可能含敏感信息 |

不得把 `.study/` 内容复制到公共题库、范文、提交记录、Issue 或 PR。脚本默认离线运行。

## 3. 稳定考点 ID

`past-papers/` 中的原始 `§N.M` 标签用于来源追溯，但个别历史标签与最新版大纲存在漂移，因此不能直接作为学习进度主键。

[`curriculum.json`](./curriculum.json) 定义稳定教学 ID：

- `Kxx.*`：跨科知识考点；
- `Cxx.*`：案例赛道；
- `Pxx.*`：论文主题。

原标签保存在 `raw_tags`，题目可有一个主考点和多个次考点，但只有稳定 ID 更新进度。

## 4. 三维掌握度

同一知识点分别记录：

| 维度 | 对应能力 | 主要证据 |
|---|---|---|
| `recognition` | 识别、回忆、选择 | 综合选择题、口头闪卡 |
| `application` | 分析、计算、选型、踩关键词 | 案例题、小型架构判断 |
| `production` | 独立组织项目实践并论证 | 论文提纲、段落、完整限时作文 |

考点状态：

```text
unseen → learning → fragile → pass_ready
```

`due` 是按能力维度计算的排课标记，不是掌握状态；识别题到期不能污染同一考点的案例或论文能力。`strategic_skip` 是学习计划决策，也不能伪装成掌握。

最低稳定证据：

- `recognition`：至少 6 个独立题目证据，并在不同日期独立答对至少两次；猜对不计独立掌握。
- `application`：至少两次独立案例练习达到 15/25 等价分，间隔至少 48 小时。
- `production`：至少一次按 75 分制估分、记录实际用时、显式标记完整且不少于 2500 字的作文达到安全线；只写摘要或提纲不能标记 `pass_ready`。

## 5. 作答事件

每次有效作答向 `attempts.jsonl` 追加一个事件：

```json
{
  "attempt_id": "a-20260810-k19-001",
  "topic_id": "K19.ATAM_TACTICS",
  "item_id": "exam-bank/12-atam-evaluation.md#3",
  "facet": null,
  "at": "2026-08-10T20:30:00+08:00",
  "subject": "comprehensive",
  "skill": "recognition",
  "mode": "practice",
  "score": 1,
  "max_score": 1,
  "duration_seconds": 42,
  "confidence": "unsure",
  "wrong_reasons": [],
  "source_type": "self_authored",
  "feedback_seen": false
}
```

要求：

- `attempt_id` 全局唯一；重复写入必须幂等，内容冲突必须拒绝。
- `item_id` 必填并稳定标识一道独立题目；不得用新的 `attempt_id` 兜底。复做同一 `item_id` 可以验证遗忘，但不能冒充多个独立掌握证据。
- `curriculum.json` 声明了 `facets` 的聚合考点，在识别/应用训练中必须记录合法 `facet`；达到题数但未覆盖全部子主题时仍不能 `pass_ready`。
- `source_type` 只能明确标记为 `official_outline`、`real`、`recalled_real`、`self_authored` 或 `simulation`，不得把模拟题称为真题。
- 用户输入无效、尚未回答或只阅读讲解时，不写掌握证据。
- 案例和论文记录得分点与 AI 估分，不能冒充官方成绩。
- 机考页面必须先保存原始答卷，再把考生选择的错因追加到 `postmortems.jsonl`；错因补充不得反向改写原始得分。

推荐错因枚举：

```text
knowledge_gap, recall_failure, concept_confusion, misread,
calculation, application, missing_keyword, weak_tradeoff,
weak_project_detail, no_metric, expression, time_management,
careless, guessed_correct
```

## 6. 三科分数证据

进度面板分别显示：

- `latest_mock_score`：最近一次同科限时成绩；
- `predicted_score`：基于近期同条件证据的保守中心值；
- `lower_bound_score`：用于排课的保守下界；
- `evidence_level`：`cold_start / low / medium / high`；
- `status`：`unmeasured / danger / near / safe`。

没有完整限时证据时不得输出精确预测。单次小测只能用于考点诊断，不能直接外推 75 分制总成绩。

每条模考证据必须使用官方 75 分制，并记录全局唯一 `mock_id`、稳定 `paper_id`、实际用时、完成时间、来源类型和 `complete=true`。重复的 `mock_id` 只能幂等重放；内容冲突必须拒绝。未做完整的卷子、单题小测和归一化的 `1/1` 都不能计为模考。

建议证据等级：

- 0 次完整限时：`cold_start`；
- 1 次：`low`；
- 2 次：`medium`；
- 最近 3 次且条件一致：`high`。

## 7. 排课优先级

先确定科目瓶颈，再确定考点：

```text
subject_gap = clamp((safe_target - lower_bound_score) / 10, 0.25, 1.5)
need = max(1 - mastery, 0.4 × review_due)

priority =
  subject_gap
  × need
  × evidence_confidence
  × (frequency + quick_win + cross_subject_value)
  ÷ max(estimated_minutes / 15, 1)
```

公式允许实现细节调整，但必须保持以下不变量：

1. 未测量科目优先获得诊断，而不是被忽略。
2. 任一科低于 45 时，不继续给强科刷高分。
3. 到期高频错题排在未学低频难点之前。
4. 高频薄弱项排在低频同等薄弱项之前。
5. 已跨日稳定的内容降权，只做周期维护。
6. 同一科最长 3 天不能完全没有练习。
7. 考前不足 3 天停止低频新课，只看保命卡、错题和答题骨架。

默认时间分配：瓶颈科 50%、第二科 30%、最强科 20%。

## 8. 过线最短路径

### 综合知识

优先顺序来自 431 道结构化历年题：

1. §4 软件工程；
2. §6 系统架构；
3. §1 计算机系统；
4. §7 质量属性；
5. 知识产权、英语、数据库等快分点。

低频且耗时内容可战略放弃，但必须明确记录原因。

### 案例分析

- 架构评估 / ATAM 作为高复用默认候选，不假定必考；
- 再从数据库、消息缓存、微服务中依据诊断选择，总计保留 1–3 条个人赛道；
- 诊断后用 `configure` 持久化路线，推荐器不得继续平均铺开所有题型；
- 用“结论 → 理由 → 技术名词/量化”组织答案；
- 每周至少一次三题或等价强度的限时证据。

### 论文

- 只维护一个匿名化、内部一致的项目素材；
- 按历史频率 × 项目适配度 × 表达能力选 1–3 个主题，并保存为个人路线；
- 提纲和摘要用于训练，但只有完整限时作文才能证明过线准备度。

## 9. 间隔复习

答错或脆弱题默认安排：当天变式、1 天、3 天、7 天、14 天。连续跨日独立答对后逐步延长，最长 30 天。

以下情况立即重置为脆弱：

- 原题会做但变式不会；
- 靠猜测答对；
- 只会术语但案例无法应用；
- 论文只有模板，没有自洽项目细节或量化效果。

## 10. 写入与恢复

- 每位考生目录使用独占锁，覆盖完整的读取、幂等判断、事件写入、状态派生和面板更新，禁止并发读改写丢进度。
- `attempts.jsonl` 是事实来源：先原子提交完整事件，再派生 `state.json`。若中途退出，下次命令从事件日志确定性重放，绝不能用重试参数伪造缺失事件。
- 所有替换采用“同目录临时文件 → 内容校验 → `fsync` → 原子替换 → 同步父目录”。建档时即创建有效 `state.json.bak`。
- 遇到空文件、截断 JSON、嵌套字段类型错误、重复 ID 或状态/日志集合不一致时，停止正常写入并报告。
- 修复以事件日志重建状态；先复制保留损坏主文件为 `.corrupt.*`，再原子替换主状态。即使主状态缺失，也允许从日志恢复。
