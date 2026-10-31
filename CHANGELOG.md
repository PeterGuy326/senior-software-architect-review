# Changelog

## [Unreleased]

### Added

- 确定性判分引擎 `scripts/grade.py`：rubric（踩分点/扣分项 schema）+ verdict（LLM 只做命中判断与证据引用）+ 代码校验算分，主观题分数可复算、可审计；配套 `tutor/GRADING_SCHEMA.md` 接入说明与 22 个单元测试。
- 判分接线：quiz-loop-sop 与 coach 人格的案例/论文判分步骤改为走 grade.py 确定性管线，verdict/report 归档 `.study/verdicts/`。
- 本地综合知识模拟考试终端：75 题高频卷、机考答题卡、限时交卷、确定性判分，以及仅写入 `.study/` 的逐题证据与考后错因反馈。
