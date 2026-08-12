# 系统架构设计师过线私教 · 仓库指令

当用户的意图是备考、学习、刷题、复习错题、练案例、练论文、查看进度或安排今日任务时：

1. 先完整读取 [`.claude/agents/senior-architect-pass-coach.md`](./.claude/agents/senior-architect-pass-coach.md)，将其作为本仓库唯一的教师行为规范。
2. 再读取 [`tutor/PROGRESS_PROTOCOL.md`](./tutor/PROGRESS_PROTOCOL.md) 和 [`tutor/curriculum.json`](./tutor/curriculum.json)。
3. 使用 `scripts/tutor.py` 维护 `.study/` 中的私人学习状态；若状态不存在，明确说“不知道当前进度”，先建档和诊断，禁止编造。
4. 个人档案、答题记录、错题、论文项目素材和会话记录默认只能写入根目录 `.study/`；只有用户明确指定时才可写入仓库外的私人目录。不得写入公共题库、范文、Issue 或其他受 Git 跟踪文件；不得使用 `git add -f .study`。
5. 给考生出题时，作答前只展示题干和选项，不展示答案标记、解析或文件中加粗的正确项。

当用户是在维护仓库代码或资料，而不是备考时，按普通仓库协作方式处理，不强制进入私教模式。

<!-- codex-migration:claude-md:2026-08-10 -->
## Migrated Claude Code instructions

# Project guidance

For exam tutoring requests, use the project agent `senior-architect-pass-coach` from [`.claude/agents/senior-architect-pass-coach.md`](./.claude/agents/senior-architect-pass-coach.md). Its rules are the single source of truth for tutoring behavior.

Learner data is private. Store profiles, progress, attempts, mistakes, project experience, and session notes only under `.study/`, which must remain ignored by Git. Never copy private learner data into tracked study materials, issues, or pull requests.

For repository maintenance requests, work normally and do not activate tutoring behavior unless the user is studying for the exam.
