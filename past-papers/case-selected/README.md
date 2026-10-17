# 案例真题精选：必选题 + 四选二

面向数据库 / MySQL、Redis、Cache-Aside 和 Web 方向的跨年份案例练习。共五道大题，第一题必做，后四题任选两道；每题 25 分，练习总分 75 分，建议 90 分钟。

这是公开回忆版的精选组卷（`recalled_real`），不是某一年的完整原卷或官方标准答案。真实考试未必同时提供四道软件方向选做题，必选题也不固定考 ATAM。

## 直接下载

- [题目册（14 页，含填空图表与空白作答页）](pdf/系统架构设计师_案例真题精选_必选加四选二.pdf)
- [题目与答案（15 页，每道大题后附参考答案与采分关键词）](pdf/系统架构设计师_案例真题精选_必选加四选二_题目与答案.pdf)

| 精选题号 | 年份 / 原题号 | 内容 |
|---|---|---|
| 一，必选 | 2024 下，试题一 | 质量属性、Ping/Echo 与心跳 |
| 二，选做 | 2026 上，试题三 | 数据库并发控制、Redis 优化 |
| 三，选做 | 2025 下，批次一试题四 | Redis 数据类型、持久化、内存淘汰 |
| 四，选做 | 2024 下，试题二 | Cache-Aside 流程与并发一致性 |
| 五，选做 | 2024 下，试题四 | Web 分层、分词器、RESTful |

## 本地重建

Python 3.10 及以上，依赖安装和生成命令：

```bash
python3 -m pip install -r scripts/requirements-case-pdf.txt
python3 scripts/build_selected_case_pdf.py
python3 scripts/build_selected_case_pdf.py --with-answers
```

默认覆盖本目录 `pdf/` 下的对应 PDF。若只做本地预览，可指定输出目录：

```bash
python3 scripts/build_selected_case_pdf.py --with-answers --output-dir output/pdf
```

生成器通过自身路径定位仓库，可从其他工作目录执行。它只读取仓库内三个年份的案例 Markdown、`scripts/selected_case_answers.py` 和本目录三张图示，不读取学习状态，不访问外网，也不依赖临时文件或本机绝对路径。PDF 元数据固定，使用相同依赖重建可得到相同文件。

## 来源与已知差异

题面来自 [`2024下.md`](../case-by-year/2024下.md)、[`2025下.md`](../case-by-year/2025下.md)、[`2026上.md`](../case-by-year/2026上.md)。保留背景、分值和填空 / 简答形式，仅校正明显错字和排版。参考答案为学习整理，未编造官方逐项评分。

图表补全的公开来源：

- 需求分类表：[希赛网公开整理](https://www.educity.cn/rk/5437194.html)，按原表转录为空白表格。
- Redis 类型表：[软考在线样张第 34 页](https://www.rkpass.cn/yangzhang/4_80_1.pdf)，按原表转录。
- `assets/cache-aside-read.png`：[公开回忆文章](https://jishuzhan.net/article/1900600614273495041)中的读取填空图，图片原址为 `https://i-blog.csdnimg.cn/direct/3bd745766d6a42e48e18adfba089042c.png`。
- `assets/cache-aside-write.png`：同一文章中的更新填空图，图片原址为 `https://i-blog.csdnimg.cn/direct/1d8f8a98c8dd42afb3f5b741130248aa.png`。
- `assets/web-architecture-blanks.png`：[公开复原文章](https://jishuzhan.net/article/2041681427436208129)中的八空图，图片原址为 `https://i-blog.csdnimg.cn/direct/6defde8e82f8467bb631111f4b4ca49f.png`。

图示保留来源署名，未附答案图，不把回忆复原图称为官方原图。源图及题目的权利归原权利人，供学习参考；如需移除可在仓库反馈。

Redis 的“好友信息发布 / 订阅”在公开题库填空口径中归为 LIST，但真正的 Pub/Sub 使用 PUBLISH / SUBSCRIBE。答案页明确区分题库口径与工程实现。此外校正了 MySQL MVCC 与写锁、缓存最终一致性边界，以及分词器规则等容易误记的表述。

此公开目录仅包含通用学习资料、来源与生成工具，不包含个人成绩、答题记录、考期或项目素材。
