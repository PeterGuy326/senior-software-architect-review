#!/usr/bin/env python3
"""Generate ``tutor/topic-map.md`` from ``tutor/curriculum.json``.

The topic map is a reference the coach reads before recommending questions:

* which stable topic ID maps to which exam-bank / cheatsheet files, and
* which aggregate topics need ``--facet`` when calling ``tutor.py record``.

Keeping the map generated (rather than hand-written) prevents drift the next
time ``curriculum.json`` gains a facet or a new topic.

Usage::

    python3 scripts/gen_topic_map.py            # rewrite tutor/topic-map.md
    python3 scripts/gen_topic_map.py --check    # exit 1 if out of date (for CI)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
CURRICULUM = REPO_ROOT / "tutor" / "curriculum.json"
OUTPUT = REPO_ROOT / "tutor" / "topic-map.md"


def _resource_kind(path: str) -> str:
    if path.startswith("exam-bank/"):
        return "exam-bank"
    if path.startswith("cheatsheets/"):
        return "cheatsheet"
    if path.startswith("notes/"):
        return "notes"
    if path.startswith("past-papers/"):
        return "past-papers"
    if path.startswith("knowledge-index/"):
        return "knowledge-index"
    return "other"


def _has_bank_items(resources: Iterable[str]) -> bool:
    return any(r.startswith("exam-bank/") for r in resources)


def render(curriculum: dict) -> str:
    topics = curriculum.get("topics", [])
    aggregate = [t for t in topics if t.get("facets")]

    lines: list[str] = []
    lines.append("# Topic Map（由脚本生成，请勿手改）")
    lines.append("")
    lines.append(
        "> 由 `python3 scripts/gen_topic_map.py` 从 "
        "[`tutor/curriculum.json`](./curriculum.json) 生成。"
        "若要修改，请改 curriculum.json 后重跑该脚本。"
    )
    lines.append("")
    lines.append("## 1. 聚合考点（`record --facet` 必填）")
    lines.append("")
    if aggregate:
        lines.append("| Topic ID | 名称 | Facets |")
        lines.append("|---|---|---|")
        for t in aggregate:
            facets = " / ".join(f"`{f}`" for f in t["facets"])
            lines.append(f"| `{t['id']}` | {t['name']} | {facets} |")
    else:
        lines.append("_当前无聚合考点。_")
    lines.append("")

    lines.append("## 2. 所有考点 → 资源映射")
    lines.append("")
    lines.append("| Topic ID | 名称 | 科目 | 频次 | 时长(分钟) | 有 exam-bank 题 | 主要资源 |")
    lines.append("|---|---|---|---|---|---|---|")
    for t in topics:
        subjects = "/".join(t.get("subjects", []))
        freq = t.get("frequency_count", "—")
        est = t.get("estimated_minutes", "—")
        resources = t.get("resources", []) or []
        has_bank = "✅" if _has_bank_items(resources) else "⚠️ 无"
        # Show up to 3 resources for readability
        shown = ", ".join(f"`{r}`" for r in resources[:3])
        if len(resources) > 3:
            shown += f" (+{len(resources) - 3})"
        lines.append(
            f"| `{t['id']}` | {t['name']} | {subjects} | {freq} | {est} | {has_bank} | {shown} |"
        )
    lines.append("")

    # Group orphaned topics (no exam-bank items) — these need self-authored
    # questions and must be tagged with ``--source-type self_authored``.
    no_bank = [t for t in topics if not _has_bank_items(t.get("resources", []) or [])]
    if no_bank:
        lines.append("## 3. 无 exam-bank 题的考点（自编题时 `--source-type self_authored`）")
        lines.append("")
        for t in no_bank:
            lines.append(f"- `{t['id']}` — {t['name']}")
        lines.append("")

    lines.append("## 4. exam-bank 文件 → topic 反查")
    lines.append("")
    # Build reverse index for the exam-bank/ resources
    reverse: dict[str, list[str]] = {}
    for t in topics:
        for r in t.get("resources", []) or []:
            if r.startswith("exam-bank/"):
                reverse.setdefault(r, []).append(t["id"])
    for path in sorted(reverse):
        topics_str = ", ".join(f"`{tid}`" for tid in sorted(reverse[path]))
        lines.append(f"- `{path}` → {topics_str}")
    lines.append("")

    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if the generated map differs from the file on disk",
    )
    args = parser.parse_args(argv)

    curriculum = json.loads(CURRICULUM.read_text(encoding="utf-8"))
    rendered = render(curriculum)

    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != rendered:
            print(
                f"error: {OUTPUT.relative_to(REPO_ROOT)} is out of date; "
                "run `python3 scripts/gen_topic_map.py`",
                file=sys.stderr,
            )
            return 1
        return 0

    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(REPO_ROOT)} ({len(rendered)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
