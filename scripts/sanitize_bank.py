#!/usr/bin/env python3
"""
Sanitize exam-bank blocks for coach-driven quiz sessions.

Reads an exam-bank markdown file, extracts the question blocks whose header
starts with ``### N.`` for the given N values, strips inline answer markers
(``✅``, bold correct-option markers, ``**答案**:`` / ``**答案**：`` lines, and
the trailing ``**解析**:`` / ``**解析**：`` section), and prints a JSON list
to stdout. Each item has::

    {
        "id": "exam-bank/<file>.md#<N>",
        "stem": "<question stem, single line>",
        "options": [{"label": "A", "text": "..."}, ...],
        "correct": ["B"],   # coach-only, DO NOT echo to the learner
        "explanation": "..." # coach-only, only for post-answer feedback
    }

Usage::

    python3 scripts/sanitize_bank.py <path-to-exam-bank.md> <N> [<N> ...]

Example::

    python3 scripts/sanitize_bank.py exam-bank/07-software-engineering.md 1 4 6

Supported option-line formats (learners will never see the raw form):

  * ``A. text`` / ``B. text`` / ``C. text`` / ``D. text``  (bare)
  * ``- A. text``                                           (bulleted)
  * ``✅ **D. text**``                                       (correct marker)
  * ``- **B. text**``                                       (correct via bold)
  * option text may contain inline ``**bold**`` for emphasis
  * an explicit ``**答案**: X`` / ``**答案**：X`` line, when present, wins over
    ``✅`` heuristics.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List


BLOCK_HEADER = re.compile(r"^###\s+(\d+)[.\s]", re.MULTILINE)
# Match option lines in all supported shapes:
#   "A. text", "- A. text", "* A. text", "**A. text**"
# Correct-answer prefixes (``✅`` and outer ``**``) are stripped from the
# probe string before matching so the same regex handles both plain and marked
# lines.
OPTION_LINE = re.compile(
    r"""^\s*
        (?:[-*]\s+)?           # optional bullet marker
        ([A-Z])                # 1: option letter
        [\.\)、]                # separator: dot, right paren, or Chinese enum comma
        \s*
        (.+?)                  # 2: option text (non-greedy)
        \s*$""",
    re.VERBOSE,
)
BOLD_MARK = re.compile(r"\*\*(.+?)\*\*")
ANSWER_LINE = re.compile(
    r"^\s*\*\*\s*答\s*案\s*\*\*\s*[:：]\s*(.+?)\s*$", re.MULTILINE
)
EXPLAIN_LINE = re.compile(
    r"^\s*\*\*\s*解\s*析\s*\*\*\s*[:：]\s*(.*)$", re.MULTILINE
)
SEPARATOR_LINE = re.compile(r"^\s*-{3,}\s*$")
CHECK_MARK = "✅"


def split_blocks(text: str) -> Dict[str, str]:
    """Return a mapping of question number -> raw block text (with header)."""
    blocks: Dict[str, str] = {}
    positions = [(m.start(), m.group(1)) for m in BLOCK_HEADER.finditer(text)]
    for i, (start, num) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        blocks[num] = text[start:end]
    return blocks


def _clean_text(value: str) -> str:
    """Remove residual markers and collapse whitespace."""
    value = value.replace(CHECK_MARK, "")
    value = BOLD_MARK.sub(r"\1", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _probe_option(stripped: str):
    """Return (letter, body, is_marked_correct) or None if not an option line.

    Peels off ``✅`` and outer ``**...**`` wrappers (both of which signal the
    correct answer in exam-bank markdown) before attempting to match the
    option pattern. ``is_marked_correct`` is True when any such marker was
    present.
    """
    marked = False
    probe = stripped

    # Peel ✅ prefix (may be followed by whitespace or **)
    if probe.startswith(CHECK_MARK):
        marked = True
        probe = probe[len(CHECK_MARK):].lstrip()

    # Peel a leading bullet marker so we can inspect the payload
    bullet = ""
    if probe.startswith(("- ", "* ")):
        bullet = probe[:2]
        probe = probe[2:].lstrip()

    # Peel outer ** ... ** wrapping the entire option payload
    if probe.startswith("**") and probe.endswith("**") and len(probe) >= 4:
        marked = True
        probe = probe[2:-2].strip()

    # Restore bullet so OPTION_LINE can still recognise the shape uniformly
    probe = f"{bullet}{probe}" if bullet else probe

    m = OPTION_LINE.match(probe)
    if not m:
        return None
    return m.group(1), m.group(2).strip(), marked


def parse_block(raw: str) -> Dict:
    """Parse one raw block into a structured item."""
    lines = raw.splitlines()
    header = lines[0] if lines else ""
    header_body = re.sub(r"^###\s+\d+[.\s]\s*", "", header).strip()
    header_body = _clean_text(header_body)

    stem_parts: List[str] = [header_body] if header_body else []
    options: List[Dict[str, str]] = []
    correct_from_marker: List[str] = []
    answer_from_line: List[str] = []
    explanation_lines: List[str] = []
    in_explanation = False
    seen_first_option = False

    for line in lines[1:]:
        if SEPARATOR_LINE.match(line):
            in_explanation = False
            continue

        m_ans = ANSWER_LINE.match(line)
        if m_ans:
            answer_from_line = re.findall(r"[A-Z]", m_ans.group(1))
            in_explanation = False
            continue

        m_exp = EXPLAIN_LINE.match(line)
        if m_exp:
            in_explanation = True
            first = m_exp.group(1).strip()
            if first:
                explanation_lines.append(first)
            continue

        if in_explanation:
            if line.strip():
                explanation_lines.append(line.strip())
            continue

        stripped = line.strip()
        if not stripped:
            continue

        probed = _probe_option(stripped)
        if probed is not None:
            label, body, is_marked = probed
            if is_marked:
                correct_from_marker.append(label)
            options.append({"label": label, "text": _clean_text(body)})
            seen_first_option = True
            continue

        # Not an option line. Before the first option → stem continuation.
        # After options started → likely stray/answer hint; drop silently.
        if not seen_first_option:
            stem_parts.append(_clean_text(stripped))

    correct = answer_from_line or correct_from_marker
    return {
        "stem": " ".join(p for p in stem_parts if p).strip(),
        "options": options,
        "correct": sorted(set(correct)),
        "explanation": " ".join(explanation_lines).strip() or None,
    }


def main(argv: List[str]) -> int:
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    numbers = [n.strip() for n in argv[2:] if n.strip()]
    text = path.read_text(encoding="utf-8")
    blocks = split_blocks(text)
    items: List[Dict] = []
    missing: List[str] = []
    for n in numbers:
        raw = blocks.get(n)
        if raw is None:
            missing.append(n)
            continue
        item = parse_block(raw)
        item["id"] = f"{path.as_posix()}#{n}"
        items.append(item)
    if missing:
        print(
            f"warning: missing question numbers in {path}: {', '.join(missing)}",
            file=sys.stderr,
        )
    print(json.dumps(items, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
