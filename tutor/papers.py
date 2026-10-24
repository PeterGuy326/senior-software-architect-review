"""Paper registry: the built-in high-frequency mock plus learner-imported papers.

Two paper kinds coexist by design:

* **builtin** — the canonical high-frequency simulation paper assembled from
  ``exam-bank/``. Every item carries a stable curriculum ``topic_id``/``facet``,
  so a submission feeds the per-question evidence chain (practice events).
* **imported** — real/recalled exam papers the learner imported into their
  private ``.study/papers/`` directory. These items have *no* curriculum
  mapping; faking one would corrupt mastery data. They therefore only feed the
  subject-level mock evidence chain (one full-paper score event).

Answers never leave the server: ``public_items()`` strips them, exactly like
the built-in paper.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PAPERS_DIRNAME = "papers"
PAPER_ID_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{2,60}$")
IMPORTED_SOURCE_TYPES = {"real", "recalled_real"}


class PaperError(ValueError):
    """A paper file is malformed; surfaced to the learner verbatim."""


def _builtin_meta() -> dict[str, Any]:
    from mock_paper import PAPER_ID, PAPER_TITLE, public_payload

    payload = public_payload()
    return {
        "paper_id": PAPER_ID,
        "title": PAPER_TITLE,
        "source_type": "simulation",
        "question_count": payload["question_count"],
        "duration_seconds": payload["duration_seconds"],
        "pass_line": payload["pass_line"],
        "builtin": True,
        "supports_topic_mapping": True,
    }


def _read_imported(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise PaperError(f"{path.name} 不是合法 JSON：{error}") from error
    if not isinstance(data, dict):
        raise PaperError(f"{path.name} 顶层必须是对象")
    paper_id = data.get("paper_id")
    if not isinstance(paper_id, str) or not PAPER_ID_RE.fullmatch(paper_id):
        raise PaperError(f"{path.name} 的 paper_id 缺失或格式非法")
    if data.get("source_type") not in IMPORTED_SOURCE_TYPES:
        raise PaperError(f"{path.name} 的 source_type 必须是 real 或 recalled_real")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise PaperError(f"{path.name} 缺少 items")
    numbers: set[int] = set()
    for item in items:
        if not isinstance(item, dict):
            raise PaperError(f"{path.name} 的 items 必须全是对象")
        number = item.get("number")
        if not isinstance(number, int) or isinstance(number, bool) or number < 1:
            raise PaperError(f"{path.name} 存在非法题号")
        if number in numbers:
            raise PaperError(f"{path.name} 题号重复：{number}")
        numbers.add(number)
        options = item.get("options")
        if not isinstance(options, list) or len(options) < 2:
            raise PaperError(f"{path.name} 第 {number} 题选项不足")
        if not isinstance(item.get("answer"), str) or not item["answer"]:
            raise PaperError(f"{path.name} 第 {number} 题缺少答案")
        if not isinstance(item.get("stem"), str) or not item["stem"].strip():
            raise PaperError(f"{path.name} 第 {number} 题缺少题干")
    if numbers != set(range(1, len(items) + 1)):
        raise PaperError(f"{path.name} 题号必须从 1 连续编号")
    duration = data.get("duration_seconds")
    if not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
        raise PaperError(f"{path.name} 的 duration_seconds 无效")
    return data


class Paper:
    """Uniform view over builtin and imported papers."""

    def __init__(self, meta: dict[str, Any], private_items: list[dict[str, Any]],
                 public_items: list[dict[str, Any]], passages: list[dict[str, Any]],
                 source_label: str) -> None:
        self.meta = meta
        self.paper_id: str = meta["paper_id"]
        self.title: str = meta["title"]
        self.source_type: str = meta["source_type"]
        self.question_count: int = meta["question_count"]
        self.duration_seconds: int = meta["duration_seconds"]
        self.pass_line: int = meta["pass_line"]
        self.builtin: bool = bool(meta.get("builtin"))
        self.supports_topic_mapping: bool = bool(meta.get("supports_topic_mapping"))
        self._private_items = private_items
        self._public_items = public_items
        self.passages = passages
        self.source_label = source_label

    def private_items(self) -> list[dict[str, Any]]:
        return self._private_items

    def public_payload(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "source_type": self.source_type,
            "question_count": self.question_count,
            "duration_seconds": self.duration_seconds,
            "pass_line": self.pass_line,
            "builtin": self.builtin,
            "supports_topic_mapping": self.supports_topic_mapping,
            "passages": self.passages,
            "items": self._public_items,
        }


def _load_builtin() -> Paper:
    from mock_paper import PAPER_ID, private_items, public_payload

    payload = public_payload()
    return Paper(
        meta=_builtin_meta(),
        private_items=private_items(),
        public_items=payload["items"],
        passages=payload.get("passages", []),
        source_label=f"exam-bank（{PAPER_ID}）",
    )


def _load_imported(data: dict[str, Any], path: Path) -> Paper:
    private_items = []
    public_items = []
    for item in data["items"]:
        question = {
            "id": item.get("id") or f"{data['paper_id']}-{item['number']:02d}",
            "topic_name": item.get("topic_name") or "历年真题",
            "stem": item["stem"],
            "options": item["options"],
            "answer": item["answer"],
            "explanation": item.get("explanation", ""),
        }
        private_items.append({"number": item["number"], "question": question,
                              "topic_id": None, "facet": None})
        public_items.append({
            "number": item["number"],
            "id": question["id"],
            "topic_name": question["topic_name"],
            "stem": question["stem"],
            "options": question["options"],
        })
    meta = {
        "paper_id": data["paper_id"],
        "title": data.get("title") or data["paper_id"],
        "source_type": data["source_type"],
        "question_count": len(data["items"]),
        "duration_seconds": data["duration_seconds"],
        "pass_line": int(data.get("pass_line", 45)),
        "builtin": False,
        "supports_topic_mapping": False,
    }
    return Paper(meta=meta, private_items=private_items, public_items=public_items,
                 passages=data.get("passages", []),
                 source_label=str(path))


def papers_dir(data_dir: Path) -> Path:
    return Path(data_dir) / PAPERS_DIRNAME


def discover_papers(data_dir: Path) -> list[dict[str, Any]]:
    """Metadata for every available paper; builtin first, then imported (sorted)."""
    result = [_builtin_meta()]
    directory = papers_dir(data_dir)
    if directory.is_dir():
        for path in sorted(directory.glob("*.json")):
            try:
                data = _read_imported(path)
            except PaperError:
                continue  # a broken file must not break paper selection
            result.append({
                "paper_id": data["paper_id"],
                "title": data.get("title") or data["paper_id"],
                "source_type": data["source_type"],
                "question_count": len(data["items"]),
                "duration_seconds": data["duration_seconds"],
                "pass_line": int(data.get("pass_line", 45)),
                "builtin": False,
                "supports_topic_mapping": False,
            })
    return result


def known_paper_ids(data_dir: Path) -> set[str]:
    return {paper["paper_id"] for paper in discover_papers(data_dir)}


def load_paper(paper_id: Any, data_dir: Path) -> Paper:
    if paper_id is None or paper_id == "":
        paper_id = _builtin_meta()["paper_id"]
    if not isinstance(paper_id, str) or not PAPER_ID_RE.fullmatch(paper_id):
        raise PaperError("试卷 ID 无效")
    directory = papers_dir(data_dir)
    path = directory / f"{paper_id}.json"
    if path.is_file():
        return _load_imported(_read_imported(path), path)
    if paper_id == _builtin_meta()["paper_id"]:
        return _load_builtin()
    raise PaperError(f"未找到试卷 {paper_id}；可用试卷见 /api/papers")
