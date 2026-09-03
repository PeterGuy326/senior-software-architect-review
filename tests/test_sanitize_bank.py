"""Tests for :mod:`scripts.sanitize_bank`.

These tests pin the answer-stripping contract that the pass-first coach
depends on: learners must never see ``✅`` markers, bold correct-option
wrappers, ``**答案**`` lines, or ``**解析**`` sections in the questions we
present. If any of those leaks back into ``options[].text`` or ``stem``,
we've regressed.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "sanitize_bank.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("sanitize_bank", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sanitize_bank = _load_module()


class SanitizeBankRealBankTests(unittest.TestCase):
    """Run the sanitizer against a real exam-bank file shipped with the repo."""

    def test_software_engineering_first_three_questions(self) -> None:
        target = REPO_ROOT / "exam-bank" / "07-software-engineering.md"
        self.assertTrue(target.exists(), "sample exam-bank file must exist")
        text = target.read_text(encoding="utf-8")
        blocks = sanitize_bank.split_blocks(text)
        for num in ("1", "4", "6"):
            with self.subTest(question=num):
                self.assertIn(num, blocks, f"question {num} missing from bank")
                item = sanitize_bank.parse_block(blocks[num])
                # Stem must be non-empty and free of any answer markers.
                self.assertTrue(item["stem"])
                self.assertNotIn("✅", item["stem"])
                self.assertNotIn("答案", item["stem"])
                self.assertNotIn("解析", item["stem"])
                # Exactly four options, labels A-D, no marker leakage.
                self.assertEqual(len(item["options"]), 4)
                labels = [opt["label"] for opt in item["options"]]
                self.assertEqual(labels, ["A", "B", "C", "D"])
                for opt in item["options"]:
                    self.assertNotIn("✅", opt["text"])
                    self.assertFalse(
                        opt["text"].startswith("**"),
                        f"option text leaks bold wrapper: {opt}",
                    )
                    self.assertFalse(
                        opt["text"].endswith("**"),
                        f"option text leaks bold wrapper: {opt}",
                    )
                # A correct answer must be detected exactly once.
                self.assertEqual(len(item["correct"]), 1)
                self.assertIn(item["correct"][0], set(labels))


class SanitizeBankSyntheticTests(unittest.TestCase):
    """Cover formatting variants that have burned us in real coaching sessions."""

    def test_inline_check_before_bold_wrapped_option(self) -> None:
        sample = (
            "### 1. Which is correct?\n\n"
            "A. wrong\n\n"
            "B. wrong\n\n"
            "C. wrong\n\n"
            "✅ **D. right answer**\n\n"
            "**答案**：D\n"
            "**解析**：because.\n---\n"
        )
        item = sanitize_bank.parse_block(sample)
        self.assertEqual(item["correct"], ["D"])
        self.assertEqual(len(item["options"]), 4)
        self.assertEqual(item["options"][3]["text"], "right answer")
        self.assertNotIn("答案", item["stem"])

    def test_bulleted_option_with_bold_marker(self) -> None:
        sample = (
            "### 2. RUP 顺序是：\n"
            "- A. 启动 → 构建 → 精化 → 移交\n"
            "- **B. 初始 → 精化 → 构建 → 移交**\n"
            "- C. 需求 → 设计 → 实现 → 测试\n"
            "- D. 计划 → 分析 → 部署 → 维护\n"
        )
        item = sanitize_bank.parse_block(sample)
        self.assertEqual(item["correct"], ["B"])
        self.assertEqual(
            [opt["text"] for opt in item["options"]],
            [
                "启动 → 构建 → 精化 → 移交",
                "初始 → 精化 → 构建 → 移交",
                "需求 → 设计 → 实现 → 测试",
                "计划 → 分析 → 部署 → 维护",
            ],
        )

    def test_explicit_answer_line_beats_marker(self) -> None:
        # Coach convention: an explicit **答案** always wins.
        sample = (
            "### 3. stem\n"
            "A. a\n"
            "✅ B. b\n"
            "C. c\n"
            "D. d\n"
            "**答案**: C\n"
            "**解析**: coach explanation.\n"
        )
        item = sanitize_bank.parse_block(sample)
        self.assertEqual(item["correct"], ["C"])
        self.assertEqual(item["explanation"], "coach explanation.")

    def test_full_width_colon_variants(self) -> None:
        # Real bank uses ``**答案**：`` with a full-width colon.
        sample = "### 4. stem\nA. a\nB. b\nC. c\nD. d\n**答案**：A\n**解析**：ok\n"
        item = sanitize_bank.parse_block(sample)
        self.assertEqual(item["correct"], ["A"])
        self.assertEqual(item["explanation"], "ok")


class SanitizeBankCliTests(unittest.TestCase):
    """The CLI path is what the coach actually invokes."""

    def test_cli_prints_missing_question_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sample = Path(tmp) / "bank.md"
            sample.write_text(
                "### 1. stem\nA. a\nB. b\nC. c\nD. d\n**答案**: A\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), str(sample), "1", "99"],
                capture_output=True,
                text=True,
                check=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(len(payload), 1)
            self.assertEqual(payload[0]["correct"], ["A"])
            self.assertIn("99", result.stderr)

    def test_cli_missing_file_errors(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "no-such-file.md", "1"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("file not found", result.stderr)


if __name__ == "__main__":
    unittest.main()
