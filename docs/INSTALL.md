# 接入指南：把这个仓库变成你的私人过线私教

适合三种人：用 WorkBuddy / Claude Code 的考生、用其他 AI 的考生、想二开的开发者。
全程只需要会说话——建档、诊断、安排学习计划全部由 agent 自动完成。

---

## 方式一：WorkBuddy（推荐，30 秒）

1. 把本仓库作为一个 Skill 装进来（二选一）：
   - **个人级**（所有项目可用）：把仓库复制或克隆到 `~/.workbuddy/skills/senior-architect-coach/`
   - **项目级**（仅当前项目）：克隆到 `<你的工作区>/.workbuddy/skills/senior-architect-coach/`
2. 重启或新开对话，直接说：

   > **开始私教，我只求考过。**

3. agent 会读取 `SKILL.md` → 发现没有 `.study/` → 问你三个问题（考试日期、每天能学多少分钟、有没有考过或模考过）→ 自动建档并给出第一轮诊断。

之后任何时候说「今天学什么」「给我出题」「练一道案例」「汇报进度」，它都会基于你的真实作答记录续接，**不会假装知道你的进度**。

## 方式二：Claude Code

1. 克隆仓库并在 Codex / Claude Code 中打开仓库目录：
   ```bash
   git clone https://github.com/PeterGuy326/senior-software-architect-review.git
   ```
2. 直接说：`开始私教，我只求考过。`
   （仓库根目录的 `AGENTS.md` 会自动把对话路由到私教规范。）

## 方式三：其他 AI（无本地文件写入权限）

1. 把仓库的 `tutor/prompts/generic-chat.md` 连同你需要的资料一起发给 AI。
2. AI 无法写你的本地文件时，让它在每轮结束时输出「状态更新」文本，你保存到本地；下次对话重新上传，它就能续接。

## 你的数据放在哪

- 所有私人数据（档案、答题记录、错题、论文素材）只写仓库内的 `.study/`，该目录被 `.gitignore` 忽略，**永远不会被提交，也不会同步给别人**。
- 换机器 / 重装：拷贝 `.study/` 目录即可完整迁移进度。
- 状态损坏时 agent 会停止写入并尝试从备份恢复，不会静默覆盖。

## 可选：接入历年真题语料与试卷

```bash
# 1. 抓取开源真题 Markdown 语料（只写 .study/corpus/，混合许可，仅个人学习）
python3 scripts/fetch_corpus.py --data-dir .study
# 2. 导入综合知识试卷到本地考试终端（.study/papers/，已支持 2016–2025 共 12 套）
python3 scripts/import_paper.py --data-dir .study --all
```

之后有两个用法：

- **问 agent**：「XX 考点哪年考过」——它会先读语料 INDEX，再定位到具体试卷；
- **考试页刷真题**：`python3 scripts/serve.py` 后在试卷选择器切换。导入的真题卷只记录原始答卷与整卷成绩，不生成逐题错因反馈（真题没有本仓库的考点映射，不伪造归属）。

案例分析的真题导入与模考已在路线图上，见 Issue #19 的后续跟进。

## 常见问题

| 问题 | 答案 |
|---|---|
| 进度会泄露吗？ | 不会。`.study/` 被 git 忽略，且 agent 有隐私红线约束 |
| 三科要同时学吗？ | agent 按「离安全线最远 + 到期复习 + 复用价值」排序，通常案例/论文优先 |
| 可以只用题库不私教吗？ | 可以，`exam-bank/` 是普通 Markdown，但出题前应自行用 `scripts/sanitize_bank.py` 脱敏 |
| 二开 / 提需求 | 直接提 Issue 或 PR（仓库内置「资料纠错 / 功能建议 / 备考打卡」三种模板）；私人数据请不要带进 PR |
| 找考友 | 到 Issue #16 学习小组报到，用「备考打卡」模板每日打卡 |
