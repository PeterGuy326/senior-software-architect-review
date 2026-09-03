#!/usr/bin/env python3
"""Local-only exam terminal for the pass-first architecture coach.

The surrounding Agent remains the product entrypoint. This process only serves
the deterministic exam UI and writes trusted evidence to the learner's private
``.study/`` directory. It never calls a model or sends learner data off-device.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "tutor"))

import tutor  # noqa: E402
from mock_paper import PAPER_ID, private_items, public_payload  # noqa: E402

MAX_BODY_BYTES = 256 * 1024
SESSION_ID_RE = re.compile(rf"^web-{re.escape(PAPER_ID)}-[A-Za-z0-9-]{{8,80}}$")
QUESTION_NUMBERS = {str(number) for number in range(1, 76)}


class RequestError(ValueError):
    """A client error that is safe to return without a traceback."""


def json_response(handler: SimpleHTTPRequestHandler, data: Any, status: int = 200) -> None:
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("X-Content-Type-Options", "nosniff")
    handler.end_headers()
    handler.wfile.write(body)


def read_body(handler: SimpleHTTPRequestHandler) -> dict[str, Any]:
    raw_length = handler.headers.get("Content-Length", "0")
    try:
        length = int(raw_length)
    except ValueError as error:
        raise RequestError("Content-Length 无效") from error
    if length <= 0 or length > MAX_BODY_BYTES:
        raise RequestError("请求体必须存在且不得超过 256 KiB")
    raw = handler.rfile.read(length)
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RequestError("请求体不是有效 JSON") from error
    if not isinstance(payload, dict):
        raise RequestError("请求体必须是 JSON 对象")
    return payload


def validate_answers(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != QUESTION_NUMBERS:
        raise RequestError("答卷必须包含 1-75 的全部题号；未答题使用空字符串")
    allowed_by_number = {
        str(item["number"]): {option["key"] for option in item["question"]["options"]}
        for item in private_items()
    }
    answers: dict[str, str] = {}
    for number, answer in value.items():
        if not isinstance(answer, str) or (answer and answer not in allowed_by_number[number]):
            raise RequestError(f"第 {number} 题答案无效")
        answers[number] = answer
    return answers


def validate_session_id(value: Any) -> str:
    if not isinstance(value, str) or not SESSION_ID_RE.fullmatch(value):
        raise RequestError("模拟考试会话标识无效")
    return value


def public_curriculum() -> dict[str, Any]:
    """Return only the syllabus metadata needed by the local dashboard."""
    curriculum = tutor.load_curriculum()
    fields = (
        "id",
        "name",
        "subjects",
        "skills",
        "facets",
        "frequency_count",
        "frequency_confidence",
        "priority_weight",
        "quick_win",
        "cross_subject_value",
        "estimated_minutes",
        "strategy_rank",
    )
    return {
        "schema_version": curriculum.get("schema_version"),
        "topics": [
            {field: topic[field] for field in fields if field in topic}
            for topic in curriculum["topics"]
        ],
    }


def grade_mock(answers: dict[str, str]) -> tuple[list[dict[str, Any]], int]:
    """Grade on the local server; answers are absent from the pre-exam payload."""
    results: list[dict[str, Any]] = []
    score = 0
    for item in private_items():
        question = item["question"]
        selected = answers[str(item["number"])]
        correct = selected == question["answer"]
        score += int(correct)
        results.append(
            {
                "number": item["number"],
                "id": question["id"],
                "topic_id": item["topic_id"],
                "topic_name": question["topic_name"],
                "selected": selected,
                "correct_answer": question["answer"],
                "correct": correct,
                "explanation": question.get("explanation", ""),
            }
        )
    return results, score


def question_source(item: dict[str, Any]) -> tuple[str, str]:
    question = item["question"]
    source = f"exam-bank/{question['topic_file']}.md"
    question_number = int(question["id"].rsplit("-", 1)[1])
    return source, f"{source}#{question_number}"


def persist_events(
    data_dir: Path,
    practice_events: list[dict[str, Any]],
    mock_event: dict[str, Any],
) -> dict[str, Any]:
    """Atomically classify and append one browser mock submission."""
    curriculum = tutor.load_curriculum()
    data_dir.mkdir(parents=True, exist_ok=True)
    with tutor.data_lock(data_dir):
        profile, state = tutor.load_profile_and_state(data_dir)
        paths = tutor.state_paths(data_dir)
        logged = tutor.load_attempts(paths["attempts"])
        by_id = {event["attempt_id"]: event for event in logged}
        existing_practice = [event for event in practice_events if event["attempt_id"] in by_id]
        if existing_practice and len(existing_practice) != len(practice_events):
            raise tutor.TutorError("该场模考只保存了部分逐题事件，拒绝自动补写")

        if existing_practice:
            existing_modes = {by_id[event["attempt_id"]].get("mode") for event in existing_practice}
            if len(existing_modes) != 1 or existing_modes.pop() not in {"mock", "review"}:
                raise tutor.TutorError("该场模考的逐题模式不一致")
            session_mode = by_id[practice_events[0]["attempt_id"]]["mode"]
            include_mock = mock_event["attempt_id"] in by_id
            retest = session_mode == "review"
            if (session_mode == "mock") != include_mock:
                raise tutor.TutorError("该场模考的整卷事件与逐题模式不一致")
        else:
            paper_measured = any(
                event.get("event_type") == "mock" and event.get("item_id") == PAPER_ID
                for event in logged
            )
            session_mode = "review" if paper_measured else "mock"
            include_mock = not paper_measured
            retest = paper_measured

        for event in practice_events:
            event["mode"] = session_mode
            tutor.validate_record_event(event, curriculum)
        candidates = [*practice_events]
        if include_mock:
            tutor.validate_mock_event(mock_event)
            candidates.append(mock_event)

        new_events: list[dict[str, Any]] = []
        for event in candidates:
            old = by_id.get(event["attempt_id"])
            if old is not None:
                if tutor.events_conflict(old, event, compare_at=False):
                    raise tutor.TutorError(f"attempt-id {event['attempt_id']} 与已记录内容冲突")
                continue
            new_events.append(event)
        if not new_events:
            return {
                "already_recorded": True,
                "retest": retest,
                "status": tutor.status_payload(profile, state),
            }
        tutor.write_attempts(paths["attempts"], [*logged, *new_events])
        for event in new_events:
            tutor.apply_event_to_state(state, event, curriculum)
        tutor.save_state_bundle(data_dir, profile, state, backup=True)
        return {
            "already_recorded": False,
            "retest": retest,
            "status": tutor.status_payload(profile, state),
        }


def persist_postmortem(
    data_dir: Path,
    session_id: str,
    answers: dict[str, str],
    reasons: dict[str, list[str]],
) -> dict[str, Any]:
    """Append learner-supplied wrong reasons without rewriting raw answer evidence."""
    results, _ = grade_mock(answers)
    wrong_results = {str(item["number"]): item for item in results if not item["correct"]}
    if set(reasons) != set(wrong_results):
        raise RequestError("每道错题都必须且只能提交一个主要错因")
    items: list[dict[str, Any]] = []
    for number, result in wrong_results.items():
        values = reasons.get(number)
        if not isinstance(values, list) or len(values) != 1 or values[0] not in tutor.WRONG_REASONS:
            raise RequestError(f"第 {number} 题错因无效")
        items.append(
            {
                "number": int(number),
                "question_id": result["id"],
                "topic_id": result["topic_id"],
                "selected_answer": result["selected"],
                "correct_answer": result["correct_answer"],
                "wrong_reason": values[0],
            }
        )

    attempts_path = tutor.state_paths(data_dir)["attempts"]
    postmortem_path = data_dir / "postmortems.jsonl"
    feedback_id = f"{session_id}-postmortem"
    with tutor.data_lock(data_dir):
        attempts = tutor.load_attempts(attempts_path)
        trusted_prefix = f"{session_id}-q-"
        trusted_events = [
            event
            for event in attempts
            if event.get("event_type") == "practice"
            and str(event.get("attempt_id", "")).startswith(trusted_prefix)
        ]
        if len(trusted_events) != 75:
            raise RequestError("尚未找到该场模考的可信交卷记录")
        persisted_answers = {
            str(int(str(event["attempt_id"]).rsplit("-q-", 1)[1])): event.get("selected_answer", "")
            for event in trusted_events
        }
        if set(persisted_answers) != QUESTION_NUMBERS or persisted_answers != answers:
            raise RequestError("错因反馈中的答卷与该场可信交卷记录不一致")
        existing: list[dict[str, Any]] = []
        if postmortem_path.exists():
            for line_number, line in enumerate(postmortem_path.read_text(encoding="utf-8").splitlines(), 1):
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as error:
                    raise tutor.TutorError(f"postmortems.jsonl 第 {line_number} 行损坏，拒绝写入") from error
                existing.append(item)
        previous = next((item for item in existing if item.get("feedback_id") == feedback_id), None)
        event = {
            "schema_version": 1,
            "feedback_id": feedback_id,
            "mock_id": session_id,
            "paper_id": PAPER_ID,
            "at": tutor.now_iso(),
            "items": items,
        }
        if previous is not None:
            comparable_previous = dict(previous)
            comparable_previous["at"] = event["at"]
            if comparable_previous != event:
                raise RequestError("该场模考的错因反馈已存在且内容不同")
            return {"already_recorded": True, "feedback_id": feedback_id}
        content = "".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in [*existing, event])
        tutor.atomic_write_text(postmortem_path, content)
    return {"already_recorded": False, "feedback_id": feedback_id}


class ExamHandler(SimpleHTTPRequestHandler):
    """Serve the exam UI and a deliberately small, same-origin local API."""

    def __init__(self, *args: Any, data_dir: Path, **kwargs: Any) -> None:
        self.data_dir = data_dir
        super().__init__(*args, directory=str(REPO_ROOT / "tutor" / "app"), **kwargs)

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        super().end_headers()

    def _request_allowed(self, *, allow_document_navigation: bool = False) -> bool:
        port = self.server.server_port
        allowed_hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        host = self.headers.get("Host", "")
        if host not in allowed_hosts:
            return False
        if allow_document_navigation and self.headers.get("Sec-Fetch-Mode") == "navigate":
            return True
        origin = self.headers.get("Origin")
        if origin and origin not in {f"http://{value}" for value in allowed_hosts}:
            return False
        if self.headers.get("Sec-Fetch-Site") == "cross-site":
            return False
        return True

    def _guard(self, *, allow_document_navigation: bool = False) -> bool:
        if self._request_allowed(allow_document_navigation=allow_document_navigation):
            return True
        json_response(self, {"ok": False, "error": "仅允许当前本地考试页面访问"}, 403)
        return False

    def do_OPTIONS(self) -> None:
        if not self._guard():
            return
        self.send_response(204)
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if not self._guard(allow_document_navigation=path in {"/", "/index.html"}):
            return
        if path == "/api/status":
            self._handle_status()
        elif path == "/api/curriculum":
            self._handle_curriculum()
        elif path == "/api/mock-paper":
            self._handle_mock_paper()
        elif path in {"/questions.json", "/api/questions"}:
            json_response(self, {"ok": False, "error": "答案库不向考试浏览器开放"}, 404)
        elif path.startswith("/api/"):
            json_response(self, {"ok": False, "error": "not found"}, 404)
        else:
            super().do_GET()

    def do_POST(self) -> None:
        if not self._guard():
            return
        path = urlsplit(self.path).path
        try:
            if path == "/api/mock-grade":
                self._handle_mock_grade(read_body(self))
            elif path == "/api/mock-record":
                self._handle_mock_record(read_body(self))
            elif path == "/api/mock-feedback":
                self._handle_mock_feedback(read_body(self))
            else:
                json_response(self, {"ok": False, "error": "not found"}, 404)
        except RequestError as error:
            json_response(self, {"ok": False, "error": str(error)}, 400)
        except tutor.TutorError as error:
            json_response(self, {"ok": False, "error": str(error)}, 409)

    def _handle_status(self) -> None:
        try:
            profile, state = tutor.load_profile_and_state(self.data_dir)
            json_response(self, {"ok": True, "data": tutor.status_payload(profile, state)})
        except tutor.TutorError as error:
            json_response(self, {"ok": False, "error": str(error), "needs_init": True}, 409)

    def _handle_curriculum(self) -> None:
        try:
            json_response(self, {"ok": True, "data": public_curriculum()})
        except tutor.TutorError as error:
            json_response(self, {"ok": False, "error": str(error)}, 500)

    def _handle_mock_paper(self) -> None:
        try:
            json_response(self, {"ok": True, "data": public_payload()})
        except (OSError, ValueError, KeyError) as error:
            json_response(self, {"ok": False, "error": str(error)}, 500)

    def _handle_mock_grade(self, body: dict[str, Any]) -> None:
        answers = validate_answers(body.get("answers"))
        results, score = grade_mock(answers)
        json_response(self, {"ok": True, "data": {"score": score, "max_score": 75, "results": results}})

    def _handle_mock_record(self, body: dict[str, Any]) -> None:
        answers = validate_answers(body.get("answers"))
        session_id = validate_session_id(body.get("session_id"))
        duration_seconds = body.get("duration_seconds")
        if not isinstance(duration_seconds, int) or isinstance(duration_seconds, bool) or not 1 <= duration_seconds <= 150 * 60:
            raise RequestError("整卷用时必须是 1-9000 秒的整数")
        confidences = body.get("confidences", {})
        durations = body.get("durations", {})
        if not isinstance(confidences, dict) or not isinstance(durations, dict):
            raise RequestError("confidence 与 durations 必须是对象")
        results, score = grade_mock(answers)
        finished_at = tutor.now_iso()
        practice_events: list[dict[str, Any]] = []
        for result, item in zip(results, private_items()):
            key = str(result["number"])
            confidence = confidences.get(key, "sure")
            if confidence not in {"sure", "unsure", "guess"}:
                raise RequestError(f"第 {key} 题 confidence 无效")
            duration = durations.get(key)
            if duration is not None and (not isinstance(duration, int) or isinstance(duration, bool) or duration <= 0):
                raise RequestError(f"第 {key} 题用时无效")
            source, item_id = question_source(item)
            practice_events.append(
                {
                    "attempt_id": f"{session_id}-q-{result['number']:02d}",
                    "event_type": "practice",
                    "topic_id": item["topic_id"],
                    "item_id": item_id,
                    "facet": item["facet"],
                    "at": finished_at,
                    "subject": "comprehensive",
                    "skill": "recognition",
                    "mode": "mock",
                    "score": int(result["correct"]),
                    "max_score": 1,
                    "duration_seconds": duration,
                    "word_count": None,
                    "complete": False,
                    "confidence": confidence,
                    "wrong_reasons": ["guessed_correct"] if result["correct"] and confidence == "guess" else [],
                    "source_type": "simulation",
                    "source": source,
                    "feedback_seen": True,
                    "question_id": result["id"],
                    "selected_answer": result["selected"],
                    "correct_answer": result["correct_answer"],
                }
            )
        mock_event = {
            "attempt_id": session_id,
            "event_type": "mock",
            "topic_id": None,
            "item_id": PAPER_ID,
            "facet": None,
            "at": finished_at,
            "subject": "comprehensive",
            "skill": "recognition",
            "mode": "full_mock",
            "score": score,
            "max_score": 75,
            "duration_seconds": duration_seconds,
            "word_count": None,
            "complete": True,
            "confidence": "sure",
            "wrong_reasons": [],
            "source_type": "simulation",
            "source": PAPER_ID,
            "feedback_seen": True,
        }
        stored = persist_events(self.data_dir, practice_events, mock_event)
        json_response(
            self,
            {
                "ok": True,
                "data": {
                    "score": score,
                    "max_score": 75,
                    **stored,
                },
            },
        )

    def _handle_mock_feedback(self, body: dict[str, Any]) -> None:
        answers = validate_answers(body.get("answers"))
        session_id = validate_session_id(body.get("session_id"))
        reasons = body.get("wrong_reasons")
        if not isinstance(reasons, dict):
            raise RequestError("wrong_reasons 必须是对象")
        result = persist_postmortem(self.data_dir, session_id, answers, reasons)
        json_response(self, {"ok": True, "data": result})

    def log_message(self, format: str, *args: Any) -> None:
        if args and "/api/" in str(args[0]):
            return
        super().log_message(format, *args)


def main() -> None:
    parser = argparse.ArgumentParser(description="系统架构设计师 · 本地模拟考试终端")
    parser.add_argument("--port", type=int, default=8420, help="本地端口（默认 8420）")
    parser.add_argument("--data-dir", default=str(REPO_ROOT / ".study"), help="私人学习状态目录")
    args = parser.parse_args()
    data_dir = Path(args.data_dir).resolve()
    data_dir.mkdir(parents=True, exist_ok=True)

    def handler_factory(*handler_args: Any, **handler_kwargs: Any) -> ExamHandler:
        return ExamHandler(*handler_args, data_dir=data_dir, **handler_kwargs)

    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_factory)
    print(
        "\n系统架构设计师 · 本地模拟考试终端\n"
        f"地址：http://localhost:{args.port}\n"
        f"私人数据：{data_dir}\n"
        "本服务不调用模型、不接收 API Key、不访问外网。\n"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n考试服务已停止。")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
