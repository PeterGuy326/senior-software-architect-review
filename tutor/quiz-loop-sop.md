# 答题循环 SOP · Quiz Loop Runtime

> 出题 / 作答 / 判分 / 记档 / 反馈 / 换科 的运行时管道。
> 与 [`tutor/PROGRESS_PROTOCOL.md`](./PROGRESS_PROTOCOL.md)（记档规则）和
> [`.claude/agents/senior-architect-pass-coach.md`](../.claude/agents/senior-architect-pass-coach.md)（教师人格）
> 配合使用。本文只讲**怎么把一轮客观题跑完并落盘**，不覆盖案例/论文的完整训练循环
> （那部分在 coach 人格里）。

## 何时用

- 用户说：复习 / 学习 / 保分 / 过线 / 私教 / 继续答题 / 换科 / 出题 / 出下一题 / 再来一组
- 用户已答完一屏、等你判分和下一屏
- 用户明确要求"选择器点选式"作答

**不用**这套流程的场景：
- 只讲教材、不考核（passive lecture）
- 案例题、论文题的完整训练（用 coach 人格里的对应流程）
- `.study/` 损坏或缺失 → 先按 coach 人格里的建档步骤走

## 前置检查

进入循环前必须过：
- CWD 在本仓库根，`python3 scripts/tutor.py --help` 正常
- 已读 [`PROGRESS_PROTOCOL.md`](./PROGRESS_PROTOCOL.md) 与
  [`.claude/agents/senior-architect-pass-coach.md`](../.claude/agents/senior-architect-pass-coach.md)
- `.study/` 存在（若无，先按 coach 人格建档）
- 已跑过 `python3 scripts/tutor.py doctor`，三项 PASS

## Step 1 · 引擎推荐下一考点

```bash
python3 scripts/tutor.py recommend --limit 6
# 若要切换科目：
python3 scripts/tutor.py recommend --subject case --limit 6
python3 scripts/tutor.py recommend --subject essay --limit 6
```

从输出取**优先级最高、且有 exam-bank 题**的考点。
"有没有 exam-bank 题"用
[`tutor/topic-map.md`](./topic-map.md)（脚本自动生成）查。

若 recommend 头部考点在 topic-map 的"无 exam-bank 题"清单里（`C01–C04`、
`P01–P06` 等），需要自编题，并在 record 时打 `--source-type self_authored`。

## Step 2 · 题目脱敏

exam-bank 的题目块结构：

```
### N. 题干（可能含 **加粗关键词**）

A. 选项文本

B. 选项文本

C. 选项文本

✅ **D. 正确选项文本**

**答案**：D
**解析**：……
---
```

`✅` / 整行 `**...**` / `**答案**：X` / `**解析**：` 都是内联的。**绝对不要直接把这段贴给用户**。

用 `scripts/sanitize_bank.py` 剥离：

```bash
python3 scripts/sanitize_bank.py exam-bank/07-software-engineering.md 1 4 6
```

输出是 JSON 数组，每项含 `stem` / `options[]` / `correct` / `explanation`。
`correct` 与 `explanation` **只**用于判分和作答后反馈，**不**在作答前回显。

## Step 3 · AskUserQuestion 点选出题

学员偏好点选。`AskUserQuestion` 的正确姿势：

- 每次调用 ≤ 4 题（工具上限）
- `label` 只放选项字母：`"A"` / `"B"` / `"C"` / `"D"`（`label` 有 12 字符限制）
- `question` 放完整题干（含"下列错误的是"这类否定词）
- `options[].description` 放该选项的**完整文本**
- `header` 放很短的题目标签，如 `"Q1 瀑布模型"`

11 题拆成 4+4+3，最后一屏可以补一道"整体把握度"自评问题
（`稳 / 不确定 / 蒙`）。

**反面示例（不要这样写）**：
- `label: "A. 严格按顺序..."` ❌（超长 + 违反 12 字符限制）
- `label: "瀑布顺序描述"` ❌（label 应是选项标识，不是题干）
- 把 `correct` 或 `✅` 塞进 `description` ❌（泄题）

## Step 4 · 逐题 record 入档

每答完一屏，立即按题逐条 record：

```bash
python3 scripts/tutor.py record \
  --attempt-id a-YYYYMMDD-dNN \
  --topic <K编号.XXX> \
  --item-id 'exam-bank/<file>.md#<N>' \
  --skill recognition \
  --subject comprehensive \
  --mode diagnostic \
  --score 0|1 --max-score 1 \
  --confidence sure|unsure|guessed \
  --source-type past_paper|self_authored
```

### 聚合考点必须传 `--facet`

以下考点漏掉 `--facet` 会报错或数据被并入 `default`（详见
[`tutor/topic-map.md`](./topic-map.md#1-聚合考点record---facet-必填)）：

| Topic | Facets |
|---|---|
| `K05.TEST_CMMI_PATTERNS` | `testing` / `cmmi` / `design_patterns` |
| `K06.DESIGN_DATA_VIEWS` | `high_level_design` / `data_design` / `uml_views` |
| `K12.PATTERNS_SOA_MICROSERVICES` | `design_patterns` / `soa` / `microservices` |
| `K13.VIEWS_SOA_LAYERING` | `four_plus_one` / `soa` / `layering` |

上表由 [`scripts/gen_topic_map.py`](../scripts/gen_topic_map.py) 从
`curriculum.json` 生成。**发现出入以 topic-map.md 为准。**

### 证据分级（详见 PROGRESS_PROTOCOL §4）

| 场景 | record？ | skill | mode | 能升 pass_ready？ |
|---|---|---|---|---|
| 客观题、闭卷、答对、`sure` | ✅ | recognition | diagnostic/practice | 是（累积 6 条证据 + 跨日 2 次） |
| 答对但 `guessed` | ✅ | recognition | diagnostic | 否，只算 fragile |
| 答错 | ✅ | recognition | diagnostic | 否，进 1/3/7/14 复习队列 |
| 案例独立作答 + 逐项估分 | ✅ | application | practice/mock | 需 2 次 15/25 等价分 |
| 案例只看讲解未作答 | ⚠️ 只写 note | application | practice | 否 |
| 论文口述骨架 | ✅ | application | practice | 否 |
| 论文限时成文 ≥ 2500 字 + 估分 | ✅ | production | mock | 需 2 篇达安全线 |
| 学员纯聊天没作答 | ❌ | — | — | — |

record 完再跑 `python3 scripts/tutor.py status` 确认落盘。

## Step 5 · 反馈与换科

对每道错题给三件套（口头即可，不再走 AskUserQuestion 免得打断节奏）：

1. **错因分类**：
   - `recall_failure`：概念记得但顺序/名字想不起来
   - `concept_confusion`：混淆了两个相邻概念（例：CMM 老版 vs CMMI）
   - `careless_reading`：题干"错误的是/不属于"读反
   - `knowledge_gap`：完全没学过
   - `application_error`：知识点会但套错场景（案例常见）

2. **最小记忆钩子**：一句口诀 / 一张对比表 / 一个反例。
   例：
   > RUP 四阶段：**"初精构移"**——初定边界、精立架构（含风险消除）、构建功能、移交用户
   > CMMI：**初·管·定·量·优**（L2 现在叫 Managed，老 CMM 才叫 Repeatable）

3. **一道变式题**（口头答）

反馈完再走 `recommend` 换下一考点；连续答对 2 组后主动提"换科"。

## Boundaries

- ❌ 用户未作答，不写任何 `record`
- ❌ 蒙对不记 pass_ready，只算 fragile / learning
- ❌ 单科 11 题小测不外推 75 分制成绩——限时整卷模考才是硬证据
- ❌ 案例/论文的作答用 `--skill application` 或 `production`，不用 `recognition`
- ❌ 案例只看讲解未作答：不算掌握证据
- ❌ 作答前不展示 cheatsheet、参考答案、加粗正解
- ❌ 不主动展示 `.study/` 的原始 JSON（除非用户明确问）

## Troubleshooting

| 症状 | 原因 | 处理 |
|---|---|---|
| `record` 报 `--facet is required` | 聚合考点漏 facet | 查 [`topic-map.md`](./topic-map.md) 补 facet |
| topic-map 与 curriculum 不一致 | 有人改了 curriculum 没重跑生成脚本 | `python3 scripts/gen_topic_map.py` |
| 学员答案里选项字母对不上 | label 用了字母以外内容 | 回 Step 3 校验 label 只放 A/B/C/D |
| status 仍显示 `unmeasured` | 单题小测不能升 measured | 限时 65 题整卷模考才升级 |
| 学员嫌打字慢改点选 | 走过一次就立刻切 AskUserQuestion | 后续每屏都点选，不要回退 |
| 学员直接要答案 | PROGRESS_PROTOCOL 禁止直接给答案 | 走 scaffolding：给方法 + 让 TA 填空 |

## Verification（每轮循环收尾自检）

答完一组、准备下一组前，快速过一遍：

- [ ] 每题都 `record` 了，`status` 里 attempt 数增加
- [ ] 聚合考点每条都带了 `--facet`
- [ ] 蒙对/不确定的题 `--confidence` 标了 `unsure` / `guessed`
- [ ] 错题给了错因 + 记忆钩子 + 变式题
- [ ] 没把 `✅` / `**答案**` / `**解析**` 泄给学员
- [ ] 没有硬贴 exam-bank 原文（一律走 `sanitize_bank.py`）

全部打勾才进入下一轮 `recommend`。

## 相关工具

| 工具 | 位置 | 作用 |
|---|---|---|
| CLI | [`scripts/tutor.py`](../scripts/tutor.py) | init / status / recommend / record / doctor |
| 脱敏器 | [`scripts/sanitize_bank.py`](../scripts/sanitize_bank.py) | 剥 exam-bank 答案，输出结构化 JSON |
| 考点表生成 | [`scripts/gen_topic_map.py`](../scripts/gen_topic_map.py) | 由 `curriculum.json` 生成 `topic-map.md` |
| 教师人格 | [`.claude/agents/senior-architect-pass-coach.md`](../.claude/agents/senior-architect-pass-coach.md) | 覆盖诊断 / 案例 / 论文全流程决策 |
| 记档协议 | [`PROGRESS_PROTOCOL.md`](./PROGRESS_PROTOCOL.md) | 证据分级、掌握度定义、私隐边界 |
| 考点表 | [`topic-map.md`](./topic-map.md) | 自动生成，切勿手改 |
