# 高级软件架构师过线私教

这个目录把原来的静态复习资料变成一个“知道你学到哪里、下一步只练最值钱内容”的私人老师。

它的目标不是让你拿高分，而是让**综合知识、案例分析、论文三科分别稳定达到 45 分**。日常以 50–55 分作为安全余量。

## 30 秒开始

### Codex

1. Clone 本仓库并在 Codex 中打开仓库目录。
2. 直接说：`开始私教，我只求考过。`
3. Codex 会读取根目录 `AGENTS.md`，建立仅保存在本地 `.study/` 的私人档案。

### Claude Code

打开仓库后说：`使用 senior-architect-pass-coach，开始私教。`

### 其他 AI

把 [通用启动提示词](./prompts/generic-chat.md) 与本仓库一并提供给 AI。普通聊天产品无法直接写本地文件时，让它在每次结束时输出状态更新，下次对话重新上传自己的私人状态。

## 本地考试终端

Agent 始终是学习入口；网页只负责提供接近正式机考的作答体验，不承载聊天、模型调用或 API Key。由 Agent 或考生在仓库根目录启动：

```bash
python3 scripts/serve.py
```

然后打开 <http://localhost:8420>。考试页提供 75 题答题卡、150 分钟倒计时、标记与拿不准状态、刷新恢复、两次确认交卷和考后错因反馈。原始答卷与错因只写入本机 `.study/`，当前 Agent 可直接读取并据此安排下一轮训练。

## 它会记住什么

- 距离考试还有多久、每天能学多少分钟；
- 综合、案例、论文三科各自的真实测量证据；
- 每个稳定教学考点在“识别 / 应用 / 产出”三种能力上的掌握度；
- 哪些题是猜对的、错因是什么、何时需要重做；
- 案例主赛道和论文匿名项目素材。

私人数据默认写入：

```text
.study/
├── profile.json        # 考期、时间预算、匿名背景
├── state.json          # 三科状态与考点掌握度
├── attempts.jsonl      # 只追加的作答证据
├── postmortems.jsonl   # 只追加的考后错因补充（按需创建）
├── dashboard.md        # 人类可读进度面板
└── paper-project.md    # 论文匿名项目素材（按需创建）
```

整个 `.study/` 已被 Git 忽略。不要使用 `git add -f .study`，不要把真实公司、客户、系统或个人信息写入公共仓库、Issue 或 PR。

## 常用说法

| 你说 | 私教会做 |
|---|---|
| `开始私教` | 建档或恢复进度，安排轻量诊断 |
| `今天学什么？` | 选择当前最高收益任务并直接开始 |
| `来 10 道题` | 从到期错题和高频薄弱点出题 |
| `复习错题` | 按遗忘节奏做变式与跨日复测 |
| `练案例` | 选择 ATAM 或已确定的案例主赛道，按得分点估分 |
| `练论文` | 围绕一个匿名项目练选题、摘要、提纲或整篇 |
| `模拟考试` | 独立计时并记录真实分数证据 |
| `看看进度` | 分别显示三科风险、证据等级和下一步 |
| `今天收工` | 写入本次证据并安排下次复习 |

斜杠形式 `/start`、`/today`、`/quiz`、`/review`、`/case`、`/essay`、`/mock`、`/status`、`/done` 只是别名；自然语言是主入口。

## 可选的本地状态工具

智能体会在后台调用标准库脚本，也可以手动使用：

```bash
# 建档
python3 scripts/tutor.py --data-dir .study init \
  --exam-date 2026-11-01 --daily-minutes 45

# 查看三科状态
python3 scripts/tutor.py --data-dir .study status

# 推荐下一项
python3 scripts/tutor.py --data-dir .study recommend

# 诊断后固定个人路线（案例 1–3 条、论文 1–3 个主题）
python3 scripts/tutor.py --data-dir .study configure \
  --case-track C01.CASE_ATAM --case-track C02.CASE_DATABASE \
  --essay-theme P01.ESSAY_ARCHITECTURE \
  --skip-topic 'K07.REALTIME_EMBEDDED=考前低收益，暂时只保留保命卡'

# 记录一次作答（示例）
python3 scripts/tutor.py --data-dir .study record \
  --topic K19.ATAM_TACTICS --skill recognition \
  --score 4 --max-score 5 --attempt-id demo-atam-001 \
  --item-id exam-bank/12-atam-evaluation.md#3 \
  --source exam-bank/12-atam-evaluation.md

# 完整限时论文证据（缺少完整性、用时或 2500 字均不会计为过线）
python3 scripts/tutor.py --data-dir .study record \
  --topic P01.ESSAY_ARCHITECTURE --skill production \
  --score 52 --max-score 75 --attempt-id essay-2026-08-10-001 \
  --item-id essay-prompt-architecture-001 --mode full_timed \
  --duration-seconds 7200 --word-count 2700 --complete

# 记录一科限时模考
python3 scripts/tutor.py --data-dir .study mock \
  --subject comprehensive --mock-id 2026-08-10-comp-001 \
  --paper-id 2025上 --score 48 --max-score 75 \
  --duration-minutes 140 --complete

# 检查内容、状态与隐私设置
python3 scripts/tutor.py --data-dir .study doctor
```

脚本不联网、不上传数据、没有第三方依赖。状态格式、掌握判据和排课公式见 [进度协议](./PROGRESS_PROTOCOL.md)。

## 第一版边界

- 历年卷用于统计考频，但其中部分是回忆版或缺失题，不直接全部纳入自动判分。
- 确定性选择题优先使用 `exam-bank/` 中带答案和解析的自编题。
- 案例与论文分数只能称为“AI 估分”，并必须展示评分依据。
- 没有完整限时证据时，只显示“待诊断/低置信度”，不制造精确通过率。
- 第一版使用必填的稳定 `item_id` 追踪独立题目；公共题库的全量题目级映射仍会继续细化。当前对容易混淆的聚合考点已用必填 `facet` 强制覆盖子主题，其他题目由私教按资源定位并保留来源。

## 维护者入口

- 智能体规范：[`.claude/agents/senior-architect-pass-coach.md`](../.claude/agents/senior-architect-pass-coach.md)
- 高频课程表：[`curriculum.json`](./curriculum.json)
- 进度协议：[`PROGRESS_PROTOCOL.md`](./PROGRESS_PROTOCOL.md)
- 公共模板：[`templates/`](./templates/)

运行验收：

```bash
python3 -m unittest discover -s tests -v
```
