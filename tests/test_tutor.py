"""Black-box acceptance tests for the private exam tutor.

Run with::

    python3 -m unittest discover -s tests -v

The tests intentionally exercise ``scripts/tutor.py`` through its command line.
That keeps the learner-state format free to evolve while protecting the product
rules that matter: safe private progress, evidence-based mastery, and pass-first
recommendations.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote


REPO_ROOT = Path(__file__).resolve().parents[1]
TUTOR_SCRIPT = REPO_ROOT / "scripts" / "tutor.py"
CURRICULUM_PATH = REPO_ROOT / "tutor" / "curriculum.json"
SUBJECTS = {"comprehensive", "case", "essay"}
PASS_READY_STATES = {"mastered", "pass_ready", "pass-ready", "ready"}


def _run_cli(
    data_dir: Path,
    *arguments: str,
    expected_returncode: int | None = 0,
) -> subprocess.CompletedProcess[str]:
    """Run the public CLI and include useful diagnostics on failure."""

    resolved_arguments = list(arguments)
    # Most tests care about higher-level progress behavior. Give every record a
    # deterministic independent item ID unless the scenario explicitly tests
    # repeated-item behavior with its own --item-id.
    if resolved_arguments[:1] == ["record"] and "--item-id" not in resolved_arguments:
        attempt_index = resolved_arguments.index("--attempt-id") + 1
        resolved_arguments.extend(
            ["--item-id", f"test-item:{resolved_arguments[attempt_index]}"]
        )
    command = [
        sys.executable,
        str(TUTOR_SCRIPT),
        "--data-dir",
        str(data_dir),
        *resolved_arguments,
    ]
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if expected_returncode is not None and completed.returncode != expected_returncode:
        raise AssertionError(
            f"command returned {completed.returncode}, expected "
            f"{expected_returncode}: {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return completed


def _json_output(completed: subprocess.CompletedProcess[str]) -> Any:
    """Decode a JSON CLI response, accepting harmless surrounding whitespace."""

    output = completed.stdout.strip()
    if not output:
        raise AssertionError(f"expected JSON output; stderr was:\n{completed.stderr}")
    try:
        return json.loads(output)
    except json.JSONDecodeError as error:
        raise AssertionError(f"CLI output is not JSON:\n{output}") from error


def _walk(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _values_for_key(value: Any, wanted_key: str) -> list[Any]:
    values: list[Any] = []
    for node in _walk(value):
        if isinstance(node, dict) and wanted_key in node:
            values.append(node[wanted_key])
    return values


def _find_topic_record(status: Any, topic_id: str) -> dict[str, Any]:
    """Find a topic whether the status uses a mapping or a list schema."""

    for node in _walk(status):
        if not isinstance(node, dict):
            continue
        if topic_id in node and isinstance(node[topic_id], dict):
            return node[topic_id]
        if node.get("topic_id") == topic_id or node.get("id") == topic_id:
            return node
    raise AssertionError(f"status does not expose progress for topic {topic_id}")


def _status_label(topic_record: dict[str, Any], skill: str = "recognition") -> str:
    """Read the visible learning-state label without fixing the whole schema."""

    for key in ("status", "state", "stage", "mastery_status"):
        value = topic_record.get(key)
        if isinstance(value, str):
            return value.lower()

    skill_record = topic_record.get(skill)
    if isinstance(skill_record, dict):
        for key in ("status", "state", "stage", "mastery_status"):
            value = skill_record.get(key)
            if isinstance(value, str):
                return value.lower()

    mastery = topic_record.get("mastery")
    if isinstance(mastery, dict):
        skill_record = mastery.get(skill)
        if isinstance(skill_record, dict):
            for key in ("status", "state", "stage", "mastery_status"):
                value = skill_record.get(key)
                if isinstance(value, str):
                    return value.lower()

    raise AssertionError("topic progress must expose a status/state/stage label")


def _snapshot_files(directory: Path) -> dict[str, bytes]:
    """Return an exact persisted-data snapshot after a CLI command finishes."""

    return {
        str(path.relative_to(directory)): path.read_bytes()
        for path in sorted(directory.rglob("*"))
        if path.is_file() and not path.name.endswith(".lock")
    }


def _recommendation_items(payload: Any) -> list[dict[str, Any]]:
    """Extract the ordered task list from the recommendation response."""

    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    if isinstance(payload, dict):
        for key in ("recommendations", "items", "tasks", "plan"):
            value = payload.get(key)
            if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                return value
    raise AssertionError("recommend --json must expose an ordered recommendation list")


def _recommendation_topic_id(item: dict[str, Any]) -> str:
    for key in ("topic_id", "id", "topic"):
        value = item.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            nested = value.get("id") or value.get("topic_id")
            if isinstance(nested, str):
                return nested
    raise AssertionError(f"recommendation has no topic id: {item!r}")


def _find_subject_allocation(payload: Any) -> dict[str, float]:
    for node in _walk(payload):
        if not isinstance(node, dict) or not SUBJECTS.issubset(node):
            continue
        if all(isinstance(node[subject], (int, float)) for subject in SUBJECTS):
            return {subject: float(node[subject]) for subject in SUBJECTS}
    raise AssertionError(
        "recommend --json must expose numeric comprehensive/case/essay allocation"
    )


def _primary_state_file(data_dir: Path) -> Path:
    """Locate the mutable state document while ignoring backups."""

    preferred_names = ("state.json", "progress.json", "profile.json")
    json_files = [
        path
        for path in data_dir.rglob("*.json")
        if "backup" not in {part.lower() for part in path.parts}
        and not path.name.endswith((".bak.json", ".backup.json"))
    ]
    for name in preferred_names:
        for path in json_files:
            if path.name == name:
                return path
    if len(json_files) == 1:
        return json_files[0]
    raise AssertionError(
        "could not identify the primary learner state JSON; found "
        + ", ".join(str(path.relative_to(data_dir)) for path in json_files)
    )


class TutorAcceptanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not TUTOR_SCRIPT.is_file():
            raise AssertionError(f"missing {TUTOR_SCRIPT}")
        if not CURRICULUM_PATH.is_file():
            raise AssertionError(f"missing {CURRICULUM_PATH}")
        cls.curriculum = json.loads(CURRICULUM_PATH.read_text(encoding="utf-8"))
        cls.topics = cls.curriculum.get("topics", [])
        if not isinstance(cls.topics, list):
            raise AssertionError("curriculum topics must be a list")
        if not cls.topics:
            raise AssertionError("curriculum topics must not be empty")

    def _init(self, data_dir: Path) -> None:
        _run_cli(
            data_dir,
            "init",
            "--exam-date",
            "2026-11-07",
            "--daily-minutes",
            "45",
            "--background",
            "backend",
        )

    def _status(self, data_dir: Path) -> Any:
        return _json_output(_run_cli(data_dir, "status", "--json"))

    def _recognition_topic(self) -> dict[str, Any]:
        candidates = [
            topic
            for topic in self.topics
            if "recognition" in topic.get("skills", [])
            and "comprehensive" in topic.get("subjects", [])
        ]
        self.assertTrue(candidates, "curriculum needs a comprehensive recognition topic")
        return max(
            candidates,
            key=lambda topic: (
                float(topic.get("frequency_count", 0)),
                float(topic.get("priority_weight", 0)),
                str(topic["id"]),
            ),
        )

    def test_curriculum_has_unique_stable_ids_and_existing_resources(self) -> None:
        self.assertIsInstance(self.curriculum.get("schema_version"), int)
        self.assertIn("strategy", self.curriculum)

        ids: list[str] = []
        required = {
            "id",
            "name",
            "subjects",
            "skills",
            "frequency_count",
            "priority_weight",
            "quick_win",
            "cross_subject_value",
            "estimated_minutes",
            "resources",
        }
        for topic in self.topics:
            with self.subTest(topic=topic.get("id", topic.get("name"))):
                self.assertTrue(required.issubset(topic), required - set(topic))
                topic_id = topic["id"]
                self.assertIsInstance(topic_id, str)
                self.assertRegex(topic_id, r"^[KCP]\d{2}(?:[._-][A-Z0-9]+)*$")
                ids.append(topic_id)

                self.assertTrue(topic["subjects"])
                self.assertTrue(set(topic["subjects"]).issubset(SUBJECTS))
                self.assertTrue(topic["skills"])
                self.assertTrue(topic["resources"])
                for resource in topic["resources"]:
                    self.assertIsInstance(resource, str)
                    local_path = resource.split("#", 1)[0]
                    self.assertTrue(local_path, "resource must name a local file")
                    resolved = (REPO_ROOT / local_path).resolve()
                    self.assertTrue(
                        resolved.is_relative_to(REPO_ROOT),
                        f"resource escapes repository: {resource}",
                    )
                    self.assertTrue(resolved.exists(), f"missing resource: {resource}")

        self.assertEqual(len(ids), len(set(ids)), "curriculum topic IDs must be unique")

    def test_init_persists_profile_and_status_is_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary) / "private-study"
            self._init(data_dir)
            self.assertTrue(data_dir.is_dir())
            self.assertTrue(any(data_dir.iterdir()), "init did not persist learner state")
            self.assertTrue((data_dir / "state.json.bak").is_file())

            status = self._status(data_dir)
            self.assertIn("2026-11-07", _values_for_key(status, "exam_date"))
            self.assertIn(45, _values_for_key(status, "daily_minutes"))
            self.assertIn("backend", _values_for_key(status, "background"))

    def test_every_command_refuses_a_copied_unignored_private_directory(self) -> None:
        with tempfile.TemporaryDirectory() as source_temporary:
            source = Path(source_temporary)
            self._init(source)
            with tempfile.TemporaryDirectory(dir=REPO_ROOT) as unsafe_temporary:
                unsafe = Path(unsafe_temporary)
                for source_file in source.iterdir():
                    if source_file.is_file() and source_file.name != ".tutor.lock":
                        (unsafe / source_file.name).write_bytes(source_file.read_bytes())
                before = _snapshot_files(unsafe)
                for arguments in (
                    ("status", "--json"),
                    (
                        "record",
                        "--topic",
                        self._recognition_topic()["id"],
                        "--skill",
                        "recognition",
                        "--score",
                        "1",
                        "--max-score",
                        "1",
                        "--attempt-id",
                        "unsafe-write",
                    ),
                ):
                    rejected = _run_cli(
                        unsafe, *arguments, expected_returncode=None
                    )
                    self.assertNotEqual(rejected.returncode, 0)
                    self.assertIn("Git", rejected.stderr)
                self.assertEqual(before, _snapshot_files(unsafe))
                self.assertFalse((unsafe / ".tutor.lock").exists())

    def test_record_keeps_right_and_wrong_evidence_and_is_idempotent(self) -> None:
        topic_id = self._recognition_topic()["id"]
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)

            _run_cli(
                data_dir,
                "record",
                "--topic",
                topic_id,
                "--skill",
                "recognition",
                "--score",
                "0",
                "--max-score",
                "1",
                "--attempt-id",
                "wrong-001",
                "--at",
                "2026-08-10T09:00:00+08:00",
                "--wrong-reason",
                "knowledge_gap",
                "--source",
                "exam-bank",
            )
            after_wrong = _snapshot_files(data_dir)
            self.assertTrue(after_wrong)

            # Replaying an external event must be a no-op, not a second attempt.
            _run_cli(
                data_dir,
                "record",
                "--topic",
                topic_id,
                "--skill",
                "recognition",
                "--score",
                "0",
                "--max-score",
                "1",
                "--attempt-id",
                "wrong-001",
                "--at",
                "2026-08-10T09:00:00+08:00",
                "--wrong-reason",
                "knowledge_gap",
                "--source",
                "exam-bank",
            )
            self.assertEqual(after_wrong, _snapshot_files(data_dir))

            conflict = _run_cli(
                data_dir,
                "record",
                "--topic",
                topic_id,
                "--skill",
                "recognition",
                "--score",
                "1",
                "--max-score",
                "1",
                "--attempt-id",
                "wrong-001",
                "--at",
                "2026-08-10T09:00:00+08:00",
                "--source",
                "exam-bank",
                expected_returncode=None,
            )
            self.assertNotEqual(conflict.returncode, 0)
            self.assertIn("冲突", conflict.stderr)
            self.assertEqual(after_wrong, _snapshot_files(data_dir))

            _run_cli(
                data_dir,
                "record",
                "--topic",
                topic_id,
                "--skill",
                "recognition",
                "--score",
                "1",
                "--max-score",
                "1",
                "--attempt-id",
                "right-001",
                "--at",
                "2026-08-10T09:10:00+08:00",
                "--source",
                "exam-bank",
            )
            status = self._status(data_dir)
            topic_record = _find_topic_record(status, topic_id)
            serialized = json.dumps(topic_record, ensure_ascii=False)
            self.assertIn("knowledge_gap", serialized)

            evidence_counts = [
                value
                for key in ("attempt_count", "attempts", "evidence_count")
                for value in _values_for_key(topic_record, key)
                if isinstance(value, (int, float))
            ]
            self.assertTrue(evidence_counts, "status must expose an evidence count")
            self.assertGreaterEqual(max(evidence_counts), 2)

    def test_one_correct_answer_is_not_mastery(self) -> None:
        topic_id = self._recognition_topic()["id"]
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            _run_cli(
                data_dir,
                "record",
                "--topic",
                topic_id,
                "--skill",
                "recognition",
                "--score",
                "1",
                "--max-score",
                "1",
                "--attempt-id",
                "single-lucky-answer",
                "--at",
                "2026-08-10T09:00:00+08:00",
            )

            label = _status_label(_find_topic_record(self._status(data_dir), topic_id))
            self.assertNotIn(label, PASS_READY_STATES)

    def test_record_requires_a_stable_item_id(self) -> None:
        topic_id = self._recognition_topic()["id"]
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            rejected = subprocess.run(
                [
                    sys.executable,
                    str(TUTOR_SCRIPT),
                    "--data-dir",
                    str(data_dir),
                    "record",
                    "--topic",
                    topic_id,
                    "--skill",
                    "recognition",
                    "--score",
                    "1",
                    "--max-score",
                    "1",
                    "--attempt-id",
                    "missing-item-id",
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("item-id", rejected.stderr)
            self.assertEqual(self._status(data_dir)["topics"], {})

    def test_recognition_mastery_requires_enough_cross_day_evidence(self) -> None:
        topic_id = self._recognition_topic()["id"]
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)

            for number in range(5):
                _run_cli(
                    data_dir,
                    "record",
                    "--topic",
                    topic_id,
                    "--skill",
                    "recognition",
                    "--score",
                    "1",
                    "--max-score",
                    "1",
                    "--attempt-id",
                    f"same-day-{number}",
                    "--at",
                    f"2026-08-10T09:{number:02d}:00+08:00",
                )

            same_day_label = _status_label(
                _find_topic_record(self._status(data_dir), topic_id)
            )
            self.assertNotIn(same_day_label, PASS_READY_STATES)

            _run_cli(
                data_dir,
                "record",
                "--topic",
                topic_id,
                "--skill",
                "recognition",
                "--score",
                "1",
                "--max-score",
                "1",
                "--attempt-id",
                "cross-day-006",
                "--at",
                "2026-08-12T09:00:00+08:00",
            )
            cross_day_label = _status_label(
                _find_topic_record(self._status(data_dir), topic_id)
            )
            self.assertIn(cross_day_label, PASS_READY_STATES)

            _run_cli(
                data_dir,
                "record",
                "--topic",
                topic_id,
                "--skill",
                "recognition",
                "--score",
                "0",
                "--max-score",
                "1",
                "--attempt-id",
                "new-variant-failed",
                "--at",
                "2026-08-13T09:00:00+08:00",
                "--wrong-reason",
                "concept_confusion",
            )
            regressed = _find_topic_record(self._status(data_dir), topic_id)
            self.assertEqual(regressed["mastery"]["recognition"]["status"], "fragile")
            self.assertEqual(
                regressed["mastery"]["recognition"]["next_review_at"],
                "2026-08-14",
            )
            _run_cli(
                data_dir,
                "record",
                "--topic",
                topic_id,
                "--skill",
                "recognition",
                "--score",
                "1",
                "--max-score",
                "1",
                "--attempt-id",
                "one-minute-quick-fix",
                "--at",
                "2026-08-13T09:01:00+08:00",
            )
            still_fragile = _find_topic_record(self._status(data_dir), topic_id)
            self.assertEqual(
                still_fragile["mastery"]["recognition"]["status"], "fragile"
            )
            self.assertEqual(
                still_fragile["mastery"]["recognition"]["next_review_at"],
                "2026-08-14",
            )

    def test_repeating_one_item_never_counts_as_independent_mastery(self) -> None:
        topic_id = self._recognition_topic()["id"]
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            for number in range(6):
                day = 10 if number < 3 else 12
                _run_cli(
                    data_dir,
                    "record",
                    "--topic",
                    topic_id,
                    "--skill",
                    "recognition",
                    "--score",
                    "1",
                    "--max-score",
                    "1",
                    "--attempt-id",
                    f"same-item-attempt-{number}",
                    "--item-id",
                    "one-question-only",
                    "--at",
                    f"2026-08-{day:02d}T09:{number:02d}:00+08:00",
                )
            label = _status_label(_find_topic_record(self._status(data_dir), topic_id))
            self.assertNotIn(label, PASS_READY_STATES)

    def test_aggregate_topic_requires_coverage_of_declared_facets(self) -> None:
        topic_id = "K05.TEST_CMMI_PATTERNS"
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            for number in range(6):
                day = 10 if number < 5 else 12
                _run_cli(
                    data_dir,
                    "record",
                    "--topic",
                    topic_id,
                    "--skill",
                    "recognition",
                    "--facet",
                    "cmmi",
                    "--score",
                    "1",
                    "--max-score",
                    "1",
                    "--attempt-id",
                    f"cmmi-only-{number}",
                    "--item-id",
                    f"cmmi-item-{number}",
                    "--at",
                    f"2026-08-{day:02d}T09:{number:02d}:00+08:00",
                )
            cmmi_only = _find_topic_record(self._status(data_dir), topic_id)
            self.assertNotIn(
                cmmi_only["mastery"]["recognition"]["status"], PASS_READY_STATES
            )

            for facet, day in (("testing", 13), ("design_patterns", 14)):
                _run_cli(
                    data_dir,
                    "record",
                    "--topic",
                    topic_id,
                    "--skill",
                    "recognition",
                    "--facet",
                    facet,
                    "--score",
                    "1",
                    "--max-score",
                    "1",
                    "--attempt-id",
                    f"facet-{facet}",
                    "--item-id",
                    f"facet-item-{facet}",
                    "--at",
                    f"2026-08-{day:02d}T09:00:00+08:00",
                )
            covered = _find_topic_record(self._status(data_dir), topic_id)
            self.assertIn(
                covered["mastery"]["recognition"]["status"], PASS_READY_STATES
            )

    def test_cross_subject_topic_exposes_unmeasured_dimensions(self) -> None:
        topic = next(
            item
            for item in self.topics
            if {"recognition", "application", "production"}.issubset(
                item.get("skills", [])
            )
        )
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            for number in range(6):
                day = 10 if number < 5 else 12
                _run_cli(
                    data_dir,
                    "record",
                    "--topic",
                    topic["id"],
                    "--skill",
                    "recognition",
                    "--score",
                    "1",
                    "--max-score",
                    "1",
                    "--attempt-id",
                    f"only-recognition-{number}",
                    "--item-id",
                    f"recognition-item-{number}",
                    "--at",
                    f"2026-08-{day:02d}T09:{number:02d}:00+08:00",
                )
            topic_record = _find_topic_record(self._status(data_dir), topic["id"])
            self.assertEqual(topic_record["mastery"]["recognition"]["status"], "pass_ready")
            self.assertNotIn(_status_label(topic_record), PASS_READY_STATES)
            self.assertNotIn("application", topic_record["mastery"])
            self.assertNotIn("production", topic_record["mastery"])

    def test_case_mastery_requires_two_independent_items_48_hours_apart(self) -> None:
        topic_id = "C01.CASE_ATAM"
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            for attempt_id, item_id, at in (
                ("case-early-1", "case-item-1", "2026-08-10T23:30:00+08:00"),
                ("case-early-2", "case-item-2", "2026-08-12T00:30:00+08:00"),
            ):
                _run_cli(
                    data_dir,
                    "record",
                    "--topic",
                    topic_id,
                    "--skill",
                    "application",
                    "--score",
                    "15",
                    "--max-score",
                    "25",
                    "--attempt-id",
                    attempt_id,
                    "--item-id",
                    item_id,
                    "--at",
                    at,
                )
            early = _status_label(_find_topic_record(self._status(data_dir), topic_id))
            self.assertNotIn(early, PASS_READY_STATES)

            _run_cli(
                data_dir,
                "record",
                "--topic",
                topic_id,
                "--skill",
                "application",
                "--score",
                "15",
                "--max-score",
                "25",
                "--attempt-id",
                "case-after-48h",
                "--item-id",
                "case-item-3",
                "--at",
                "2026-08-12T23:31:00+08:00",
            )
            ready = _status_label(_find_topic_record(self._status(data_dir), topic_id))
            self.assertIn(ready, PASS_READY_STATES)

    def test_case_spacing_must_be_between_distinct_items(self) -> None:
        topic_id = "C01.CASE_ATAM"
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            for attempt_id, item_id, at in (
                ("case-a-first", "case-a", "2026-08-10T09:00:00+08:00"),
                ("case-b-middle", "case-b", "2026-08-11T09:00:00+08:00"),
                ("case-a-repeat", "case-a", "2026-08-12T09:00:00+08:00"),
            ):
                _run_cli(
                    data_dir,
                    "record",
                    "--topic",
                    topic_id,
                    "--skill",
                    "application",
                    "--score",
                    "15",
                    "--max-score",
                    "25",
                    "--attempt-id",
                    attempt_id,
                    "--item-id",
                    item_id,
                    "--at",
                    at,
                )
            label = _status_label(_find_topic_record(self._status(data_dir), topic_id))
            self.assertNotIn(label, PASS_READY_STATES)

    def test_essay_requires_a_full_timed_passing_essay_itself(self) -> None:
        topic_id = "P01.ESSAY_ARCHITECTURE"
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            for attempt_id, item_id, score, maximum, mode in (
                ("great-outline", "outline-1", 10, 10, "practice"),
                ("failed-full-essay", "essay-1", 40, 75, "full_timed"),
            ):
                full_essay_evidence = (
                    ("--duration-seconds", "7200", "--word-count", "2600", "--complete")
                    if mode == "full_timed"
                    else ()
                )
                _run_cli(
                    data_dir,
                    "record",
                    "--topic",
                    topic_id,
                    "--skill",
                    "production",
                    "--score",
                    str(score),
                    "--max-score",
                    str(maximum),
                    "--attempt-id",
                    attempt_id,
                    "--item-id",
                    item_id,
                    "--mode",
                    mode,
                    "--at",
                    "2026-08-10T10:00:00+08:00",
                    *full_essay_evidence,
                )
            failed = _status_label(_find_topic_record(self._status(data_dir), topic_id))
            self.assertNotIn(failed, PASS_READY_STATES)

            _run_cli(
                data_dir,
                "record",
                "--topic",
                topic_id,
                "--skill",
                "production",
                "--score",
                "52",
                "--max-score",
                "75",
                "--attempt-id",
                "passing-full-essay",
                "--item-id",
                "essay-2",
                "--mode",
                "full_timed",
                "--duration-seconds",
                "7200",
                "--word-count",
                "2700",
                "--complete",
                "--at",
                "2026-08-12T10:00:00+08:00",
            )
            ready = _status_label(_find_topic_record(self._status(data_dir), topic_id))
            self.assertIn(ready, PASS_READY_STATES)

            _run_cli(
                data_dir,
                "record",
                "--topic",
                topic_id,
                "--skill",
                "production",
                "--score",
                "10",
                "--max-score",
                "10",
                "--attempt-id",
                "outline-after-passing-essay",
                "--item-id",
                "outline-after-pass",
                "--mode",
                "practice",
                "--at",
                "2026-08-13T10:00:00+08:00",
            )
            after_outline = _find_topic_record(self._status(data_dir), topic_id)
            self.assertIn(_status_label(after_outline), PASS_READY_STATES)
            self.assertEqual(
                after_outline["mastery"]["production"]["next_review_at"],
                "2026-08-26",
            )

    def test_cold_start_rotates_diagnostics_across_all_three_subjects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)

            def target() -> str:
                payload = _json_output(
                    _run_cli(
                        data_dir,
                        "recommend",
                        "--json",
                        "--limit",
                        "3",
                        "--today",
                        "2026-08-10",
                    )
                )
                return payload["target_subject"]

            self.assertEqual(target(), "comprehensive")
            _run_cli(
                data_dir,
                "record",
                "--topic",
                "K22.ENGLISH_READING",
                "--skill",
                "recognition",
                "--score",
                "0",
                "--max-score",
                "1",
                "--attempt-id",
                "cold-comprehensive",
                "--item-id",
                "cold-comprehensive-item",
                "--at",
                "2026-08-10T09:00:00+08:00",
            )
            self.assertEqual(target(), "case")
            _run_cli(
                data_dir,
                "record",
                "--topic",
                "C01.CASE_ATAM",
                "--skill",
                "application",
                "--score",
                "0",
                "--max-score",
                "25",
                "--attempt-id",
                "cold-case",
                "--item-id",
                "cold-case-item",
                "--at",
                "2026-08-10T09:10:00+08:00",
            )
            self.assertEqual(target(), "essay")

    def test_first_comprehensive_diagnostic_starts_with_declared_core_domains(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            payload = _json_output(
                _run_cli(
                    data_dir,
                    "recommend",
                    "--json",
                    "--subject",
                    "comprehensive",
                    "--limit",
                    "5",
                    "--today",
                    "2026-08-10",
                )
            )
            first_group = set(
                self.curriculum["strategy"]["comprehensive_cold_start_groups"][0]
            )
            recommended = {
                _recommendation_topic_id(item)
                for item in _recommendation_items(payload)
            }
            self.assertTrue(recommended.issubset(first_group))

    def test_last_three_days_only_recommends_existing_or_survival_material(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            payload = _json_output(
                _run_cli(
                    data_dir,
                    "recommend",
                    "--json",
                    "--subject",
                    "comprehensive",
                    "--limit",
                    "8",
                    "--today",
                    "2026-11-05",
                )
            )
            self.assertTrue(payload["crunch_mode"])
            self.assertEqual(payload["days_to_exam"], 2)
            items = _recommendation_items(payload)
            self.assertTrue(items)
            for item in items:
                self.assertTrue(
                    any(
                        "SURVIVAL.md" in resource
                        or resource.startswith("cheatsheets/")
                        for resource in item["resources"]
                    ),
                    item,
                )

    def test_weak_mock_subject_gets_non_equal_priority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            for subject, score, minute in (
                ("comprehensive", 75, 0),
                ("case", 44, 1),
                ("essay", 75, 2),
            ):
                _run_cli(
                    data_dir,
                    "mock",
                    "--subject",
                    subject,
                    "--mock-id",
                    f"weak-subject-{subject}",
                    "--paper-id",
                    f"fixture-{subject}-001",
                    "--score",
                    str(score),
                    "--max-score",
                    "75",
                    "--duration-minutes",
                    "90",
                    "--complete",
                    "--at",
                    f"2026-08-10T10:0{minute}:00+08:00",
                )

            status = self._status(data_dir)
            status_text = json.dumps(status, ensure_ascii=False)
            self.assertIn("44", status_text)
            for subject in SUBJECTS:
                self.assertIn(subject, status_text)

            recommendation = _json_output(
                _run_cli(
                    data_dir,
                    "recommend",
                    "--json",
                    "--limit",
                    "12",
                    "--today",
                    "2026-08-10",
                )
            )
            allocation = _find_subject_allocation(recommendation)
            self.assertGreater(allocation["case"], allocation["comprehensive"])
            self.assertGreater(allocation["case"], allocation["essay"])
            self.assertGreater(len(set(allocation.values())), 1, "subjects were averaged")

            items = _recommendation_items(recommendation)
            self.assertTrue(items)
            first = items[0]
            first_subject = first.get("subject")
            if first_subject is None:
                topic_id = _recommendation_topic_id(first)
                topic = next(topic for topic in self.topics if topic["id"] == topic_id)
                self.assertIn("case", topic["subjects"])
            else:
                self.assertEqual(first_subject, "case")

    def test_danger_subject_remains_primary_while_overdue_safe_subject_is_maintained(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            for subject, score, at in (
                ("case", 70, "2026-06-30T10:00:00+08:00"),
                ("essay", 70, "2026-08-09T10:00:00+08:00"),
                ("comprehensive", 44, "2026-08-10T10:00:00+08:00"),
            ):
                _run_cli(
                    data_dir,
                    "mock",
                    "--subject",
                    subject,
                    "--mock-id",
                    f"hard-gate-{subject}",
                    "--paper-id",
                    f"hard-gate-paper-{subject}",
                    "--score",
                    str(score),
                    "--max-score",
                    "75",
                    "--duration-minutes",
                    "90",
                    "--complete",
                    "--at",
                    at,
                )
            payload = _json_output(
                _run_cli(
                    data_dir,
                    "recommend",
                    "--json",
                    "--limit",
                    "4",
                    "--today",
                    "2026-08-10",
                )
            )
            self.assertEqual(payload["target_subject"], "comprehensive")
            self.assertEqual(payload["maintenance_subject"], "case")
            self.assertGreater(payload["subject_allocation"]["comprehensive"], 0.5)
            self.assertGreater(
                payload["subject_allocation"]["comprehensive"],
                payload["subject_allocation"]["case"],
            )
            items = _recommendation_items(payload)
            self.assertEqual(items[0]["subject"], "comprehensive")
            self.assertTrue(any(item["subject"] == "case" for item in items[1:]))

    def test_mock_is_complete_75_point_evidence_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            arguments = (
                "mock",
                "--subject",
                "comprehensive",
                "--mock-id",
                "mock-idempotent-001",
                "--paper-id",
                "fixture-comprehensive-001",
                "--score",
                "50",
                "--max-score",
                "75",
                "--duration-minutes",
                "120",
                "--complete",
                "--at",
                "2026-08-10T10:00:00+08:00",
            )
            _run_cli(data_dir, *arguments)
            first = self._status(data_dir)
            _run_cli(data_dir, *arguments)
            second = self._status(data_dir)
            self.assertEqual(first, second)
            comprehensive = second["subjects"]["comprehensive"]
            self.assertEqual(comprehensive["evidence_level"], "low")
            self.assertEqual(len(comprehensive["mock_scores"]), 1)

            rejected = _run_cli(
                data_dir,
                "mock",
                "--subject",
                "comprehensive",
                "--mock-id",
                "fake-one-point-mock",
                "--paper-id",
                "one-question",
                "--score",
                "1",
                "--max-score",
                "1",
                "--duration-minutes",
                "1",
                "--complete",
                expected_returncode=None,
            )
            self.assertNotEqual(rejected.returncode, 0)

    def test_high_frequency_weak_topic_precedes_low_frequency_weak_topic(self) -> None:
        comparable_group = set(
            self.curriculum["strategy"]["comprehensive_cold_start_groups"][0]
        )
        candidates = [
            topic
            for topic in self.topics
            if "comprehensive" in topic.get("subjects", [])
            and "recognition" in topic.get("skills", [])
            and topic["id"] in comparable_group
        ]
        self.assertGreaterEqual(len(candidates), 2)
        comparable_pairs = [
            (left, right)
            for left in candidates
            for right in candidates
            if left["estimated_minutes"] == right["estimated_minutes"]
            and float(left["frequency_count"]) > float(right["frequency_count"])
        ]
        self.assertTrue(comparable_pairs, "curriculum needs a cost-comparable frequency pair")
        high, low = max(
            comparable_pairs,
            key=lambda pair: float(pair[0]["frequency_count"])
            - float(pair[1]["frequency_count"]),
        )

        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            for topic, suffix in ((high, "high"), (low, "low")):
                _run_cli(
                    data_dir,
                    "record",
                    "--topic",
                    topic["id"],
                    "--skill",
                    "recognition",
                    "--score",
                    "0",
                    "--max-score",
                    "1",
                    "--attempt-id",
                    f"weak-{suffix}",
                    "--at",
                    "2026-08-10T11:00:00+08:00",
                    "--wrong-reason",
                    "knowledge_gap",
                )

            arguments = (
                "recommend",
                "--json",
                "--subject",
                "comprehensive",
                "--limit",
                str(len(candidates)),
                "--today",
                "2026-08-10",
            )
            first_payload = _json_output(_run_cli(data_dir, *arguments))
            second_payload = _json_output(_run_cli(data_dir, *arguments))
            first_ids = [
                _recommendation_topic_id(item)
                for item in _recommendation_items(first_payload)
            ]
            second_ids = [
                _recommendation_topic_id(item)
                for item in _recommendation_items(second_payload)
            ]
            self.assertEqual(first_ids, second_ids, "first choice must be deterministic")
            self.assertIn(high["id"], first_ids)
            self.assertIn(low["id"], first_ids)
            self.assertLess(first_ids.index(high["id"]), first_ids.index(low["id"]))

    def test_mastered_case_strategy_track_yields_to_an_unseen_weak_track(self) -> None:
        primary = next(topic for topic in self.topics if topic["id"] == "C01.CASE_ATAM")
        fallback = next(topic for topic in self.topics if topic["id"] == "C02.CASE_DATABASE")
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            for number, at in enumerate(
                ("2026-08-10T09:00:00+08:00", "2026-08-12T09:00:00+08:00"),
                1,
            ):
                _run_cli(
                    data_dir,
                    "record",
                    "--topic",
                    primary["id"],
                    "--skill",
                    "application",
                    "--score",
                    "15",
                    "--max-score",
                    "25",
                    "--attempt-id",
                    f"atam-pass-{number}",
                    "--item-id",
                    f"atam-case-{number}",
                    "--at",
                    at,
                )

            payload = _json_output(
                _run_cli(
                    data_dir,
                    "recommend",
                    "--json",
                    "--subject",
                    "case",
                    "--limit",
                    str(len(self.topics)),
                    "--today",
                    "2026-08-13",
                )
            )
            ids = [
                _recommendation_topic_id(item)
                for item in _recommendation_items(payload)
            ]
            self.assertLess(ids.index(fallback["id"]), ids.index(primary["id"]))

    def test_configured_case_and_essay_routes_filter_unselected_tracks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            _run_cli(
                data_dir,
                "configure",
                "--case-track",
                "C02.CASE_DATABASE",
                "--essay-theme",
                "P03.ESSAY_RELIABILITY",
                "--skip-topic",
                "K07.REALTIME_EMBEDDED=当前低收益",
            )
            status = self._status(data_dir)
            self.assertEqual(status["strategy"]["case_tracks"], ["C02.CASE_DATABASE"])
            self.assertEqual(
                status["strategy"]["essay_themes"], ["P03.ESSAY_RELIABILITY"]
            )
            self.assertIn("K07.REALTIME_EMBEDDED", status["strategy"]["strategic_skips"])
            for subject, expected_prefix, expected_id in (
                ("case", "C", "C02.CASE_DATABASE"),
                ("essay", "P", "P03.ESSAY_RELIABILITY"),
            ):
                payload = _json_output(
                    _run_cli(
                        data_dir,
                        "recommend",
                        "--json",
                        "--subject",
                        subject,
                        "--limit",
                        str(len(self.topics)),
                        "--today",
                        "2026-08-10",
                    )
                )
                canonical_ids = [
                    _recommendation_topic_id(item)
                    for item in _recommendation_items(payload)
                    if _recommendation_topic_id(item).startswith(expected_prefix)
                ]
                self.assertEqual(canonical_ids, [expected_id])

            comprehensive = _json_output(
                _run_cli(
                    data_dir,
                    "recommend",
                    "--json",
                    "--subject",
                    "comprehensive",
                    "--limit",
                    str(len(self.topics)),
                    "--today",
                    "2026-08-10",
                )
            )
            comprehensive_ids = {
                _recommendation_topic_id(item)
                for item in _recommendation_items(comprehensive)
            }
            self.assertNotIn("K07.REALTIME_EMBEDDED", comprehensive_ids)

    def test_mastery_is_not_shared_across_subject_skills(self) -> None:
        topic = next(
            item
            for item in self.topics
            if {"recognition", "application"}.issubset(item.get("skills", []))
            and {"comprehensive", "case"}.issubset(item.get("subjects", []))
        )
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            for number in range(6):
                day = 10 if number < 5 else 12
                _run_cli(
                    data_dir,
                    "record",
                    "--topic",
                    topic["id"],
                    "--skill",
                    "recognition",
                    "--score",
                    "1",
                    "--max-score",
                    "1",
                    "--attempt-id",
                    f"cross-skill-{number}",
                    "--at",
                    f"2026-08-{day:02d}T09:{number:02d}:00+08:00",
                )

            payload = _json_output(
                _run_cli(
                    data_dir,
                    "recommend",
                    "--json",
                    "--subject",
                    "case",
                    "--limit",
                    str(len(self.topics)),
                    "--today",
                    "2026-08-12",
                )
            )
            recommendation = next(
                item
                for item in _recommendation_items(payload)
                if _recommendation_topic_id(item) == topic["id"]
            )
            self.assertEqual(
                recommendation.get("mastery"),
                0,
                "recognition mastery must not reduce case/application priority",
            )

    def test_recognition_review_date_does_not_mark_application_due(self) -> None:
        topic = next(
            item
            for item in self.topics
            if {"recognition", "application"}.issubset(item.get("skills", []))
            and {"comprehensive", "case"}.issubset(item.get("subjects", []))
        )
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            _run_cli(
                data_dir,
                "record",
                "--topic",
                topic["id"],
                "--skill",
                "recognition",
                "--score",
                "0",
                "--max-score",
                "1",
                "--attempt-id",
                "recognition-due-only",
                "--at",
                "2026-08-10T09:00:00+08:00",
            )
            payload = _json_output(
                _run_cli(
                    data_dir,
                    "recommend",
                    "--json",
                    "--subject",
                    "case",
                    "--limit",
                    str(len(self.topics)),
                    "--today",
                    "2026-08-12",
                )
            )
            application_item = next(
                item
                for item in _recommendation_items(payload)
                if _recommendation_topic_id(item) == topic["id"]
            )
            self.assertFalse(application_item["review_due"])

    def test_pending_wal_event_replays_without_double_count(self) -> None:
        topic_id = self._recognition_topic()["id"]
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            initial_state = (data_dir / "state.json").read_bytes()
            initial_backup = (data_dir / "state.json.bak").read_bytes()
            arguments = (
                "record",
                "--topic",
                topic_id,
                "--skill",
                "recognition",
                "--score",
                "1",
                "--max-score",
                "1",
                "--attempt-id",
                "transaction-retry-001",
                "--at",
                "2026-08-10T09:00:00+08:00",
            )
            _run_cli(data_dir, *arguments)
            # Simulate a stop after the write-ahead event committed but before
            # its derived state replacement. Reading status must replay it.
            (data_dir / "state.json").write_bytes(initial_state)
            (data_dir / "state.json.bak").write_bytes(initial_backup)

            topic = _find_topic_record(self._status(data_dir), topic_id)
            attempt_counts = [
                value
                for value in _values_for_key(topic, "attempt_count")
                if isinstance(value, (int, float))
            ]
            self.assertIn(1, attempt_counts)
            events = [
                json.loads(line)
                for line in (data_dir / "attempts.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            self.assertEqual(
                [event["attempt_id"] for event in events], ["transaction-retry-001"]
            )

    def test_missing_log_evidence_is_detected_and_repair_uses_the_log_as_truth(self) -> None:
        topic_id = self._recognition_topic()["id"]
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            _run_cli(
                data_dir,
                "record",
                "--topic",
                topic_id,
                "--skill",
                "recognition",
                "--score",
                "1",
                "--max-score",
                "1",
                "--attempt-id",
                "ghost-state-evidence",
                "--at",
                "2026-08-10T09:00:00+08:00",
            )
            (data_dir / "attempts.jsonl").write_text("", encoding="utf-8")
            doctor = _run_cli(data_dir, "doctor", expected_returncode=None)
            self.assertNotEqual(doctor.returncode, 0)
            self.assertIn("不存在", doctor.stdout)

            _run_cli(data_dir, "repair")
            repaired = self._status(data_dir)
            self.assertEqual(repaired["topics"], {})
            _run_cli(data_dir, "doctor")

    def test_concurrent_records_are_serialized_without_lost_progress(self) -> None:
        topic_id = self._recognition_topic()["id"]
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            processes: list[subprocess.Popen[str]] = []
            for number in range(12):
                command = [
                    sys.executable,
                    str(TUTOR_SCRIPT),
                    "--data-dir",
                    str(data_dir),
                    "record",
                    "--topic",
                    topic_id,
                    "--skill",
                    "recognition",
                    "--score",
                    "1",
                    "--max-score",
                    "1",
                    "--attempt-id",
                    f"concurrent-{number}",
                    "--item-id",
                    f"concurrent-item-{number}",
                    "--at",
                    f"2026-08-10T09:{number:02d}:00+08:00",
                ]
                processes.append(
                    subprocess.Popen(
                        command,
                        cwd=REPO_ROOT,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                )
            failures = []
            for process in processes:
                stdout, stderr = process.communicate(timeout=30)
                if process.returncode != 0:
                    failures.append((process.returncode, stdout, stderr))
            self.assertEqual(failures, [])

            topic = _find_topic_record(self._status(data_dir), topic_id)
            self.assertEqual(topic["mastery"]["recognition"]["attempt_count"], 12)
            events = [
                json.loads(line)
                for line in (data_dir / "attempts.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            self.assertEqual(len(events), 12)
            self.assertEqual(len({event["attempt_id"] for event in events}), 12)

    def test_corrupt_state_is_not_overwritten_and_repair_recovers_it(self) -> None:
        topic_id = self._recognition_topic()["id"]
        with tempfile.TemporaryDirectory() as temporary:
            data_dir = Path(temporary)
            self._init(data_dir)
            _run_cli(
                data_dir,
                "record",
                "--topic",
                topic_id,
                "--skill",
                "recognition",
                "--score",
                "0",
                "--max-score",
                "1",
                "--attempt-id",
                "before-corruption",
                "--at",
                "2026-08-10T12:00:00+08:00",
            )
            state_file = _primary_state_file(data_dir)
            corrupt_bytes = b'{"schema_version": 1, "learner": '
            state_file.write_bytes(corrupt_bytes)

            failed_write = _run_cli(
                data_dir,
                "record",
                "--topic",
                topic_id,
                "--skill",
                "recognition",
                "--score",
                "1",
                "--max-score",
                "1",
                "--attempt-id",
                "must-not-overwrite-corrupt-state",
                expected_returncode=None,
            )
            self.assertNotEqual(failed_write.returncode, 0)
            self.assertEqual(state_file.read_bytes(), corrupt_bytes)

            doctor = _run_cli(
                data_dir,
                "doctor",
                "--json",
                expected_returncode=None,
            )
            self.assertIn(
                doctor.returncode,
                (0, 1),
                f"doctor crashed unexpectedly: {doctor.stderr}",
            )
            diagnosis = (doctor.stdout + doctor.stderr).lower()
            self.assertRegex(diagnosis, r"corrupt|invalid|unhealthy|false|error")

            _run_cli(data_dir, "repair")
            repaired_status = self._status(data_dir)
            self.assertIsInstance(repaired_status, dict)
            self.assertNotEqual(state_file.read_bytes(), corrupt_bytes)
            json.loads(state_file.read_text(encoding="utf-8"))

            # A syntactically valid rollback is not enough: attempts.jsonl is
            # the durable evidence source, so repair must not silently forget
            # the last accepted answer. Otherwise replay is also impossible,
            # because the attempt ID will correctly be treated as a duplicate.
            repaired_topic = _find_topic_record(repaired_status, topic_id)
            repaired_counts = [
                value
                for key in ("attempt_count", "attempts", "evidence_count")
                for value in _values_for_key(repaired_topic, key)
                if isinstance(value, (int, float))
            ]
            self.assertTrue(repaired_counts, "repair lost the topic evidence")
            self.assertGreaterEqual(max(repaired_counts), 1)


class RepositoryContractTest(unittest.TestCase):
    def test_init_refuses_an_unignored_directory_inside_the_repository(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temporary:
            data_dir = Path(temporary)
            rejected = _run_cli(
                data_dir,
                "init",
                "--daily-minutes",
                "45",
                expected_returncode=None,
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("Git", rejected.stderr)
            self.assertEqual(list(data_dir.iterdir()), [])

    def test_all_private_study_files_are_gitignored(self) -> None:
        tracked = subprocess.run(
            ["git", "ls-files", "--", ".study"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(tracked.stdout.strip(), "", ".study must never be tracked")

        for candidate in (
            ".study/state.json",
            ".study/events.jsonl",
            ".study/backups/state.json",
            ".study/arbitrary/nested/private-note.txt",
        ):
            with self.subTest(candidate=candidate):
                ignored = subprocess.run(
                    ["git", "check-ignore", "--no-index", "-q", candidate],
                    cwd=REPO_ROOT,
                    check=False,
                )
                self.assertEqual(ignored.returncode, 0, f"not gitignored: {candidate}")

    def test_agent_documentation_local_references_exist(self) -> None:
        documents = (
            REPO_ROOT / ".claude" / "agents" / "senior-architect-pass-coach.md",
            REPO_ROOT / "AGENTS.md",
            REPO_ROOT / "CLAUDE.md",
            REPO_ROOT / "tutor" / "README.md",
            REPO_ROOT / "tutor" / "PROGRESS_PROTOCOL.md",
        )
        for document in documents:
            self.assertTrue(document.is_file(), f"missing agent document: {document}")

        local_reference_count = 0
        link_pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
        for document in documents:
            text = document.read_text(encoding="utf-8")
            for raw_target in link_pattern.findall(text):
                target = raw_target.strip().strip("<>").split(maxsplit=1)[0]
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                path_part = unquote(target.split("#", 1)[0])
                if not path_part:
                    continue
                local_reference_count += 1
                referenced = Path(path_part)
                if not referenced.is_absolute():
                    referenced = document.parent / referenced
                self.assertTrue(
                    referenced.resolve().exists(),
                    f"broken local reference in {document}: {raw_target}",
                )
        self.assertGreater(local_reference_count, 0, "agent docs need local references")

    def test_exam_bank_questions_have_matching_answers(self) -> None:
        bank_files = sorted(
            path for path in (REPO_ROOT / "exam-bank").glob("*.md") if path.name != "README.md"
        )
        self.assertTrue(bank_files)

        seen_question_ids: set[str] = set()
        for bank_file in bank_files:
            text = bank_file.read_text(encoding="utf-8")
            headings = list(re.finditer(r"(?m)^###\s+(\d+)\.\s+", text))
            self.assertTrue(headings, f"no questions found in {bank_file}")
            numbers = [int(heading.group(1)) for heading in headings]
            self.assertEqual(numbers, list(range(1, len(numbers) + 1)), bank_file)

            for index, heading in enumerate(headings):
                question_number = int(heading.group(1))
                end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
                block = text[heading.start() : end]
                question_id = f"{bank_file.stem}.q{question_number:03d}"
                self.assertNotIn(question_id, seen_question_ids)
                seen_question_ids.add(question_id)

                options = re.findall(
                    r"(?m)^(?:✅\s+)?(?:\*\*)?([A-D])\.\s+",
                    block,
                )
                answers = re.findall(
                    r"(?m)^\*\*答案\*\*[：:]\s*(?:\*\*)?([A-D])",
                    block,
                )
                marked = re.findall(r"(?m)^✅\s+\*\*([A-D])\.", block)
                with self.subTest(question=question_id):
                    self.assertEqual(options, ["A", "B", "C", "D"])
                    self.assertEqual(len(answers), 1)
                    self.assertEqual(len(marked), 1)
                    self.assertEqual(answers[0], marked[0])


if __name__ == "__main__":
    unittest.main()
