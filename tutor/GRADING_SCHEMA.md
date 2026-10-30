# 确定性判分 · Grading Schema

> 解决"同一份答案两次判分结果不一样"的问题。LLM 只负责**语义命中判断与证据引用**，
> 校验与算分由 `scripts/grade.py` 确定性完成，两边各司其职。

## 为什么需要

此前的判分流程（`quiz-loop-sop.md`）完全由 coach 人格 prompt 驱动：模型每轮对
"踩分点是否命中、扣多少分"自由发挥，导致三个问题：

1. **判分漂移**：同一答案在不同轮次可能得到不同分数；
2. **算分不可审计**：分数是模型口算的，没有结构化证据；
3. **无法沉淀数据**：`.study/attempts.jsonl` 里的分数没有可复算的依据。

引入 rubric/verdict 两份 JSON 后，分数变成**可复算的纯函数**：
`final_score = Σ(命中踩分点权重) − Σ(命中扣分项)`，并夹在 `[0, max_score]`。

## 两个文件

### 1. rubric（评分规则，出题/审核时一次性写好）

```jsonc
{
  "schema_version": 1,
  "question_ref": "case-2024-Q1",
  "subject": "case",              // comprehensive | case | essay
  "max_score": 25,
  "key_points": [                 // 踩分点；weights 之和必须 == max_score
    {
      "id": "KP1",
      "desc": "识别出该场景的核心质量属性为性能",
      "weight": 5,
      "aliases": ["性能", "响应时间", "吞吐量"]   // 可选：同义表述，提示 LLM 命中口径
    }
  ],
  "common_errors": [              // 可选：扣分项
    { "id": "E1", "desc": "将可用性与性能混为一谈", "deduct": 2 }
  ],
  "pass_score": 15,               // 可选；缺省为 max_score × 0.6（对齐 45/75）
  "notes": "评分口径说明（可选）"
}
```

### 2. verdict（判分结果，LLM 每次判分时产出）

```jsonc
{
  "schema_version": 1,
  "question_ref": "case-2024-Q1",
  "points": [                     // 必须覆盖 rubric 的每一个 key_point，且各出现一次
    { "id": "KP1", "hit": true,  "evidence": "考生原文：「系统要在 2 秒内响应……」" },
    { "id": "KP2", "hit": false }
  ],
  "errors_hit": ["E1"],           // 可选：命中的扣分项 id
  "typos": ["枷锁→架构"],          // 可选：错别字清单
  "comment": "总评一句话（可选）"
}
```

## 命令

```bash
# 出题时：生成 rubric 模板（weights 自动均分且总和 == max）
python3 scripts/grade.py scaffold --ref case-2024-Q1 --subject case --max 25 --points 5

# 入库前：校验 rubric（weights 总和、id 唯一性、字段合法性）
python3 scripts/grade.py validate rubrics/case-2024-Q1.json

# 判分时：LLM 产出 verdict 后，校验 + 确定性算分
python3 scripts/grade.py grade \
  --rubric rubrics/case-2024-Q1.json \
  --verdict .study/verdicts/case-2024-Q1.json \
  --out .study/verdicts/case-2024-Q1.report.json
```

`grade` 输出的 report 包含 `final_score`、`passed`、逐点命中与证据、扣分明细、
错别字——可直接被人阅读，也可被脚本消费。

## 在 quiz-loop 中的接入方式

案例/论文题判分时，把 SOP 的"按得分点估分"一步替换为：

1. 取该题的 rubric（无则先用 `scaffold` 起模板、agent 补全踩分点后经审核入库）；
2. agent 阅读考生答案 + rubric，**只**输出 verdict JSON（命中与否 + 证据引用）；
3. 运行 `grade.py grade` 得到确定性分数与报告；
4. `tutor.py record ... --score <final_score>` 照常记档，verdict 与 report 归档到
   `.study/verdicts/`（该目录已被 git 忽略，不要提交真实作答内容）。

客观题（四选一）不经过此流程，仍由 `tutor.py` 直接比对答案键。

## 隐私边界

rubric 属于题库资产，可提交到仓库；**verdict、report 与考生答案只写 `.study/`**，
遵守根目录 `AGENTS.md` 与 `tutor/PROGRESS_PROTOCOL.md` 的隐私约定。
