from __future__ import annotations

import importlib.util
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("exam_server", REPO_ROOT / "scripts" / "serve.py")
assert SPEC and SPEC.loader
exam_server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exam_server)


class ExamServerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        created_at = exam_server.tutor.now_iso()
        profile = {
            "schema_version": 1,
            "exam_date": "2099-12-31",
            "daily_minutes": 60,
            "timezone": "Asia/Shanghai",
            "background": "",
            "known_strengths": [],
            "known_weaknesses": [],
            "created_at": created_at,
        }
        curriculum = exam_server.tutor.load_curriculum()
        paths = exam_server.tutor.state_paths(self.data_dir)
        exam_server.tutor.atomic_write_json(paths["profile"], profile)
        exam_server.tutor.atomic_write_text(paths["attempts"], "")
        exam_server.tutor.save_state_bundle(
            self.data_dir,
            profile,
            exam_server.tutor.new_state(curriculum, created_at),
            backup=True,
        )

        def handler_factory(*args, **kwargs):
            return exam_server.ExamHandler(*args, data_dir=self.data_dir, **kwargs)

        self.server = exam_server.ThreadingHTTPServer(("127.0.0.1", 0), handler_factory)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.origin = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temp_dir.cleanup()

    def request(self, path: str, *, payload=None, headers=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.origin + path,
            data=data,
            headers={"Content-Type": "application/json", **(headers or {})},
            method="POST" if payload is not None else "GET",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())

    def correct_answers(self):
        return {
            str(item["number"]): item["question"]["answer"]
            for item in exam_server.private_items()
        }

    def test_public_paper_withholds_answers_and_places_english_last(self) -> None:
        status, payload = self.request("/api/mock-paper")
        self.assertEqual(status, 200)
        paper = payload["data"]
        self.assertEqual(len(paper["items"]), 75)
        self.assertEqual((paper["passages"][0]["start"], paper["passages"][0]["end"]), (71, 75))
        serialized = json.dumps(paper, ensure_ascii=False)
        self.assertNotIn('"answer"', serialized)
        self.assertNotIn('"explanation"', serialized)

        with self.assertRaises(urllib.error.HTTPError) as denied:
            self.request("/questions.json")
        self.assertEqual(denied.exception.code, 404)

    def test_cross_site_origin_is_rejected(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as denied:
            self.request("/api/status", headers={"Origin": "https://evil.example"})
        self.assertEqual(denied.exception.code, 403)

        navigation = urllib.request.Request(
            self.origin + "/",
            headers={
                "Origin": "null",
                "Sec-Fetch-Site": "cross-site",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Dest": "document",
            },
        )
        with urllib.request.urlopen(navigation, timeout=3) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("本地模拟考试", response.read().decode("utf-8"))

    def test_submit_persists_once_and_same_paper_retest_is_not_a_new_mock(self) -> None:
        answers = self.correct_answers()
        common = {
            "answers": answers,
            "confidences": {},
            "durations": {},
            "duration_seconds": 9000,
        }
        first_id = f"web-{exam_server.PAPER_ID}-12345678"
        _, first = self.request("/api/mock-record", payload={"session_id": first_id, **common})
        self.assertFalse(first["data"]["retest"])
        self.assertEqual(first["data"]["score"], 75)

        _, replay = self.request("/api/mock-record", payload={"session_id": first_id, **common})
        self.assertFalse(replay["data"]["retest"])
        self.assertTrue(replay["data"]["already_recorded"])

        second_id = f"web-{exam_server.PAPER_ID}-abcdefgh"
        _, second = self.request("/api/mock-record", payload={"session_id": second_id, **common})
        self.assertTrue(second["data"]["retest"])

        attempts = exam_server.tutor.load_attempts(
            exam_server.tutor.state_paths(self.data_dir)["attempts"]
        )
        self.assertEqual(sum(event.get("event_type") == "mock" for event in attempts), 1)
        self.assertEqual(len(attempts), 151)
        first_question = next(event for event in attempts if event["attempt_id"].endswith("-q-01"))
        self.assertTrue(first_question["item_id"].startswith("exam-bank/"))
        self.assertEqual(first_question["selected_answer"], first_question["correct_answer"])

        _, feedback = self.request(
            "/api/mock-feedback",
            payload={"session_id": first_id, "answers": answers, "wrong_reasons": {}},
        )
        self.assertTrue(feedback["ok"])

        _, retest_feedback = self.request(
            "/api/mock-feedback",
            payload={"session_id": second_id, "answers": answers, "wrong_reasons": {}},
        )
        self.assertTrue(retest_feedback["ok"])
        self.assertTrue((self.data_dir / "postmortems.jsonl").is_file())

        tampered_answers = dict(answers)
        original = tampered_answers["1"]
        tampered_answers["1"] = next(key for key in "ABCD" if key != original)
        with self.assertRaises(urllib.error.HTTPError) as rejected:
            self.request(
                "/api/mock-feedback",
                payload={
                    "session_id": first_id,
                    "answers": tampered_answers,
                    "wrong_reasons": {"1": ["knowledge_gap"]},
                },
            )
        self.assertEqual(rejected.exception.code, 400)

    def test_concurrent_first_submissions_create_one_full_mock(self) -> None:
        common = {
            "answers": self.correct_answers(),
            "confidences": {},
            "durations": {},
            "duration_seconds": 9000,
        }
        payloads = [
            {"session_id": f"web-{exam_server.PAPER_ID}-concurrent{i}", **common}
            for i in (1, 2)
        ]
        with ThreadPoolExecutor(max_workers=2) as executor:
            responses = list(
                executor.map(lambda payload: self.request("/api/mock-record", payload=payload), payloads)
            )

        self.assertEqual(sorted(response[1]["data"]["retest"] for response in responses), [False, True])
        attempts = exam_server.tutor.load_attempts(
            exam_server.tutor.state_paths(self.data_dir)["attempts"]
        )
        self.assertEqual(sum(event.get("event_type") == "mock" for event in attempts), 1)
        self.assertEqual(len(attempts), 151)


if __name__ == "__main__":
    unittest.main()
