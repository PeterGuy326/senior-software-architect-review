from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("grade", REPO_ROOT / "scripts" / "grade.py")
assert SPEC and SPEC.loader
grade = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(grade)


def make_rubric() -> dict:
    return {
        "schema_version": 1,
        "question_ref": "case-2024-Q1",
        "subject": "case",
        "max_score": 10,
        "key_points": [
            {"id": "KP1", "desc": "识别性能需求", "weight": 3, "aliases": ["响应时间", "吞吐"]},
            {"id": "KP2", "desc": "识别可用性需求", "weight": 3, "aliases": ["故障", "冗余"]},
            {"id": "KP3", "desc": "给出架构策略", "weight": 4, "aliases": ["缓存", "负载均衡"]},
        ],
        "common_errors": [
            {"id": "E1", "desc": "混淆可用性与性能", "deduct": 2},
        ],
        "pass_score": 6,
    }


def make_verdict() -> dict:
    return {
        "schema_version": 1,
        "question_ref": "case-2024-Q1",
        "points": [
            {"id": "KP1", "hit": True, "evidence": "考生提到响应时间 2 秒"},
            {"id": "KP2", "hit": True, "evidence": "考生提到双机热备"},
            {"id": "KP3", "hit": False},
        ],
        "errors_hit": ["E1"],
        "typos": ["枷锁→架构"],
        "comment": "总体结构清晰，策略部分薄弱",
    }


class RubricValidationTest(unittest.TestCase):
    def test_valid_rubric_passes(self) -> None:
        self.assertEqual(grade.validate_rubric(make_rubric()), [])

    def test_wrong_schema_version(self) -> None:
        rubric = make_rubric()
        rubric["schema_version"] = 2
        with self.assertRaises(grade.GradingError):
            grade.validate_rubric(rubric)

    def test_weight_sum_must_equal_max(self) -> None:
        rubric = make_rubric()
        rubric["max_score"] = 99
        with self.assertRaises(grade.GradingError):
            grade.validate_rubric(rubric)

    def test_empty_key_points_rejected(self) -> None:
        rubric = make_rubric()
        rubric["key_points"] = []
        with self.assertRaises(grade.GradingError):
            grade.validate_rubric(rubric)

    def test_negative_weight_rejected(self) -> None:
        rubric = make_rubric()
        rubric["key_points"][0]["weight"] = -1
        with self.assertRaises(grade.GradingError):
            grade.validate_rubric(rubric)

    def test_duplicate_key_point_id_rejected(self) -> None:
        rubric = make_rubric()
        rubric["key_points"][1]["id"] = "KP1"
        with self.assertRaises(grade.GradingError):
            grade.validate_rubric(rubric)

    def test_negative_deduction_rejected(self) -> None:
        rubric = make_rubric()
        rubric["common_errors"][0]["deduct"] = -3
        with self.assertRaises(grade.GradingError):
            grade.validate_rubric(rubric)

    def test_coarse_rubric_warns(self) -> None:
        rubric = make_rubric()
        rubric["key_points"] = rubric["key_points"][:1]
        rubric["max_score"] = 3
        del rubric["pass_score"]
        self.assertTrue(any("coarse" in w for w in grade.validate_rubric(rubric)))

    def test_scaffold_weights_sum_to_max(self) -> None:
        rubric = grade.scaffold_rubric("essay-x", "essay", 25, 5)
        self.assertEqual(grade.validate_rubric(rubric), [])


class VerdictValidationTest(unittest.TestCase):
    def test_valid_verdict_passes(self) -> None:
        self.assertEqual(grade.validate_verdict(make_verdict(), make_rubric()), [])

    def test_missing_key_point_rejected(self) -> None:
        verdict = make_verdict()
        verdict["points"] = verdict["points"][:2]
        with self.assertRaises(grade.GradingError):
            grade.validate_verdict(verdict, make_rubric())

    def test_unknown_key_point_rejected(self) -> None:
        verdict = make_verdict()
        verdict["points"].append({"id": "KP9", "hit": True})
        with self.assertRaises(grade.GradingError):
            grade.validate_verdict(verdict, make_rubric())

    def test_duplicate_key_point_rejected(self) -> None:
        verdict = make_verdict()
        verdict["points"].append(dict(verdict["points"][0]))
        with self.assertRaises(grade.GradingError):
            grade.validate_verdict(verdict, make_rubric())

    def test_hit_requires_boolean(self) -> None:
        verdict = make_verdict()
        verdict["points"][0]["hit"] = "yes"
        with self.assertRaises(grade.GradingError):
            grade.validate_verdict(verdict, make_rubric())

    def test_question_ref_must_match(self) -> None:
        verdict = make_verdict()
        verdict["question_ref"] = "case-2023-Q2"
        with self.assertRaises(grade.GradingError):
            grade.validate_verdict(verdict, make_rubric())

    def test_unknown_error_hit_rejected(self) -> None:
        verdict = make_verdict()
        verdict["errors_hit"] = ["E9"]
        with self.assertRaises(grade.GradingError):
            grade.validate_verdict(verdict, make_rubric())

    def test_hit_without_evidence_warns(self) -> None:
        verdict = make_verdict()
        verdict["points"][0]["evidence"] = ""
        warnings = grade.validate_verdict(verdict, make_rubric())
        self.assertTrue(any("evidence" in w for w in warnings))


class ScoreComputationTest(unittest.TestCase):
    def test_score_is_sum_of_hits_minus_deductions(self) -> None:
        report = grade.compute_report(make_rubric(), make_verdict())
        self.assertEqual(report["earned_points"], 6)
        self.assertEqual(report["deductions"], 2)
        self.assertEqual(report["final_score"], 4)
        self.assertFalse(report["passed"])

    def test_full_marks(self) -> None:
        verdict = make_verdict()
        verdict["points"][2]["hit"] = True
        verdict["points"][2]["evidence"] = "考生给出缓存+负载均衡策略"
        verdict["errors_hit"] = []
        report = grade.compute_report(make_rubric(), verdict)
        self.assertEqual(report["final_score"], 10)
        self.assertTrue(report["passed"])

    def test_score_clamped_at_zero(self) -> None:
        verdict = make_verdict()
        verdict["points"] = [{**p, "hit": False} for p in verdict["points"]]
        verdict["errors_hit"] = ["E1"]
        report = grade.compute_report(make_rubric(), verdict)
        self.assertEqual(report["final_score"], 0)

    def test_default_pass_line_is_sixty_percent(self) -> None:
        rubric = make_rubric()
        rubric["max_score"] = 10
        del rubric["pass_score"]
        grade.validate_rubric(rubric)
        verdict = make_verdict()
        verdict["points"] = [{**p, "hit": True} for p in verdict["points"]]
        verdict["errors_hit"] = []
        report = grade.compute_report(rubric, verdict)
        self.assertEqual(report["pass_score"], 6)

    def test_report_is_json_serializable(self) -> None:
        report = grade.compute_report(make_rubric(), make_verdict())
        json.dumps(report, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
