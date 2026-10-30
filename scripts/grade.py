#!/usr/bin/env python3
"""Deterministic grading for subjective questions (case / essay).

Splits the grading loop into two halves so that scoring becomes reproducible:

1. The Agent (LLM) reads a learner's answer together with a machine-readable
   *rubric* and emits a *verdict*: for every key point, whether it was hit and
   which learner sentence is the evidence. It never computes the score.
2. This script validates both documents and deterministically computes the
   final score (sum of hit key-point weights minus deductions, clamped).

The learner's data stays local: files in, report out, no network.

Usage:
    python3 scripts/grade.py validate rubric.json
    python3 scripts/grade.py scaffold --ref case-2024-Q1 --subject case --max 25
    python3 scripts/grade.py grade --rubric rubric.json --verdict verdict.json [--out report.json]
    python3 scripts/grade.py selftest

Exit codes: 0 ok, 1 validation error, 2 usage error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
SUBJECTS = ("comprehensive", "case", "essay")
DEFAULT_PASS_RATIO = 0.6


class GradingError(Exception):
    """Raised when a rubric or verdict fails validation."""


# ---------------------------------------------------------------------------
# Rubric validation
# ---------------------------------------------------------------------------

def validate_rubric(rubric: dict[str, Any]) -> list[str]:
    """Validate a rubric dict. Returns warnings; raises GradingError on errors."""
    if not isinstance(rubric, dict):
        raise GradingError("rubric must be a JSON object")
    if rubric.get("schema_version") != SCHEMA_VERSION:
        raise GradingError(f"rubric.schema_version must be {SCHEMA_VERSION}")
    if not str(rubric.get("question_ref", "")).strip():
        raise GradingError("rubric.question_ref must be a non-empty string")
    if rubric.get("subject") not in SUBJECTS:
        raise GradingError(f"rubric.subject must be one of {SUBJECTS}")

    max_score = rubric.get("max_score")
    if not isinstance(max_score, (int, float)) or isinstance(max_score, bool) or max_score <= 0:
        raise GradingError("rubric.max_score must be a positive number")

    key_points = rubric.get("key_points")
    if not isinstance(key_points, list) or not key_points:
        raise GradingError("rubric.key_points must be a non-empty list")

    warnings: list[str] = []
    seen_ids: set[str] = set()
    total_weight = 0.0
    for i, kp in enumerate(key_points):
        where = f"key_points[{i}]"
        if not isinstance(kp, dict):
            raise GradingError(f"{where} must be an object")
        kp_id = str(kp.get("id", "")).strip()
        if not kp_id or kp_id in seen_ids:
            raise GradingError(f"{where}.id must be a unique non-empty string")
        seen_ids.add(kp_id)
        if not str(kp.get("desc", "")).strip():
            raise GradingError(f"{where}.desc must be a non-empty string")
        weight = kp.get("weight")
        if not isinstance(weight, (int, float)) or isinstance(weight, bool) or weight <= 0:
            raise GradingError(f"{where}.weight must be a positive number")
        aliases = kp.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(a, str) for a in aliases):
            raise GradingError(f"{where}.aliases must be a list of strings")
        total_weight += float(weight)

    if abs(total_weight - float(max_score)) > 1e-9:
        raise GradingError(
            f"sum of key_points weights ({total_weight:g}) must equal max_score ({max_score:g})"
        )

    common_errors = rubric.get("common_errors", [])
    if not isinstance(common_errors, list):
        raise GradingError("rubric.common_errors must be a list")
    error_ids: set[str] = set()
    for i, err in enumerate(common_errors):
        where = f"common_errors[{i}]"
        if not isinstance(err, dict):
            raise GradingError(f"{where} must be an object")
        err_id = str(err.get("id", "")).strip()
        if not err_id or err_id in error_ids:
            raise GradingError(f"{where}.id must be a unique non-empty string")
        error_ids.add(err_id)
        if not str(err.get("desc", "")).strip():
            raise GradingError(f"{where}.desc must be a non-empty string")
        deduct = err.get("deduct")
        if not isinstance(deduct, (int, float)) or isinstance(deduct, bool) or deduct < 0:
            raise GradingError(f"{where}.deduct must be a non-negative number")

    pass_score = rubric.get("pass_score")
    if pass_score is not None:
        if not isinstance(pass_score, (int, float)) or isinstance(pass_score, bool):
            raise GradingError("rubric.pass_score must be a number")
        if not 0 <= float(pass_score) <= float(max_score):
            raise GradingError("rubric.pass_score must be within [0, max_score]")

    if len(seen_ids) < 3:
        warnings.append("fewer than 3 key points: grading may be too coarse")
    return warnings


# ---------------------------------------------------------------------------
# Verdict validation
# ---------------------------------------------------------------------------

def validate_verdict(verdict: dict[str, Any], rubric: dict[str, Any]) -> list[str]:
    """Validate a verdict dict against its rubric. Returns warnings."""
    if not isinstance(verdict, dict):
        raise GradingError("verdict must be a JSON object")
    if verdict.get("schema_version") != SCHEMA_VERSION:
        raise GradingError(f"verdict.schema_version must be {SCHEMA_VERSION}")
    if verdict.get("question_ref") != rubric.get("question_ref"):
        raise GradingError(
            f"verdict.question_ref {verdict.get('question_ref')!r} does not match "
            f"rubric.question_ref {rubric.get('question_ref')!r}"
        )

    rubric_points = {kp["id"]: kp for kp in rubric["key_points"]}
    points = verdict.get("points")
    if not isinstance(points, list):
        raise GradingError("verdict.points must be a list")

    warnings: list[str] = []
    judged: set[str] = set()
    for i, pt in enumerate(points):
        where = f"points[{i}]"
        if not isinstance(pt, dict):
            raise GradingError(f"{where} must be an object")
        pt_id = str(pt.get("id", "")).strip()
        if pt_id not in rubric_points:
            raise GradingError(f"{where}.id {pt_id!r} is not defined in the rubric")
        if pt_id in judged:
            raise GradingError(f"{where}.id {pt_id!r} appears more than once")
        judged.add(pt_id)
        if not isinstance(pt.get("hit"), bool):
            raise GradingError(f"{where}.hit must be a boolean")
        if pt["hit"] and not str(pt.get("evidence", "")).strip():
            warnings.append(f"{where} ({pt_id}): hit without evidence quote")

    missing = [kp_id for kp_id in rubric_points if kp_id not in judged]
    if missing:
        raise GradingError(f"verdict.points is missing rubric key points: {', '.join(missing)}")

    rubric_errors = {err["id"] for err in rubric.get("common_errors", [])}
    errors_hit = verdict.get("errors_hit", [])
    if not isinstance(errors_hit, list):
        raise GradingError("verdict.errors_hit must be a list")
    if len(errors_hit) != len(set(errors_hit)):
        raise GradingError("verdict.errors_hit contains duplicates")
    for err_id in errors_hit:
        if err_id not in rubric_errors:
            raise GradingError(f"verdict.errors_hit entry {err_id!r} is not defined in the rubric")

    for field in ("typos",):
        value = verdict.get(field, [])
        if not isinstance(value, list) or any(not isinstance(t, str) for t in value):
            raise GradingError(f"verdict.{field} must be a list of strings")
    if verdict.get("comment") is not None and not isinstance(verdict["comment"], str):
        raise GradingError("verdict.comment must be a string")
    return warnings


# ---------------------------------------------------------------------------
# Deterministic score computation
# ---------------------------------------------------------------------------

def compute_report(rubric: dict[str, Any], verdict: dict[str, Any]) -> dict[str, Any]:
    """Compute the deterministic grading report. Assumes both are validated."""
    rubric_points = {kp["id"]: kp for kp in rubric["key_points"]}
    hit_map = {pt["id"]: pt for pt in verdict["points"]}

    point_rows: list[dict[str, Any]] = []
    earned = 0.0
    for kp_id, kp in rubric_points.items():
        hit = hit_map[kp_id]["hit"]
        evidence = hit_map[kp_id].get("evidence", "")
        if hit:
            earned += float(kp["weight"])
        point_rows.append(
            {"id": kp_id, "desc": kp["desc"], "weight": kp["weight"], "hit": hit, "evidence": evidence}
        )

    error_rows: list[dict[str, Any]] = []
    error_ids = set(verdict.get("errors_hit", []))
    deducted = 0.0
    for err in rubric.get("common_errors", []):
        if err["id"] in error_ids:
            deducted += float(err["deduct"])
            error_rows.append({"id": err["id"], "desc": err["desc"], "deduct": err["deduct"]})

    max_score = float(rubric["max_score"])
    raw_score = earned - deducted
    final_score = max(0.0, min(max_score, raw_score))
    # Whole numbers stay whole; otherwise round to one decimal.
    final_score = round(final_score, 1)
    if final_score == int(final_score):
        final_score = int(final_score)

    pass_score = rubric.get("pass_score")
    if pass_score is None:
        pass_score = round(max_score * DEFAULT_PASS_RATIO, 1)
    return {
        "schema_version": SCHEMA_VERSION,
        "question_ref": rubric["question_ref"],
        "subject": rubric["subject"],
        "max_score": rubric["max_score"],
        "pass_score": pass_score,
        "earned_points": round(earned, 1),
        "deductions": round(deducted, 1),
        "final_score": final_score,
        "passed": float(final_score) >= float(pass_score),
        "points": point_rows,
        "errors_hit": error_rows,
        "typos": verdict.get("typos", []),
        "comment": verdict.get("comment", ""),
    }


# ---------------------------------------------------------------------------
# Scaffold
# ---------------------------------------------------------------------------

def scaffold_rubric(question_ref: str, subject: str, max_score: float, n_points: int) -> dict[str, Any]:
    """Emit a rubric template whose key-point weights sum to max_score."""
    per = round(max_score / n_points, 1)
    weights = [per] * (n_points - 1) + [round(max_score - per * (n_points - 1), 1)]
    return {
        "schema_version": SCHEMA_VERSION,
        "question_ref": question_ref,
        "subject": subject,
        "max_score": max_score,
        "key_points": [
            {
                "id": f"KP{i + 1}",
                "desc": f"<踩分点 {i + 1}：描述该点考察的具体内容>",
                "weight": weights[i],
                "aliases": ["<同义表述1>", "<同义表述2>"],
            }
            for i in range(n_points)
        ],
        "common_errors": [
            {"id": "E1", "desc": "<常见错误/混淆点>", "deduct": 0},
        ],
        "notes": "weights 之和必须等于 max_score；LLM 只负责命中判断与证据引用，算分由 grade.py 完成",
    }


# ---------------------------------------------------------------------------
# IO helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        raise GradingError(f"{path}: invalid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise GradingError(f"{path}: top level must be a JSON object")
    return data


# ---------------------------------------------------------------------------
# Self test (stdlib only, mirrors tests/test_grade.py coverage)
# ---------------------------------------------------------------------------

def selftest() -> int:
    good_rubric = scaffold_rubric("case-2024-Q1", "case", 10, 4)
    assert validate_rubric(good_rubric) == []
    for mutator in (
        lambda r: r.update(schema_version=2),
        lambda r: r.update(max_score=99),
        lambda r: r["key_points"].pop(),
        lambda r: r["key_points"][0].update(weight=-1),
    ):
        bad = json.loads(json.dumps(good_rubric))
        mutator(bad)
        try:
            validate_rubric(bad)
        except GradingError:
            pass
        else:
            raise AssertionError("expected GradingError")

    verdict = {
        "schema_version": SCHEMA_VERSION,
        "question_ref": "case-2024-Q1",
        "points": [
            {"id": "KP1", "hit": True, "evidence": "考生提到响应时间"},
            {"id": "KP2", "hit": True, "evidence": "考生提到吞吐量"},
            {"id": "KP3", "hit": False},
            {"id": "KP4", "hit": False},
        ],
        "errors_hit": ["E1"],
    }
    assert validate_verdict(verdict, good_rubric) == []
    report = compute_report(good_rubric, verdict)
    weights = {kp["id"]: kp["weight"] for kp in good_rubric["key_points"]}
    expected = weights["KP1"] + weights["KP2"]
    assert abs(report["earned_points"] - expected) < 1e-6, report
    assert report["final_score"] == max(0.0, expected - good_rubric["common_errors"][0]["deduct"])
    assert 0 <= report["final_score"] <= report["max_score"]
    assert report["passed"] is (float(report["final_score"]) >= float(report["pass_score"]))

    missing_point = json.loads(json.dumps(verdict))
    missing_point["points"] = missing_point["points"][:2]
    try:
        validate_verdict(missing_point, good_rubric)
    except GradingError:
        pass
    else:
        raise AssertionError("expected GradingError for missing key points")
    print("selftest: all assertions passed")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic rubric grading for subjective questions")
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="validate a rubric file")
    p_validate.add_argument("rubric", type=Path)

    p_scaffold = sub.add_parser("scaffold", help="print a rubric template")
    p_scaffold.add_argument("--ref", required=True, help="question reference, e.g. case-2024-Q1")
    p_scaffold.add_argument("--subject", default="case", choices=SUBJECTS)
    p_scaffold.add_argument("--max", type=float, required=True, help="max score")
    p_scaffold.add_argument("--points", type=int, default=5, help="number of key points")

    p_grade = sub.add_parser("grade", help="grade a verdict against a rubric")
    p_grade.add_argument("--rubric", type=Path, required=True)
    p_grade.add_argument("--verdict", type=Path, required=True)
    p_grade.add_argument("--out", type=Path, help="write the report JSON here")
    p_grade.add_argument("--json", action="store_true", help="print machine-readable JSON instead of a table")

    sub.add_parser("selftest", help="run built-in assertions")

    args = parser.parse_args(argv)

    try:
        if args.command == "selftest":
            return selftest()
        if args.command == "validate":
            rubric = load_json(args.rubric)
            warnings = validate_rubric(rubric)
            for w in warnings:
                print(f"WARNING: {w}", file=sys.stderr)
            print(
                f"OK: {args.rubric} — {rubric['question_ref']} ({rubric['subject']}, "
                f"max {rubric['max_score']:g}, {len(rubric['key_points'])} key points)"
            )
            return 0
        if args.command == "scaffold":
            print(json.dumps(scaffold_rubric(args.ref, args.subject, args.max, args.points),
                             ensure_ascii=False, indent=2))
            return 0
        if args.command == "grade":
            rubric = load_json(args.rubric)
            validate_rubric(rubric)
            verdict = load_json(args.verdict)
            warnings = validate_verdict(verdict, rubric)
            report = compute_report(rubric, verdict)
            report["warnings"] = warnings
            if args.out:
                args.out.parent.mkdir(parents=True, exist_ok=True)
                args.out.write_text(
                    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
            if args.json:
                print(json.dumps(report, ensure_ascii=False, indent=2))
            else:
                print(f"{report['question_ref']}  ({report['subject']})")
                print("-" * 48)
                for row in report["points"]:
                    mark = "✓" if row["hit"] else "✗"
                    print(f"  {mark} {row['id']} [{row['weight']:g}分] {row['desc']}")
                    if row["hit"] and row["evidence"]:
                        print(f"      证据：{row['evidence']}")
                for row in report["errors_hit"]:
                    print(f"  − {row['id']} [-{row['deduct']:g}分] {row['desc']}")
                for t in report["typos"]:
                    print(f"  错别字：{t}")
                print("-" * 48)
                print(
                    f"得分：{report['final_score']:g} / {report['max_score']:g}"
                    f"（踩分 {report['earned_points']:g}，扣 {report['deductions']:g}）"
                    f"　{'通过' if report['passed'] else '未达线'}（{report['pass_score']:g} 分及格线）"
                )
                for w in warnings:
                    print(f"WARNING: {w}", file=sys.stderr)
            return 0
    except GradingError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    parser.error(f"unknown command {args.command!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
