#!/usr/bin/env python3
"""把开源真题语料中的「综合知识」试卷导入为本地考试终端可用的试卷 JSON。

输入：``.study/corpus/`` 下的历年真题清洗版 Markdown（由
``scripts/fetch_corpus.py`` 抓取，格式规整：``## 第N题`` + ``- **A.**`` 选项 +
``**正确答案：X**`` + ``**解析：**``）。

输出：``<data-dir>/papers/<paper-id>.json``——只写私人目录，绝不触碰仓库受
Git 跟踪的文件。导入的真题卷在考试终端中以「整卷成绩」计入证据，不伪造逐题
考点归属。

用法：
    python3 scripts/import_paper.py --data-dir .study --all      # 导入语料中全部综合知识试卷
    python3 scripts/import_paper.py --data-dir .study <文件.md>   # 导入指定文件
    python3 scripts/import_paper.py --data-dir .study --list     # 查看已导入试卷
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_SUBDIR = Path("content/02-历年真题-清洗版")
PAPER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{2,60}$")

HEADING_RE = re.compile(r"(?m)^##\s*第(\d+)题\s*$")
OPTION_RE = re.compile(r"^-\s*\*\*([A-F])[.．]\*\*\s*(.+?)\s*$")
ANSWER_RE = re.compile(r"^\*\*正确答案[：:]\s*\*?\*?\s*([A-F])")
FRONTMATTER_RE = re.compile(r"(?s)^---\s*\n(.*?)\n---\s*\n")


class ImportError_(ValueError):
    pass


def parse_frontmatter(raw: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(raw)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"')
    return fields


def parse_paper(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    meta = parse_frontmatter(raw)
    year = meta.get("year", "")
    session = meta.get("session", "")
    subject = meta.get("subject", "")
    if not (year and session):
        raise ImportError_("frontmatter 缺少 year/session，无法生成稳定 paper_id")
    paper_id = f"real-{year}-{session}-{subject or 'comprehensive'}"
    if not PAPER_ID_RE.fullmatch(paper_id):
        raise ImportError_(f"生成的 paper_id 非法：{paper_id}")

    headings = list(HEADING_RE.finditer(raw))
    if not headings:
        raise ImportError_("未找到「## 第N题」结构，可能不是综合知识试卷")

    items: list[dict] = []
    problems: list[str] = []
    for index, heading in enumerate(headings):
        number = int(heading.group(1))
        block_end = headings[index + 1].start() if index + 1 < len(headings) else len(raw)
        block = raw[heading.end():block_end]
        options: list[dict[str, str]] = []
        answer = ""
        stem_lines: list[str] = []
        explanation_lines: list[str] = []
        in_explanation = False
        for line in block.splitlines():
            stripped = line.strip()
            option_match = OPTION_RE.match(stripped)
            if option_match:
                options.append({"key": option_match.group(1), "text": option_match.group(2)})
                continue
            answer_match = ANSWER_RE.match(stripped)
            if answer_match:
                answer = answer_match.group(1)
                continue
            if re.match(r"^\*\*解析\*\*[：:]?", stripped):
                in_explanation = True
                continue
            if stripped in {"", "---"}:
                continue
            if in_explanation:
                explanation_lines.append(stripped)
            elif not options:
                stem_lines.append(stripped)
        stem = " ".join(stem_lines).strip()
        if not stem:
            problems.append(f"第 {number} 题缺少题干")
        if len(options) < 2:
            problems.append(f"第 {number} 题选项不足 {len(options)} 个")
        if not answer:
            problems.append(f"第 {number} 题缺少正确答案")
        if answer and options and answer not in {option["key"] for option in options}:
            problems.append(f"第 {number} 题答案 {answer} 不在选项中")
        items.append({
            "number": number,
            "id": f"{paper_id}-{number:02d}",
            "topic_name": "历年真题",
            "stem": stem,
            "options": options,
            "answer": answer,
            "explanation": " ".join(explanation_lines).strip(),
        })

    if problems:
        raise ImportError_("；".join(problems[:8]) + (" 等" if len(problems) > 8 else ""))

    source_numbers = [item["number"] for item in items]
    if len(set(source_numbers)) != len(source_numbers):
        raise ImportError_("题号重复")
    if any(b <= a for a, b in zip(source_numbers, source_numbers[1:])):
        raise ImportError_("题号不是严格递增")
    if source_numbers and (source_numbers[0] < 1 or source_numbers[-1] > 99):
        raise ImportError_("题号超出 1-99 范围")

    # The exam UI answer sheet needs contiguous 1..N numbering; keep the source
    # number in the item id so evidence stays traceable to the original paper.
    for index, item in enumerate(items, 1):
        item["source_number"] = item["number"]
        item["number"] = index

    gaps = sorted(set(range(source_numbers[0], source_numbers[-1] + 1)) - set(source_numbers))
    title = f"{year}年{'上' if session == 'h1' else '下'}半年 综合知识（真题清洗版）"
    return {
        "paper_id": paper_id,
        "title": title,
        "source_type": "recalled_real",
        "question_count": len(items),
        "duration_seconds": 150 * 60,
        "pass_line": 45,
        "imported_from": str(path),
        "imported_at": _now_iso(),
        "source_number_gaps": gaps,
        "items": items,
    }


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def write_paper(data_dir: Path, paper: dict, force: bool) -> str:
    papers_dir = data_dir / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)
    target = papers_dir / f"{paper['paper_id']}.json"
    if target.exists() and not force:
        return "exists"
    target.write_text(json.dumps(paper, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return "written"


def discover_corpus_files(corpus_dir: Path) -> list[Path]:
    """Only exact-name papers; 回忆版/备选 files map to the same paper_id."""
    if not corpus_dir.is_dir():
        return []
    return sorted(corpus_dir.glob("*-综合知识.md"))


def main() -> int:
    parser = argparse.ArgumentParser(description="导入历年真题综合知识试卷到本地考试终端")
    parser.add_argument("files", nargs="*", help="要导入的真题 Markdown 文件")
    parser.add_argument("--data-dir", default=str(REPO_ROOT / ".study"), help="私人状态目录")
    parser.add_argument("--corpus-dir", default=None,
                        help=f"真题语料目录（默认 <data-dir>/corpus/{DEFAULT_CORPUS_SUBDIR}）")
    parser.add_argument("--all", action="store_true", help="导入语料中全部综合知识试卷")
    parser.add_argument("--force", action="store_true", help="覆盖已导入的同名试卷")
    parser.add_argument("--list", action="store_true", help="只列出已导入试卷")
    args = parser.parse_args()

    data_dir = Path(args.data_dir).expanduser().resolve()
    papers_dir = data_dir / "papers"

    if args.list:
        if not papers_dir.is_dir():
            print("尚未导入任何试卷。先运行 scripts/fetch_corpus.py 抓取语料。")
            return 0
        for path in sorted(papers_dir.glob("*.json")):
            try:
                paper = json.loads(path.read_text(encoding="utf-8"))
                print(f"  {paper['paper_id']}  {paper['title']}  {paper['question_count']} 题")
            except (json.JSONDecodeError, KeyError):
                print(f"  [损坏] {path.name}")
        return 0

    targets: list[Path] = [Path(item).expanduser() for item in args.files]
    if args.all or not targets:
        corpus_dir = Path(args.corpus_dir).expanduser() if args.corpus_dir else data_dir / "corpus" / DEFAULT_CORPUS_SUBDIR
        found = discover_corpus_files(corpus_dir)
        if not found:
            print(f"[FAIL] 在 {corpus_dir} 未找到综合知识试卷。")
            print("       先运行：python3 scripts/fetch_corpus.py --data-dir .study")
            return 1
        targets = found
        print(f"发现 {len(targets)} 套综合知识试卷")

    written = skipped = failed = 0
    for path in targets:
        try:
            paper = parse_paper(path)
            outcome = write_paper(data_dir, paper, force=args.force)
        except (ImportError_, OSError) as error:
            failed += 1
            print(f"  [跳过] {path.name}: {error}")
            continue
        if outcome == "exists":
            skipped += 1
            print(f"  [已存在] {paper['paper_id']}（--force 可覆盖）")
        else:
            written += 1
            gaps = paper.get("source_number_gaps") or []
            notes = []
            if paper["question_count"] != 75:
                notes.append(f"非 75 题（{paper['question_count']}），只存原始答卷")
            if gaps:
                notes.append(f"原卷缺题号 {gaps}")
            note = f"（{'；'.join(notes)}）" if notes else ""
            print(f"  [已导入] {paper['paper_id']}  {paper['question_count']} 题{note}")

    print(f"\n完成：导入 {written} 套，跳过 {skipped} 套，失败 {failed} 套")
    print(f"试卷目录：{papers_dir}")
    print("下一步：python3 scripts/serve.py --data-dir .study，在考试页选择试卷")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
