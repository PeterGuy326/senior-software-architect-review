#!/usr/bin/env python3
"""Local, dependency-free progress engine for the pass-first exam tutor.

The AI coach owns the conversation; this script owns durable evidence.  It
stores learner data only in ``.study/`` (or an explicitly supplied data
directory) and never performs network requests.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Iterator


SCHEMA_VERSION = 1
REPO_ROOT = Path(__file__).resolve().parents[1]
CURRICULUM_PATH = REPO_ROOT / "tutor" / "curriculum.json"
SUBJECTS = ("comprehensive", "case", "essay")
SKILLS = ("recognition", "application", "production")
WRONG_REASONS = {
    "knowledge_gap",
    "recall_failure",
    "concept_confusion",
    "misread",
    "calculation",
    "application",
    "missing_keyword",
    "weak_tradeoff",
    "weak_project_detail",
    "no_metric",
    "expression",
    "time_management",
    "careless",
    "guessed_correct",
}


class TutorError(RuntimeError):
    """A user-actionable state or input error."""


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now().astimezone()
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise TutorError(f"无效时间：{value!r}，请使用 ISO-8601 格式") from error
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise TutorError(f"无效日期：{value!r}，请使用 YYYY-MM-DD") from error


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def fsync_directory(directory: Path) -> None:
    """Persist directory metadata after an atomic replacement when supported."""

    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(directory, flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_write_bytes(path: Path, content: bytes) -> None:
    """Validate elsewhere, then atomically replace a file in the same directory."""

    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        fsync_directory(path.parent)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def atomic_write_text(path: Path, content: str) -> None:
    atomic_write_bytes(path, content.encode("utf-8"))


def atomic_write_json(path: Path, value: Any) -> None:
    serialized = json_text(value)
    json.loads(serialized)
    atomic_write_text(path, serialized)


@contextmanager
def data_lock(data_dir: Path) -> Iterator[None]:
    """Serialize every read-modify-write cycle for one learner directory."""

    lock_path = data_dir / ".tutor.lock"
    with lock_path.open("a+b") as handle:
        if os.name == "nt":
            import msvcrt

            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def load_json(path: Path, label: str) -> Any:
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise TutorError(f"缺少{label}：{path}") from error
    if not content.strip():
        raise TutorError(f"{label}为空，拒绝静默覆盖：{path}")
    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise TutorError(f"{label}损坏或不是有效 JSON，拒绝静默覆盖：{path}") from error


def load_curriculum() -> dict[str, Any]:
    curriculum = load_json(CURRICULUM_PATH, "课程表")
    if not isinstance(curriculum, dict) or not isinstance(curriculum.get("topics"), list):
        raise TutorError("tutor/curriculum.json 缺少 topics 数组")
    if curriculum.get("schema_version") != SCHEMA_VERSION:
        raise TutorError("课程表 schema_version 不受支持")

    seen: set[str] = set()
    for topic in curriculum["topics"]:
        if not isinstance(topic, dict) or not isinstance(topic.get("id"), str):
            raise TutorError("课程表包含无效考点")
        topic_id = topic["id"]
        if topic_id in seen:
            raise TutorError(f"课程表考点 ID 重复：{topic_id}")
        facets = topic.get("facets", [])
        if (
            not isinstance(facets, list)
            or any(not isinstance(facet, str) or not facet for facet in facets)
            or len(facets) != len(set(facets))
        ):
            raise TutorError(f"课程表考点 {topic_id} facets 无效")
        seen.add(topic_id)
    groups = curriculum.get("strategy", {}).get("comprehensive_cold_start_groups", [])
    if not isinstance(groups, list) or any(not isinstance(group, list) for group in groups):
        raise TutorError("课程表 comprehensive_cold_start_groups 无效")
    grouped_ids = [topic_id for group in groups for topic_id in group]
    if len(grouped_ids) != len(set(grouped_ids)) or any(
        topic_id not in seen for topic_id in grouped_ids
    ):
        raise TutorError("课程表冷启动分组包含重复或未知考点 ID")
    return curriculum


def topic_map(curriculum: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {topic["id"]: topic for topic in curriculum["topics"]}


def state_paths(data_dir: Path) -> dict[str, Path]:
    return {
        "profile": data_dir / "profile.json",
        "state": data_dir / "state.json",
        "attempts": data_dir / "attempts.jsonl",
        "dashboard": data_dir / "dashboard.md",
    }


def blank_subject() -> dict[str, Any]:
    return {
        "mock_scores": [],
        "latest_mock_score": None,
        "predicted_score": None,
        "lower_bound_score": None,
        "evidence_level": "cold_start",
        "last_practiced_at": None,
        "evidence_count": 0,
    }


def new_state(curriculum: dict[str, Any], created_at: str) -> dict[str, Any]:
    strategy = curriculum.get("strategy", {})
    return {
        "schema_version": SCHEMA_VERSION,
        "strategy": {
            "pass_line": float(strategy.get("pass_line", 45)),
            "safe_target": float(strategy.get("safe_target", 52)),
            "case_tracks": ["C01.CASE_ATAM"],
            "essay_themes": [],
            "case_tracks_configured": False,
            "essay_themes_configured": False,
            "strategic_skips": {},
        },
        "subjects": {subject: blank_subject() for subject in SUBJECTS},
        "topics": {},
        "applied_attempt_ids": [],
        "created_at": created_at,
        "last_session_at": None,
    }


def require_number_or_none(value: Any, label: str) -> None:
    if value is not None and (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(float(value))
    ):
        raise TutorError(f"state.json {label} 必须是数字或 null")


def validate_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict):
        raise TutorError("state.json 顶层必须是对象")
    if state.get("schema_version") != SCHEMA_VERSION:
        raise TutorError(
            f"state.json schema_version={state.get('schema_version')!r} 不受支持"
        )
    subjects = state.get("subjects")
    if not isinstance(subjects, dict) or any(
        not isinstance(subjects.get(subject), dict) for subject in SUBJECTS
    ):
        raise TutorError("state.json 缺少三科独立状态")
    if not isinstance(state.get("topics"), dict):
        raise TutorError("state.json topics 必须是对象")
    strategy = state.get("strategy")
    if not isinstance(strategy, dict):
        raise TutorError("state.json strategy 必须是对象")
    for key in ("pass_line", "safe_target"):
        require_number_or_none(strategy.get(key), f"strategy.{key}")
    for key in ("case_tracks", "essay_themes"):
        values = strategy.get(key)
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            raise TutorError(f"state.json strategy.{key} 必须是字符串数组")
    for key in ("case_tracks_configured", "essay_themes_configured"):
        if not isinstance(strategy.get(key), bool):
            raise TutorError(f"state.json strategy.{key} 必须是布尔值")
    skips = strategy.get("strategic_skips", {})
    if not isinstance(skips, dict) or any(
        not isinstance(topic_id, str) or not isinstance(reason, str)
        for topic_id, reason in skips.items()
    ):
        raise TutorError("state.json strategy.strategic_skips 必须是字符串映射")
    applied_ids = state.get("applied_attempt_ids")
    if not isinstance(applied_ids, list) or any(
        not isinstance(item, str) or not item for item in applied_ids
    ):
        raise TutorError("state.json applied_attempt_ids 必须是非空字符串数组")
    if len(applied_ids) != len(set(applied_ids)):
        raise TutorError("state.json applied_attempt_ids 存在重复")

    for subject_name in SUBJECTS:
        subject = subjects[subject_name]
        if not isinstance(subject.get("mock_scores"), list):
            raise TutorError(f"state.json subjects.{subject_name}.mock_scores 必须是数组")
        if subject.get("evidence_level") not in ("cold_start", "low", "medium", "high"):
            raise TutorError(f"state.json subjects.{subject_name}.evidence_level 无效")
        evidence_count = subject.get("evidence_count")
        if not isinstance(evidence_count, int) or isinstance(evidence_count, bool) or evidence_count < 0:
            raise TutorError(f"state.json subjects.{subject_name}.evidence_count 无效")
        for key in ("latest_mock_score", "predicted_score", "lower_bound_score"):
            require_number_or_none(subject.get(key), f"subjects.{subject_name}.{key}")
        if subject.get("last_practiced_at") is not None:
            parse_datetime(subject["last_practiced_at"])
        seen_mocks: set[str] = set()
        for mock in subject["mock_scores"]:
            if not isinstance(mock, dict) or not isinstance(mock.get("mock_id"), str):
                raise TutorError(f"state.json subjects.{subject_name}.mock_scores 包含无效记录")
            if mock["mock_id"] in seen_mocks:
                raise TutorError(f"state.json 模考 ID 重复：{mock['mock_id']}")
            seen_mocks.add(mock["mock_id"])
            if not isinstance(mock.get("paper_id"), str) or not mock["paper_id"]:
                raise TutorError(f"state.json 模考 {mock['mock_id']} 缺少 paper_id")
            parse_datetime(mock.get("at"))
            for key in ("score", "max_score", "score_75", "duration_minutes"):
                value = mock.get(key)
                if (
                    not isinstance(value, (int, float))
                    or isinstance(value, bool)
                    or not math.isfinite(float(value))
                ):
                    raise TutorError(f"state.json 模考 {mock['mock_id']}.{key} 无效")
            if mock.get("complete") is not True:
                raise TutorError(f"state.json 模考 {mock['mock_id']} 不是完整证据")

    for topic_id, topic in state["topics"].items():
        if not isinstance(topic_id, str) or not isinstance(topic, dict):
            raise TutorError("state.json topics 包含无效考点")
        mastery = topic.get("mastery")
        if not isinstance(mastery, dict):
            raise TutorError(f"state.json topics.{topic_id}.mastery 必须是对象")
        if topic.get("status") not in ("unseen", "learning", "fragile", "pass_ready"):
            raise TutorError(f"state.json topics.{topic_id}.status 无效")
        if topic.get("last_attempt_at") is not None:
            parse_datetime(topic["last_attempt_at"])
        if topic.get("next_review_at") is not None:
            parse_date(topic["next_review_at"])
        for skill, record in mastery.items():
            if skill not in SKILLS or not isinstance(record, dict):
                raise TutorError(f"state.json topics.{topic_id} 包含无效能力维度")
            count = record.get("attempt_count")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise TutorError(f"state.json topics.{topic_id}.{skill}.attempt_count 无效")
            for key in ("score_sum", "max_score_sum", "mastery"):
                if not isinstance(record.get(key), (int, float)) or isinstance(record.get(key), bool):
                    raise TutorError(f"state.json topics.{topic_id}.{skill}.{key} 无效")
                if not math.isfinite(float(record[key])):
                    raise TutorError(f"state.json topics.{topic_id}.{skill}.{key} 不是有限数")
            if record.get("status") not in ("unseen", "learning", "fragile", "pass_ready"):
                raise TutorError(f"state.json topics.{topic_id}.{skill}.status 无效")
            for key in ("attempted_items", "qualified_evidence", "successful_dates"):
                if not isinstance(record.get(key), list):
                    raise TutorError(f"state.json topics.{topic_id}.{skill}.{key} 必须是数组")
            attempted_items = record["attempted_items"]
            if any(not isinstance(item, str) or not item for item in attempted_items):
                raise TutorError(f"state.json topics.{topic_id}.{skill}.attempted_items 无效")
            if len(attempted_items) != len(set(attempted_items)):
                raise TutorError(f"state.json topics.{topic_id}.{skill}.attempted_items 重复")
            for evidence in record["qualified_evidence"]:
                if (
                    not isinstance(evidence, dict)
                    or not isinstance(evidence.get("attempt_id"), str)
                    or not isinstance(evidence.get("item_id"), str)
                ):
                    raise TutorError(f"state.json topics.{topic_id}.{skill} 资格证据无效")
                parse_datetime(evidence.get("at"))
                ratio = evidence.get("ratio")
                if (
                    not isinstance(ratio, (int, float))
                    or isinstance(ratio, bool)
                    or not math.isfinite(float(ratio))
                ):
                    raise TutorError(f"state.json topics.{topic_id}.{skill} 资格比例无效")
            for successful_date in record["successful_dates"]:
                if not isinstance(successful_date, str):
                    raise TutorError(f"state.json topics.{topic_id}.{skill} 成功日期无效")
                parse_date(successful_date)
            if not isinstance(record.get("wrong_reason_counts"), dict):
                raise TutorError(f"state.json topics.{topic_id}.{skill}.wrong_reason_counts 无效")
            if record.get("last_attempt_at") is not None:
                parse_datetime(record["last_attempt_at"])
            if record.get("next_review_at") is not None:
                parse_date(record["next_review_at"])
            if "regression_active" in record and not isinstance(
                record["regression_active"], bool
            ):
                raise TutorError(f"state.json topics.{topic_id}.{skill}.regression_active 无效")
            if record.get("regression_active"):
                if not isinstance(record.get("regressed_at"), str):
                    raise TutorError(f"state.json topics.{topic_id}.{skill} 缺少回退时间")
                parse_datetime(record["regressed_at"])
                if not isinstance(record.get("regressed_item_id"), str):
                    raise TutorError(f"state.json topics.{topic_id}.{skill} 缺少回退题目")
    if state.get("last_session_at") is not None:
        parse_datetime(state["last_session_at"])
    return state


def load_profile_and_state(data_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    paths = state_paths(data_dir)
    profile = load_json(paths["profile"], "私人档案")
    state = validate_state(load_json(paths["state"], "学习状态"))
    if not isinstance(profile, dict) or profile.get("schema_version") != SCHEMA_VERSION:
        raise TutorError("profile.json schema_version 不受支持")
    attempts = load_attempts(paths["attempts"])
    logged_ids = {event["attempt_id"] for event in attempts}
    applied_ids = set(state["applied_attempt_ids"])
    ghost_ids = applied_ids - logged_ids
    if ghost_ids:
        raise TutorError(
            "状态包含证据日志中不存在的作答："
            + ", ".join(sorted(ghost_ids))
            + "；请运行 repair，以事件日志为准重建"
        )
    pending = [event for event in attempts if event["attempt_id"] not in applied_ids]
    if pending:
        curriculum = load_curriculum()
        for event in pending:
            apply_event_to_state(state, event, curriculum)
        save_state_bundle(data_dir, profile, state, backup=True)
    return profile, state


def load_attempts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise TutorError(f"缺少作答证据日志：{path}")
    events: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise TutorError(f"attempts.jsonl 第 {line_number} 行损坏，拒绝写入") from error
        if not isinstance(event, dict) or not isinstance(event.get("attempt_id"), str):
            raise TutorError(f"attempts.jsonl 第 {line_number} 行缺少 attempt_id")
        if not event["attempt_id"]:
            raise TutorError(f"attempts.jsonl 第 {line_number} 行 attempt_id 为空")
        if event["attempt_id"] in seen_ids:
            raise TutorError(f"attempts.jsonl 存在重复 attempt_id：{event['attempt_id']}")
        seen_ids.add(event["attempt_id"])
        events.append(event)
    return events


def write_attempts(path: Path, events: Iterable[dict[str, Any]]) -> None:
    content = "".join(
        json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n" for event in events
    )
    atomic_write_text(path, content)


def subject_status(subject: dict[str, Any], safe_target: float) -> str:
    lower_bound = subject.get("lower_bound_score")
    if lower_bound is None:
        return "unmeasured"
    if lower_bound < 45:
        return "danger"
    if lower_bound < safe_target:
        return "near"
    return "safe"


def status_payload(profile: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    safe_target = float(state.get("strategy", {}).get("safe_target", 52))
    subjects: dict[str, Any] = {}
    for name in SUBJECTS:
        item = dict(state["subjects"][name])
        item["status"] = subject_status(item, safe_target)
        subjects[name] = item
    return {
        "schema_version": SCHEMA_VERSION,
        "profile": profile,
        "strategy": state.get("strategy", {}),
        "subjects": subjects,
        "topics": state.get("topics", {}),
        "last_session_at": state.get("last_session_at"),
    }


def render_dashboard(profile: dict[str, Any], state: dict[str, Any]) -> str:
    payload = status_payload(profile, state)
    lines = [
        "# 私人学习进度",
        "",
        "> 此文件位于 `.study/`，不得提交到公共仓库。",
        "",
        f"- 考试日期：{profile.get('exam_date') or '未设置'}",
        f"- 每日预算：{profile.get('daily_minutes', 0)} 分钟",
        f"- 最后学习：{payload.get('last_session_at') or '尚无有效作答'}",
        "",
        "## 三科过线状态",
        "",
        "| 科目 | 状态 | 最近模考 | 保守下界 | 证据 |",
        "|---|---|---:|---:|---|",
    ]
    labels = {"comprehensive": "综合", "case": "案例", "essay": "论文"}
    for name in SUBJECTS:
        item = payload["subjects"][name]
        lines.append(
            "| {label} | {status} | {latest} | {lower} | {evidence} |".format(
                label=labels[name],
                status=item["status"],
                latest=item.get("latest_mock_score")
                if item.get("latest_mock_score") is not None
                else "—",
                lower=item.get("lower_bound_score")
                if item.get("lower_bound_score") is not None
                else "—",
                evidence=item.get("evidence_level", "cold_start"),
            )
        )

    lines.extend(["", "## 已产生证据的考点", ""])
    if not payload["topics"]:
        lines.append("尚无有效作答，不能判断掌握度。")
    else:
        lines.extend(
            [
                "| 考点 | 综合识别 | 案例应用 | 论文产出 | 整体 | 最近作答 | 下次复习 |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for topic_id, record in sorted(payload["topics"].items()):
            mastery = record.get("mastery", {})

            def dimension_status(skill: str) -> str:
                value = mastery.get(skill)
                return value.get("status", "unseen") if isinstance(value, dict) else "unseen"

            lines.append(
                f"| {topic_id} | {dimension_status('recognition')} | "
                f"{dimension_status('application')} | {dimension_status('production')} | "
                f"{record.get('status', 'learning')} | "
                f"{record.get('last_attempt_at') or '—'} | "
                f"{record.get('next_review_at') or '—'} |"
            )
    return "\n".join(lines) + "\n"


def save_state_bundle(
    data_dir: Path,
    profile: dict[str, Any],
    state: dict[str, Any],
    *,
    backup: bool = True,
) -> None:
    paths = state_paths(data_dir)
    validate_state(state)
    atomic_write_json(paths["state"], state)
    atomic_write_text(paths["dashboard"], render_dashboard(profile, state))
    if backup:
        # A stale backup is safe because attempts.jsonl is the durable source
        # of truth; repair deterministically replays every logged event.
        atomic_write_json(paths["state"].with_name("state.json.bak"), state)


def new_skill_record() -> dict[str, Any]:
    return {
        "status": "unseen",
        "mastery": 0.0,
        "attempt_count": 0,
        "score_sum": 0.0,
        "max_score_sum": 0.0,
        "attempted_items": [],
        "qualified_evidence": [],
        "successful_dates": [],
        "wrong_reason_counts": {},
        "last_attempt_at": None,
        "next_review_at": None,
    }


def skill_status(
    skill: str,
    record: dict[str, Any],
    safe_target: float,
    required_facets: Iterable[str] = (),
) -> str:
    attempts = int(record.get("attempt_count", 0))
    if attempts == 0:
        return "unseen"
    maximum = float(record.get("max_score_sum", 0))
    accuracy = float(record.get("score_sum", 0)) / maximum if maximum else 0.0
    evidence = [
        item for item in record.get("qualified_evidence", []) if isinstance(item, dict)
    ]
    unique_items = {item.get("item_id") for item in evidence if item.get("item_id")}
    required_facet_set = set(required_facets)
    covered_facets = {item.get("facet") for item in evidence if item.get("facet")}
    facets_satisfied = skill == "production" or required_facet_set.issubset(
        covered_facets
    )
    dates = sorted(
        {
            parse_datetime(item.get("at")).date().isoformat()
            for item in evidence
            if item.get("at")
        }
    )

    if record.get("regression_active"):
        regressed_at = parse_datetime(record.get("regressed_at"))
        regressed_item_id = record.get("regressed_item_id")
        recovery = [
            item
            for item in evidence
            if item.get("at") and parse_datetime(item["at"]) > regressed_at
        ]
        recovered = False
        if skill == "recognition":
            recovery = [
                item for item in recovery if item.get("item_id") != regressed_item_id
            ]
            recovery_items = {item.get("item_id") for item in recovery if item.get("item_id")}
            recovery_dates = {
                parse_datetime(item["at"]).date().isoformat() for item in recovery
            }
            recovered = len(recovery_items) >= 2 and len(recovery_dates) >= 2
        elif skill == "application":
            recovery = [
                item for item in recovery if item.get("item_id") != regressed_item_id
            ]
            recovered = any(
                left.get("item_id") != right.get("item_id")
                and abs(parse_datetime(right["at"]) - parse_datetime(left["at"]))
                >= timedelta(hours=48)
                for left_index, left in enumerate(recovery)
                for right in recovery[left_index + 1 :]
            )
        elif skill == "production":
            recovered = any(item.get("mode") == "full_timed" for item in recovery)
        if not recovered:
            return "fragile"

    if skill == "recognition":
        if (
            len(unique_items) >= 6
            and len(dates) >= 2
            and accuracy >= 0.8
            and facets_satisfied
        ):
            return "pass_ready"
    elif skill == "application":
        timed_items = [
            (item.get("item_id"), parse_datetime(item["at"]))
            for item in evidence
            if item.get("item_id") and item.get("at")
        ]
        distinct_pair_is_spaced = any(
            left_id != right_id and abs(right_at - left_at) >= timedelta(hours=48)
            for left_index, (left_id, left_at) in enumerate(timed_items)
            for right_id, right_at in timed_items[left_index + 1 :]
        )
        if (
            len(unique_items) >= 2
            and accuracy >= 0.6
            and distinct_pair_is_spaced
            and facets_satisfied
        ):
            return "pass_ready"
    elif skill == "production":
        safe_ratio = safe_target / 75.0
        if any(
            item.get("mode") == "full_timed"
            and (
                float(item.get("score", 0)) / float(item.get("max_score", 1))
                if float(item.get("max_score", 0)) > 0
                else float(item.get("ratio", 0))
            )
            >= safe_ratio
            for item in evidence
        ):
            return "pass_ready"

    if accuracy >= 0.75 and attempts >= 2:
        return "fragile"
    return "learning"


def refresh_topic_status(
    topic_record: dict[str, Any], required_skills: Iterable[str]
) -> None:
    mastery = topic_record.get("mastery", {})
    statuses = []
    for skill in required_skills:
        record = mastery.get(skill)
        statuses.append(
            record.get("status", "unseen") if isinstance(record, dict) else "unseen"
        )
    if statuses and all(status == "pass_ready" for status in statuses):
        overall = "pass_ready"
    elif any(status == "fragile" for status in statuses):
        overall = "fragile"
    elif any(status != "unseen" for status in statuses):
        overall = "learning"
    else:
        overall = "unseen"
    topic_record["status"] = overall


def cmd_init(args: argparse.Namespace) -> int:
    curriculum = load_curriculum()
    data_dir = args.data_dir
    private, privacy_message = privacy_check(data_dir)
    if not private:
        raise TutorError(f"拒绝在可能被 Git 跟踪的目录建档：{privacy_message}")
    paths = state_paths(data_dir)
    if paths["state"].exists() or paths["profile"].exists():
        load_profile_and_state(data_dir)
        print(f"私人学习档案已存在：{data_dir}")
        return 0

    exam_date = None
    if args.exam_date:
        exam_date = parse_date(args.exam_date).isoformat()
    if args.daily_minutes <= 0 or args.daily_minutes > 1440:
        raise TutorError("daily-minutes 必须在 1–1440 之间")

    created_at = now_iso()
    profile = {
        "schema_version": SCHEMA_VERSION,
        "exam_date": exam_date,
        "daily_minutes": args.daily_minutes,
        "timezone": datetime.now().astimezone().tzname(),
        "background": args.background or "",
        "known_strengths": [],
        "known_weaknesses": [],
        "created_at": created_at,
    }
    state = new_state(curriculum, created_at)

    data_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(paths["profile"], profile)
    atomic_write_text(paths["attempts"], "")
    save_state_bundle(data_dir, profile, state, backup=True)
    print(f"已建立私人学习档案：{data_dir}")
    print("当前三科均为未测量；先做高频考点轻量诊断，不能编造进度。")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    profile, state = load_profile_and_state(args.data_dir)
    payload = status_payload(profile, state)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    print(f"考试日期：{profile.get('exam_date') or '未设置'}")
    print(f"每日预算：{profile.get('daily_minutes')} 分钟")
    labels = {"comprehensive": "综合", "case": "案例", "essay": "论文"}
    for subject in SUBJECTS:
        item = payload["subjects"][subject]
        latest = item.get("latest_mock_score")
        lower = item.get("lower_bound_score")
        print(
            f"{labels[subject]}：{item['status']}；最近模考 "
            f"{latest if latest is not None else '未测'}；保守下界 "
            f"{lower if lower is not None else '未测'}；证据 {item['evidence_level']}"
        )
    if not state["topics"]:
        print("尚无有效作答记录，不能判断具体考点掌握度。")
    else:
        print(f"已有 {len(state['topics'])} 个考点产生学习证据。")
    return 0


def choose_subject_for_skill(topic: dict[str, Any], skill: str) -> str:
    preferred = {
        "recognition": "comprehensive",
        "application": "case",
        "production": "essay",
    }[skill]
    subjects = topic.get("subjects", [])
    return preferred if preferred in subjects else subjects[0]


def validate_record_event(event: dict[str, Any], curriculum: dict[str, Any]) -> None:
    topics = topic_map(curriculum)
    topic_id = event.get("topic_id")
    if topic_id not in topics:
        raise TutorError(f"未知稳定考点 ID：{topic_id}")
    topic = topics[topic_id]
    attempt_id = event.get("attempt_id")
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        raise TutorError("attempt-id 必须是非空字符串")
    skill = event.get("skill")
    if skill not in topic.get("skills", []):
        raise TutorError(f"{topic_id} 不支持能力维度 {skill}")
    facets = topic.get("facets", [])
    facet = event.get("facet")
    if facets and skill != "production" and facet not in facets:
        raise TutorError(
            f"{topic_id}/{skill} 必须用 --facet 标明子主题：" + ", ".join(facets)
        )
    if facet is not None and facet not in facets:
        raise TutorError(f"{topic_id} 不支持 facet {facet}")
    item_id = event.get("item_id")
    if not isinstance(item_id, str) or not item_id.strip():
        raise TutorError("item-id 必填，且必须稳定标识一道独立题目")
    score = event.get("score")
    maximum = event.get("max_score")
    if (
        not isinstance(score, (int, float))
        or not isinstance(maximum, (int, float))
        or isinstance(score, bool)
        or isinstance(maximum, bool)
        or not math.isfinite(float(score))
        or not math.isfinite(float(maximum))
        or maximum <= 0
        or score < 0
        or score > maximum
    ):
        raise TutorError("score 必须在 0 到 max-score 之间，且 max-score > 0")
    subject = event.get("subject")
    if subject not in topic.get("subjects", []):
        raise TutorError(f"考点 {topic_id} 不属于科目 {subject}")
    if event.get("confidence") not in ("guess", "unsure", "sure"):
        raise TutorError("confidence 无效")
    if event.get("mode") not in ("diagnostic", "practice", "review", "mock", "full_timed"):
        raise TutorError("mode 无效")
    if event.get("mode") == "full_timed" and skill != "production":
        raise TutorError("full_timed 仅用于完整论文，整科模考请使用 mock 命令")
    if event.get("source_type") not in (
        "official_outline",
        "real",
        "recalled_real",
        "self_authored",
        "simulation",
    ):
        raise TutorError("source_type 无效")
    duration = event.get("duration_seconds")
    if duration is not None and (
        not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0
    ):
        raise TutorError("duration-seconds 必须是正整数")
    word_count = event.get("word_count")
    if word_count is not None and (
        not isinstance(word_count, int) or isinstance(word_count, bool) or word_count < 0
    ):
        raise TutorError("word-count 必须是非负整数")
    parse_datetime(event.get("at"))
    reasons = event.get("wrong_reasons")
    if not isinstance(reasons, list):
        raise TutorError("wrong_reasons 必须是数组")
    invalid_reasons = set(reasons) - WRONG_REASONS
    if invalid_reasons:
        raise TutorError("未知错因：" + ", ".join(sorted(invalid_reasons)))
    if skill == "production" and event.get("mode") == "full_timed":
        if event.get("complete") is not True:
            raise TutorError("完整限时论文必须显式传入 --complete")
        duration = event.get("duration_seconds")
        if not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
            raise TutorError("完整限时论文必须记录正整数 duration-seconds")
        word_count = event.get("word_count")
        if not isinstance(word_count, int) or isinstance(word_count, bool) or word_count < 2500:
            raise TutorError("完整限时论文必须达到 2500 字并记录 word-count")
        if maximum != 75:
            raise TutorError("完整限时论文必须按官方 75 分制记录")


def apply_record_event(
    state: dict[str, Any], event: dict[str, Any], curriculum: dict[str, Any]
) -> dict[str, Any]:
    validate_record_event(event, curriculum)
    attempt_id = event["attempt_id"]
    if attempt_id in set(state.get("applied_attempt_ids", [])):
        return {"already_applied": True}

    topic = topic_map(curriculum)[event["topic_id"]]
    attempted_at = parse_datetime(event["at"])
    attempted_iso = attempted_at.isoformat(timespec="seconds")
    attempted_date = attempted_at.date().isoformat()
    score = float(event["score"])
    maximum = float(event["max_score"])
    ratio = score / maximum
    skill = event["skill"]
    subject = event["subject"]

    topic_record = state["topics"].setdefault(
        event["topic_id"],
        {
            "topic_id": event["topic_id"],
            "name": topic["name"],
            "status": "unseen",
            "required_skills": topic.get("skills", []),
            "mastery": {},
            "wrong_reason_counts": {},
            "last_attempt_at": None,
            "next_review_at": None,
        },
    )
    record = topic_record["mastery"].setdefault(skill, new_skill_record())
    previous_status = record.get("status")
    record["attempt_count"] = int(record.get("attempt_count", 0)) + 1
    record["score_sum"] = round(float(record.get("score_sum", 0)) + score, 4)
    record["max_score_sum"] = round(float(record.get("max_score_sum", 0)) + maximum, 4)
    attempted_items = set(record.get("attempted_items", []))
    attempted_items.add(event["item_id"])
    record["attempted_items"] = sorted(attempted_items)

    previous_last = record.get("last_attempt_at")
    is_latest = not previous_last or attempted_at >= parse_datetime(previous_last)
    is_mastery_assessment = skill != "production" or event.get("mode") == "full_timed"
    if is_latest:
        record["last_attempt_at"] = attempted_iso

    safe_target = float(state.get("strategy", {}).get("safe_target", 52))
    threshold = {
        "recognition": 0.8,
        "application": 0.6,
        "production": safe_target / 75,
    }[skill]
    qualifies = (
        ratio >= threshold
        and event.get("confidence") != "guess"
        and (
            skill != "production"
            or (
                event.get("mode") == "full_timed"
                and event.get("complete") is True
                and int(event.get("word_count", 0)) >= 2500
                and int(event.get("duration_seconds", 0)) > 0
            )
        )
    )
    if is_latest and is_mastery_assessment:
        record["latest_qualified"] = qualifies
        record["latest_ratio"] = round(ratio, 4)
        record["latest_confidence"] = event.get("confidence")
        if previous_status == "pass_ready":
            record["ever_pass_ready"] = True
        if record.get("ever_pass_ready") and not qualifies:
            record["regression_active"] = True
            record["regressed_at"] = attempted_iso
            record["regressed_item_id"] = event["item_id"]
    if qualifies:
        evidence = record.setdefault("qualified_evidence", [])
        evidence.append(
            {
                "attempt_id": attempt_id,
                "item_id": event["item_id"],
                "facet": event.get("facet"),
                "at": attempted_iso,
                "score": score,
                "max_score": maximum,
                "ratio": ratio,
                "mode": event.get("mode"),
                "complete": event.get("complete", False),
                "duration_seconds": event.get("duration_seconds"),
                "word_count": event.get("word_count"),
            }
        )
        dates = set(record.get("successful_dates", []))
        dates.add(attempted_date)
        record["successful_dates"] = sorted(dates)
    if skill == "production" and event.get("mode") == "full_timed":
        record["full_timed_count"] = int(record.get("full_timed_count", 0)) + 1

    for reason in event.get("wrong_reasons", []):
        counts = record["wrong_reason_counts"]
        counts[reason] = int(counts.get(reason, 0)) + 1
        topic_counts = topic_record["wrong_reason_counts"]
        topic_counts[reason] = int(topic_counts.get(reason, 0)) + 1

    evidence_target = {"recognition": 6, "application": 2, "production": 1}[skill]
    evidence_factor = min(1.0, len(attempted_items) / evidence_target)
    lifetime_accuracy = record["score_sum"] / record["max_score_sum"]
    record["mastery"] = round(lifetime_accuracy * evidence_factor, 4)
    record["status"] = skill_status(
        skill, record, safe_target, topic.get("facets", [])
    )
    if record["status"] == "pass_ready":
        record["ever_pass_ready"] = True
        record["regression_active"] = False

    if record.get("regression_active"):
        interval_days = 1
    elif record["status"] == "pass_ready":
        interval_days = 14
    elif ratio < 0.8 or event.get("confidence") == "guess":
        interval_days = 1
    else:
        interval_days = 3
    next_review = attempted_at.date() + timedelta(days=interval_days)
    if is_latest and (is_mastery_assessment or not record.get("next_review_at")):
        record["next_review_at"] = next_review.isoformat()

    topic_last = topic_record.get("last_attempt_at")
    if not topic_last or attempted_at >= parse_datetime(topic_last):
        topic_record["last_attempt_at"] = attempted_iso
    topic_record["next_review_at"] = min(
        item.get("next_review_at")
        for item in topic_record["mastery"].values()
        if item.get("next_review_at")
    )
    refresh_topic_status(topic_record, topic.get("skills", []))

    subject_last = state["subjects"][subject].get("last_practiced_at")
    if not subject_last or attempted_at >= parse_datetime(subject_last):
        state["subjects"][subject]["last_practiced_at"] = attempted_iso
    state["subjects"][subject]["evidence_count"] = int(
        state["subjects"][subject].get("evidence_count", 0)
    ) + 1
    session_last = state.get("last_session_at")
    if not session_last or attempted_at >= parse_datetime(session_last):
        state["last_session_at"] = attempted_iso
    state["applied_attempt_ids"].append(attempt_id)
    return {
        "already_applied": False,
        "topic_status": topic_record["status"],
        "next_review_at": record.get("next_review_at") or next_review.isoformat(),
    }


def events_conflict(existing: dict[str, Any], candidate: dict[str, Any], *, compare_at: bool) -> bool:
    keys = (
        "event_type",
        "topic_id",
        "item_id",
        "facet",
        "subject",
        "skill",
        "mode",
        "score",
        "max_score",
        "duration_seconds",
        "word_count",
        "complete",
        "confidence",
        "wrong_reasons",
        "source_type",
        "source",
    )
    return any(existing.get(key) != candidate.get(key) for key in keys) or (
        compare_at and existing.get("at") != candidate.get("at")
    )


def cmd_record(args: argparse.Namespace) -> int:
    curriculum = load_curriculum()
    topics = topic_map(curriculum)
    topic = topics.get(args.topic)
    if topic is None:
        raise TutorError(f"未知稳定考点 ID：{args.topic}")
    subject = args.subject or choose_subject_for_skill(topic, args.skill)
    event = {
        "attempt_id": args.attempt_id,
        "event_type": "practice",
        "topic_id": args.topic,
        "item_id": args.item_id,
        "facet": args.facet,
        "at": parse_datetime(args.at).isoformat(timespec="seconds"),
        "subject": subject,
        "skill": args.skill,
        "mode": args.mode,
        "score": args.score,
        "max_score": args.max_score,
        "duration_seconds": args.duration_seconds,
        "word_count": args.word_count,
        "complete": args.complete,
        "confidence": args.confidence,
        "wrong_reasons": args.wrong_reason or [],
        "source_type": args.source_type,
        "source": args.source,
        "feedback_seen": False,
    }
    validate_record_event(event, curriculum)
    profile, state = load_profile_and_state(args.data_dir)
    paths = state_paths(args.data_dir)
    attempts = load_attempts(paths["attempts"])
    existing = next(
        (item for item in attempts if item["attempt_id"] == args.attempt_id), None
    )
    if existing is not None:
        if events_conflict(existing, event, compare_at=bool(args.at)):
            raise TutorError(f"attempt-id {args.attempt_id} 与已记录内容冲突")
        print(f"作答 {args.attempt_id} 已记录，本次幂等跳过。")
        return 0

    # attempts.jsonl is the write-ahead source of truth. If the process stops
    # after this replacement, the next command replays the pending event.
    write_attempts(paths["attempts"], [*attempts, event])
    result = apply_record_event(state, event, curriculum)
    save_state_bundle(args.data_dir, profile, state, backup=True)
    print(
        f"已记录 {args.attempt_id}：{args.topic}/{args.skill} "
        f"{args.score:g}/{args.max_score:g}，状态 {result['topic_status']}，"
        f"下次复习 {result['next_review_at']}。"
    )
    return 0


def recompute_mock_summary(subject: dict[str, Any]) -> None:
    scores = [float(item["score_75"]) for item in subject["mock_scores"][-3:]]
    count = len(subject["mock_scores"])
    latest = scores[-1]
    if count == 1:
        predicted = latest
        lower = max(0.0, latest - 5.0)
        evidence = "low"
    elif count == 2:
        predicted = statistics.mean(scores)
        lower = min(scores)
        evidence = "medium"
    else:
        predicted = statistics.median(scores)
        lower = min(scores)
        evidence = "high"
    subject["latest_mock_score"] = round(latest, 2)
    subject["predicted_score"] = round(predicted, 2)
    subject["lower_bound_score"] = round(lower, 2)
    subject["evidence_level"] = evidence


def validate_mock_event(event: dict[str, Any]) -> None:
    score = event.get("score")
    maximum = event.get("max_score")
    if (
        not isinstance(score, (int, float))
        or not isinstance(maximum, (int, float))
        or isinstance(score, bool)
        or isinstance(maximum, bool)
        or not math.isfinite(float(score))
        or not math.isfinite(float(maximum))
        or maximum <= 0
        or score < 0
        or score > maximum
    ):
        raise TutorError("score 必须在 0 到 max-score 之间，且 max-score > 0")
    if maximum != 75:
        raise TutorError("完整模考必须按官方 75 分制记录，不能把小测归一化成模考")
    if event.get("complete") is not True:
        raise TutorError("只有完整完成的同科试卷才能作为模考证据")
    duration = event.get("duration_seconds")
    if not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0:
        raise TutorError("duration-minutes 必须大于 0")
    if event.get("subject") not in SUBJECTS:
        raise TutorError("模考科目无效")
    if not isinstance(event.get("attempt_id"), str) or not event["attempt_id"].strip():
        raise TutorError("mock-id 必填")
    if not isinstance(event.get("item_id"), str) or not event["item_id"]:
        raise TutorError("paper-id 必填")
    if event.get("source_type") not in (
        "real",
        "recalled_real",
        "self_authored",
        "simulation",
    ):
        raise TutorError("模考 source_type 无效")
    parse_datetime(event.get("at"))


def apply_mock_event(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    validate_mock_event(event)
    attempt_id = event["attempt_id"]
    if attempt_id in set(state.get("applied_attempt_ids", [])):
        return {"already_applied": True}
    measured_at = parse_datetime(event["at"]).isoformat(timespec="seconds")
    subject_name = event["subject"]
    score = float(event["score"])
    maximum = float(event["max_score"])
    score_75 = score / maximum * 75
    subject = state["subjects"][subject_name]
    subject["mock_scores"].append(
        {
            "mock_id": attempt_id,
            "paper_id": event["item_id"],
            "at": measured_at,
            "score": score,
            "max_score": maximum,
            "score_75": round(score_75, 2),
            "duration_minutes": round(int(event["duration_seconds"]) / 60, 2),
            "complete": True,
        }
    )
    subject["mock_scores"].sort(key=lambda item: item["at"])
    previous_last = subject.get("last_practiced_at")
    if not previous_last or parse_datetime(measured_at) >= parse_datetime(previous_last):
        subject["last_practiced_at"] = measured_at
    subject["evidence_count"] = int(subject.get("evidence_count", 0)) + 1
    recompute_mock_summary(subject)
    previous_session = state.get("last_session_at")
    if not previous_session or parse_datetime(measured_at) >= parse_datetime(previous_session):
        state["last_session_at"] = measured_at
    state["applied_attempt_ids"].append(attempt_id)
    return {
        "already_applied": False,
        "lower_bound_score": subject["lower_bound_score"],
        "evidence_level": subject["evidence_level"],
    }


def apply_event_to_state(
    state: dict[str, Any], event: dict[str, Any], curriculum: dict[str, Any]
) -> dict[str, Any]:
    if event.get("event_type") == "mock" or event.get("mode") == "full_mock":
        return apply_mock_event(state, event)
    return apply_record_event(state, event, curriculum)


def cmd_mock(args: argparse.Namespace) -> int:
    if not math.isfinite(args.duration_minutes) or args.duration_minutes <= 0:
        raise TutorError("duration-minutes 必须是大于 0 的有限数")
    measured_at = parse_datetime(args.at).isoformat(timespec="seconds")
    event = {
        "attempt_id": args.mock_id,
        "event_type": "mock",
        "topic_id": None,
        "item_id": args.paper_id,
        "at": measured_at,
        "subject": args.subject,
        "skill": {
            "comprehensive": "recognition",
            "case": "application",
            "essay": "production",
        }[args.subject],
        "mode": "full_mock",
        "score": args.score,
        "max_score": args.max_score,
        "duration_seconds": round(args.duration_minutes * 60),
        "word_count": None,
        "confidence": "sure",
        "wrong_reasons": [],
        "source_type": args.source_type,
        "source": args.paper_id,
        "complete": args.complete,
        "feedback_seen": False,
    }
    validate_mock_event(event)
    profile, state = load_profile_and_state(args.data_dir)
    paths = state_paths(args.data_dir)
    attempts = load_attempts(paths["attempts"])
    logged_event = next(
        (item for item in attempts if item.get("attempt_id") == args.mock_id), None
    )
    if logged_event is not None:
        if events_conflict(logged_event, event, compare_at=bool(args.at)):
            raise TutorError(f"mock-id {args.mock_id} 与已记录内容冲突")
        print(f"模考 {args.mock_id} 已记录，本次幂等跳过。")
        return 0

    write_attempts(paths["attempts"], [*attempts, event])
    result = apply_mock_event(state, event)
    save_state_bundle(args.data_dir, profile, state, backup=True)
    print(
        f"已记录模考 {args.mock_id}：{args.subject} {args.score:g}/{args.max_score:g}；"
        f"保守下界 {result['lower_bound_score']:g}/75，证据 {result['evidence_level']}。"
    )
    return 0


def subject_allocations(state: dict[str, Any], today: date) -> dict[str, float]:
    safe_target = float(state.get("strategy", {}).get("safe_target", 52))
    any_practice = any(
        state["subjects"][subject].get("last_practiced_at") for subject in SUBJECTS
    )
    raw: dict[str, float] = {}
    for subject in SUBJECTS:
        subject_state = state["subjects"][subject]
        lower = subject_state.get("lower_bound_score")
        if lower is None:
            evidence_count = int(subject_state.get("evidence_count", 0))
            raw[subject] = 1.2 + 0.4 / (1 + evidence_count)
        else:
            raw[subject] = max(0.2, min(2.0, (safe_target - float(lower)) / 10 + 0.2))
        last_practiced = subject_state.get("last_practiced_at")
        if any_practice and not last_practiced:
            raw[subject] += 0.3
        elif last_practiced:
            age_days = max(0, (today - parse_datetime(last_practiced).date()).days)
            if age_days >= 3:
                raw[subject] += 0.2
    total = sum(raw.values())
    return {subject: round(raw[subject] / total, 4) for subject in SUBJECTS}


def topic_mastery(state: dict[str, Any], topic_id: str, skill: str) -> float:
    record = state.get("topics", {}).get(topic_id)
    if not record:
        return 0.0
    skill_record = record.get("mastery", {}).get(skill)
    if not isinstance(skill_record, dict):
        return 0.0
    if skill_record.get("status") == "pass_ready":
        # Once the evidence gate is met, this track moves to maintenance even
        # when its rubric threshold is intentionally only 60% (case) or 52/75
        # (essay). Raw accuracy remains visible in state; this value is solely
        # the scheduling need signal.
        return 1.0
    return float(skill_record.get("mastery", 0))


def select_target_subject(
    state: dict[str, Any], allocations: dict[str, float]
) -> str:
    critical = [
        subject
        for subject in SUBJECTS
        if state["subjects"][subject].get("lower_bound_score") is None
        or float(state["subjects"][subject]["lower_bound_score"]) < 45
    ]
    candidates = critical or list(SUBJECTS)
    return max(
        candidates,
        key=lambda subject: (allocations[subject], -SUBJECTS.index(subject)),
    )


def select_maintenance_subject(
    state: dict[str, Any], target_subject: str, today: date
) -> str | None:
    overdue: list[tuple[int, str]] = []
    for subject in SUBJECTS:
        if subject == target_subject:
            continue
        last_practiced = state["subjects"][subject].get("last_practiced_at")
        if not last_practiced:
            continue
        age_days = max(0, (today - parse_datetime(last_practiced).date()).days)
        if age_days >= 3:
            overdue.append((age_days, subject))
    if not overdue:
        return None
    return max(overdue, key=lambda item: (item[0], -SUBJECTS.index(item[1])))[1]


def cmd_configure(args: argparse.Namespace) -> int:
    if (
        args.case_track is None
        and args.essay_theme is None
        and args.skip_topic is None
        and args.unskip_topic is None
    ):
        raise TutorError(
            "至少提供路线选项或 --skip-topic TOPIC=原因 / --unskip-topic TOPIC"
        )
    curriculum = load_curriculum()
    topics = topic_map(curriculum)
    profile, state = load_profile_and_state(args.data_dir)
    if args.case_track is not None:
        tracks = list(dict.fromkeys(args.case_track))
        if not 1 <= len(tracks) <= 3:
            raise TutorError("案例主赛道请选择 1–3 个")
        invalid = [
            topic_id
            for topic_id in tracks
            if topic_id not in topics
            or "case" not in topics[topic_id].get("subjects", [])
            or not topic_id.startswith("C")
        ]
        if invalid:
            raise TutorError("无效案例赛道：" + ", ".join(invalid))
        state["strategy"]["case_tracks"] = tracks
        state["strategy"]["case_tracks_configured"] = True
    if args.essay_theme is not None:
        themes = list(dict.fromkeys(args.essay_theme))
        if not 1 <= len(themes) <= 3:
            raise TutorError("论文主题请选择 1–3 个")
        invalid = [
            topic_id
            for topic_id in themes
            if topic_id not in topics
            or "essay" not in topics[topic_id].get("subjects", [])
            or not topic_id.startswith("P")
        ]
        if invalid:
            raise TutorError("无效论文主题：" + ", ".join(invalid))
        state["strategy"]["essay_themes"] = themes
        state["strategy"]["essay_themes_configured"] = True
    skips = state["strategy"].setdefault("strategic_skips", {})
    if not isinstance(skips, dict):
        raise TutorError("state.json strategic_skips 无效")
    for specification in args.skip_topic or []:
        topic_id, separator, reason = specification.partition("=")
        topic_id = topic_id.strip()
        reason = reason.strip()
        if not separator or topic_id not in topics or not reason:
            raise TutorError("skip-topic 必须使用 TOPIC_ID=原因，且考点必须存在")
        skips[topic_id] = reason
    for topic_id in args.unskip_topic or []:
        if topic_id not in topics:
            raise TutorError(f"未知稳定考点 ID：{topic_id}")
        skips.pop(topic_id, None)
    save_state_bundle(args.data_dir, profile, state, backup=True)
    print(
        "已更新个人路线：案例 "
        + ", ".join(state["strategy"].get("case_tracks", []))
        + "；论文 "
        + (", ".join(state["strategy"].get("essay_themes", [])) or "待诊断")
        + f"；战略放弃 {len(skips)} 个"
    )
    return 0


def cmd_recommend(args: argparse.Namespace) -> int:
    curriculum = load_curriculum()
    profile, state = load_profile_and_state(args.data_dir)
    today = parse_date(args.today) if args.today else datetime.now().astimezone().date()
    exam_date = parse_date(profile["exam_date"]) if profile.get("exam_date") else None
    days_to_exam = (exam_date - today).days if exam_date else None
    crunch_mode = days_to_exam is not None and 0 <= days_to_exam <= 3
    allocations = subject_allocations(state, today)
    target_subject = args.subject or select_target_subject(state, allocations)
    maintenance_subject = (
        None
        if args.subject
        else select_maintenance_subject(state, target_subject, today)
    )
    strategy = state.get("strategy", {})
    configured_case_tracks = set(strategy.get("case_tracks", []))
    configured_essay_themes = set(strategy.get("essay_themes", []))
    strategic_skips = set(strategy.get("strategic_skips", {}))
    cold_start_groups = curriculum.get("strategy", {}).get(
        "comprehensive_cold_start_groups", []
    )
    cold_start_group_by_topic = {
        topic_id: group_index
        for group_index, topic_ids in enumerate(cold_start_groups, 1)
        for topic_id in topic_ids
    }

    ranked: list[dict[str, Any]] = []
    for topic in curriculum["topics"]:
        if topic["id"] in strategic_skips:
            continue
        progress = state.get("topics", {}).get(topic["id"], {})
        survival_resource = any(
            "SURVIVAL.md" in resource or resource.startswith("cheatsheets/")
            for resource in topic.get("resources", [])
        )
        if crunch_mode and not progress and not survival_resource:
            continue
        subjects = topic.get("subjects", [])
        if args.subject and args.subject not in subjects:
            continue
        if (
            topic["id"].startswith("C")
            and strategy.get("case_tracks_configured")
            and topic["id"] not in configured_case_tracks
        ):
            continue
        if (
            topic["id"].startswith("P")
            and strategy.get("essay_themes_configured")
            and topic["id"] not in configured_essay_themes
        ):
            continue
        chosen_subject = target_subject if target_subject in subjects else max(
            subjects, key=lambda subject: allocations.get(subject, 0)
        )
        skill = {
            "comprehensive": "recognition",
            "case": "application",
            "essay": "production",
        }[chosen_subject]
        if skill not in topic.get("skills", []):
            skill = topic.get("skills", [skill])[0]
        mastery = topic_mastery(state, topic["id"], skill)
        need = max(0.08, 1.0 - mastery)
        skill_progress = progress.get("mastery", {}).get(skill, {})
        review_at = (
            skill_progress.get("next_review_at")
            if isinstance(skill_progress, dict)
            else None
        )
        due = False
        if review_at:
            try:
                due = parse_date(review_at) <= today
            except TutorError:
                due = True
        due_factor = 1.7 if due else 1.0
        frequency = max(0.0, float(topic.get("frequency_count", 0)))
        confidence_factor = {
            "high": 1.0,
            "medium": 0.9,
            "low": 0.7,
            "expert_estimate": 0.65,
        }.get(str(topic.get("frequency_confidence", "low")), 0.7)
        value = (
            (1.0 + math.log1p(frequency))
            * confidence_factor
            * float(topic.get("priority_weight", 0.5))
            * (1.0 + 0.2 * float(topic.get("quick_win", 0)))
            * (1.0 + 0.2 * float(topic.get("cross_subject_value", 0)))
        )
        cost = max(0.5, float(topic.get("estimated_minutes", 60)) / 60)
        score = allocations[chosen_subject] * need * due_factor * value / cost
        # Pass-first is a hard subject gate, not merely a soft score. This
        # prevents a 75-point strong subject from outranking a 44-point weak one.
        gate = 1 if chosen_subject == target_subject else 0
        expected_prefix = {"comprehensive": "K", "case": "C", "essay": "P"}[
            chosen_subject
        ]
        track_gate = 1 if topic["id"].startswith(expected_prefix) else 0
        cold_start_group = 999
        if (
            chosen_subject == "comprehensive"
            and state["subjects"]["comprehensive"].get("lower_bound_score") is None
            and int(state["subjects"]["comprehensive"].get("evidence_count", 0)) < 6
        ):
            cold_start_group = cold_start_group_by_topic.get(topic["id"], 999)
        reasons = []
        if state["subjects"][chosen_subject].get("lower_bound_score") is None:
            reasons.append("该科尚未测量，先诊断")
        elif state["subjects"][chosen_subject]["lower_bound_score"] < 45:
            reasons.append("该科保守下界未过线")
        if due:
            reasons.append("已到复习日")
        if crunch_mode:
            reasons.append("考前 3 天，只做错题、保命卡或答题骨架")
        if frequency >= 6:
            reasons.append(f"历年高频证据 {int(frequency)} 次")
        if float(topic.get("cross_subject_value", 0)) >= 0.8:
            reasons.append("三科复用价值高")
        if not reasons:
            reasons.append("当前投入产出比最高")
        ranked.append(
            {
                "topic_id": topic["id"],
                "name": topic["name"],
                "subject": chosen_subject,
                "skill": skill,
                "priority_score": round(score, 4),
                "mastery": round(mastery, 4),
                "review_due": due,
                "estimated_minutes": topic.get("estimated_minutes"),
                "reason": "；".join(reasons),
                "resources": topic.get("resources", []),
                "_gate": gate,
                "_track_gate": track_gate,
                "_strategy_rank": int(topic.get("strategy_rank", 999)),
                "_frequency": frequency,
                "_cold_start_group": cold_start_group,
            }
        )

    ranked.sort(
        key=lambda item: (
            -item["_gate"],
            -int(item["review_due"]),
            -item["_track_gate"],
            item["_cold_start_group"],
            -item["priority_score"],
            item["_strategy_rank"],
            -item["_frequency"],
            item["topic_id"],
        )
    )
    selected = ranked[: args.limit]
    if maintenance_subject and args.limit >= 2 and not any(
        item["subject"] == maintenance_subject for item in selected
    ):
        maintenance_item = next(
            (item for item in ranked if item["subject"] == maintenance_subject),
            None,
        )
        if maintenance_item is not None:
            maintenance_item = dict(maintenance_item)
            maintenance_item["reason"] = "三天最低维护；" + maintenance_item["reason"]
            selected[-1] = maintenance_item

    recommendations = []
    for item in selected:
        clean = {key: value for key, value in item.items() if not key.startswith("_")}
        recommendations.append(clean)

    payload = {
        "today": today.isoformat(),
        "safe_target": state.get("strategy", {}).get("safe_target", 52),
        "target_subject": target_subject,
        "maintenance_subject": maintenance_subject,
        "crunch_mode": crunch_mode,
        "days_to_exam": days_to_exam,
        "subject_allocation": allocations,
        "recommendations": recommendations,
        "profile": {
            "exam_date": profile.get("exam_date"),
            "daily_minutes": profile.get("daily_minutes"),
        },
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    print(f"当前优先科目：{target_subject}")
    print(
        "时间分配："
        + "，".join(f"{subject} {allocation:.0%}" for subject, allocation in allocations.items())
    )
    for index, item in enumerate(recommendations, 1):
        print(
            f"{index}. [{item['subject']}] {item['topic_id']} {item['name']} "
            f"— {item['reason']}"
        )
    return 0


def privacy_check(data_dir: Path) -> tuple[bool, str]:
    try:
        relative_data_dir = data_dir.resolve().relative_to(REPO_ROOT)
    except ValueError:
        return True, "私人目录位于仓库外，不会被此仓库提交"

    if not (REPO_ROOT / ".git").exists():
        safe_name = relative_data_dir.parts and (
            relative_data_dir.parts[0] == ".study"
            or relative_data_dir.parts[0].startswith(".study-")
        )
        return (
            bool(safe_name),
            f"{relative_data_dir} 匹配私人目录规则"
            if safe_name
            else f"{relative_data_dir} 不匹配私人目录规则",
        )

    candidate = (relative_data_dir / "state.json").as_posix()
    ignored = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", candidate],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    ).returncode == 0
    return (
        ignored,
        f"{relative_data_dir} 已被 Git 忽略"
        if ignored
        else f"{relative_data_dir} 未被 Git 忽略",
    )


def doctor_checks(data_dir: Path) -> tuple[bool, list[dict[str, Any]]]:
    checks: list[dict[str, Any]] = []
    healthy = True

    try:
        curriculum = load_curriculum()
        missing = []
        for topic in curriculum["topics"]:
            for resource in topic.get("resources", []):
                if not (REPO_ROOT / resource.split("#", 1)[0]).exists():
                    missing.append(resource)
        ok = not missing
        checks.append(
            {
                "name": "curriculum",
                "healthy": ok,
                "message": "课程表与资源有效" if ok else "缺少资源：" + ", ".join(missing),
            }
        )
        healthy = healthy and ok
    except TutorError as error:
        checks.append({"name": "curriculum", "healthy": False, "message": str(error)})
        healthy = False

    paths = state_paths(data_dir)
    state_path = paths["state"]
    if not state_path.exists():
        partial = [
            path.name
            for key, path in paths.items()
            if key != "state" and path.exists()
        ]
        backup_path = state_path.with_name("state.json.bak")
        if backup_path.exists():
            partial.append(backup_path.name)
        ok = not partial
        checks.append(
            {
                "name": "state",
                "healthy": ok,
                "message": "尚未建档；没有学习进度可读取"
                if ok
                else "建档不完整，可运行 repair：" + ", ".join(sorted(partial)),
            }
        )
        healthy = healthy and ok
    else:
        try:
            _, state = load_profile_and_state(data_dir)
            attempts = load_attempts(paths["attempts"])
            backup_path = state_path.with_name("state.json.bak")
            validate_state(load_json(backup_path, "状态备份"))
            logged_ids = {event["attempt_id"] for event in attempts}
            applied_ids = set(state["applied_attempt_ids"])
            if logged_ids != applied_ids:
                raise TutorError("状态与事件日志集合不一致，请运行 repair")
            checks.append(
                {
                    "name": "state",
                    "healthy": True,
                    "message": "私人状态、事件日志与备份一致",
                }
            )
        except TutorError as error:
            checks.append(
                {"name": "state", "healthy": False, "message": f"invalid/corrupt: {error}"}
            )
            healthy = False

    ignored, privacy_message = privacy_check(data_dir)
    checks.append(
        {
            "name": "privacy",
            "healthy": ignored,
            "message": privacy_message,
        }
    )
    healthy = healthy and ignored
    return healthy, checks


def cmd_doctor(args: argparse.Namespace) -> int:
    healthy, checks = doctor_checks(args.data_dir)
    payload = {"healthy": healthy, "checks": checks}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        for check in checks:
            marker = "PASS" if check["healthy"] else "FAIL"
            print(f"[{marker}] {check['name']}: {check['message']}")
    return 0 if healthy else 1


def cmd_repair(args: argparse.Namespace) -> int:
    paths = state_paths(args.data_dir)
    state_path = paths["state"]
    backup_path = state_path.with_name(state_path.name + ".bak")
    profile = load_json(paths["profile"], "私人档案")
    if not isinstance(profile, dict) or profile.get("schema_version") != SCHEMA_VERSION:
        raise TutorError("profile.json schema_version 不受支持")
    attempts = load_attempts(paths["attempts"])
    logged_ids = {event["attempt_id"] for event in attempts}
    current: dict[str, Any] | None = None
    try:
        current = validate_state(load_json(state_path, "学习状态"))
    except TutorError:
        pass
    else:
        if set(current["applied_attempt_ids"]) == logged_ids:
            try:
                validate_state(load_json(backup_path, "状态备份"))
            except TutorError:
                pass
            else:
                print("状态、事件日志与备份有效，无需修复。")
                return 0

    curriculum = load_curriculum()
    source_state = current
    if source_state is None:
        try:
            source_state = validate_state(load_json(backup_path, "状态备份"))
        except TutorError:
            source_state = None
    rebuilt = new_state(curriculum, str(profile.get("created_at") or now_iso()))
    if source_state is not None and isinstance(source_state.get("strategy"), dict):
        for key in (
            "pass_line",
            "safe_target",
            "case_tracks",
            "essay_themes",
            "case_tracks_configured",
            "essay_themes_configured",
            "strategic_skips",
        ):
            if key in source_state["strategy"]:
                rebuilt["strategy"][key] = source_state["strategy"][key]
    try:
        for event in attempts:
            apply_event_to_state(rebuilt, event, curriculum)
        validate_state(rebuilt)
    except TutorError as error:
        raise TutorError(f"事件日志无法确定性重建，已保留原文件：{error}") from error

    corrupt_path: Path | None = None
    if state_path.exists():
        stamp = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S.%f%z")
        corrupt_path = state_path.with_name(f"{state_path.name}.corrupt.{stamp}")
        atomic_write_bytes(corrupt_path, state_path.read_bytes())
    save_state_bundle(args.data_dir, profile, rebuilt, backup=True)
    if corrupt_path is None:
        print("state.json 缺失，已依据事件日志重建。")
    else:
        print(f"已依据事件日志重建；原状态保留为 {corrupt_path.name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="系统架构设计师过线私教的本地进度引擎"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=REPO_ROOT / ".study",
        help="私人状态目录（默认：仓库根目录 .study）",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="建立或恢复私人学习档案")
    init_parser.add_argument("--exam-date")
    init_parser.add_argument("--daily-minutes", type=int, default=45)
    init_parser.add_argument("--background", default="")
    init_parser.set_defaults(func=cmd_init)

    status_parser = subparsers.add_parser("status", help="查看三科独立进度")
    status_parser.add_argument("--json", action="store_true")
    status_parser.set_defaults(func=cmd_status)

    recommend_parser = subparsers.add_parser("recommend", help="推荐下一项高收益任务")
    recommend_parser.add_argument("--json", action="store_true")
    recommend_parser.add_argument("--subject", choices=SUBJECTS)
    recommend_parser.add_argument("--limit", type=int, default=5)
    recommend_parser.add_argument("--today")
    recommend_parser.set_defaults(func=cmd_recommend)

    configure_parser = subparsers.add_parser(
        "configure", help="保存诊断后的案例赛道与论文主题"
    )
    configure_parser.add_argument("--case-track", action="append")
    configure_parser.add_argument("--essay-theme", action="append")
    configure_parser.add_argument("--skip-topic", action="append")
    configure_parser.add_argument("--unskip-topic", action="append")
    configure_parser.set_defaults(func=cmd_configure)

    record_parser = subparsers.add_parser("record", help="记录一次有效作答")
    record_parser.add_argument("--topic", required=True)
    record_parser.add_argument("--skill", choices=SKILLS, required=True)
    record_parser.add_argument("--score", type=float, required=True)
    record_parser.add_argument("--max-score", type=float, required=True)
    record_parser.add_argument("--attempt-id", required=True)
    record_parser.add_argument("--item-id", required=True)
    record_parser.add_argument("--facet")
    record_parser.add_argument("--at")
    record_parser.add_argument("--subject", choices=SUBJECTS)
    record_parser.add_argument("--wrong-reason", action="append")
    record_parser.add_argument("--source")
    record_parser.add_argument(
        "--source-type",
        choices=("official_outline", "real", "recalled_real", "self_authored", "simulation"),
        default="self_authored",
    )
    record_parser.add_argument("--duration-seconds", type=int)
    record_parser.add_argument("--word-count", type=int)
    record_parser.add_argument("--complete", action="store_true")
    record_parser.add_argument("--confidence", choices=("guess", "unsure", "sure"), default="sure")
    record_parser.add_argument(
        "--mode",
        choices=("diagnostic", "practice", "review", "mock", "full_timed"),
        default="practice",
    )
    record_parser.set_defaults(func=cmd_record)

    mock_parser = subparsers.add_parser("mock", help="记录一科完整限时成绩")
    mock_parser.add_argument("--subject", choices=SUBJECTS, required=True)
    mock_parser.add_argument("--mock-id", required=True)
    mock_parser.add_argument("--paper-id", required=True)
    mock_parser.add_argument("--score", type=float, required=True)
    mock_parser.add_argument("--max-score", type=float, default=75)
    mock_parser.add_argument("--duration-minutes", type=float, required=True)
    mock_parser.add_argument("--complete", action="store_true")
    mock_parser.add_argument(
        "--source-type",
        choices=("real", "recalled_real", "self_authored", "simulation"),
        default="simulation",
    )
    mock_parser.add_argument("--at")
    mock_parser.set_defaults(func=cmd_mock)

    doctor_parser = subparsers.add_parser("doctor", help="检查课程、状态和隐私设置")
    doctor_parser.add_argument("--json", action="store_true")
    doctor_parser.set_defaults(func=cmd_doctor)

    repair_parser = subparsers.add_parser("repair", help="从最近有效备份恢复损坏状态")
    repair_parser.set_defaults(func=cmd_repair)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.data_dir = args.data_dir.expanduser().resolve()
    if getattr(args, "limit", 1) <= 0:
        print("错误：limit 必须大于 0", file=sys.stderr)
        return 2
    try:
        private, privacy_message = privacy_check(args.data_dir)
        if not private:
            raise TutorError(
                f"拒绝读取或写入可能被 Git 跟踪的私人目录：{privacy_message}"
            )
        if args.command == "init":
            args.data_dir.mkdir(parents=True, exist_ok=True)
        if args.data_dir.exists():
            with data_lock(args.data_dir):
                return int(args.func(args))
        return int(args.func(args))
    except TutorError as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
