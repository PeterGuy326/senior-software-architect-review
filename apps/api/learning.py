"""Shared pure learning calculations for direct SQL and managed RPC storage."""
import copy
import sys
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from .db import ROOT

sys.path.insert(0, str(ROOT / 'scripts'))
import tutor


def choose_question(profile, state, curriculum, pool, last):
    ranked = tutor.recommend_payload(profile, state, curriculum,
        today=datetime.now(ZoneInfo('Asia/Shanghai')).date(),
        subject='comprehensive', limit=100)['recommendations']
    priorities = {r['topic_id']: i for i, r in enumerate(ranked)}
    return min(pool, key=lambda q: (q['item_id'] in last,
        priorities.get(q['topic_id'], 999), last.get(q['item_id'], ''), q['item_id']))


def public_question(issue_id, question):
    return {'issue_id': issue_id, 'question': {key: question[key] for key in
        ['item_id', 'stem', 'options', 'topic_name', 'source_type'] if key != 'item_id'} |
        {'id': question['item_id']}}


def evaluate(question, body, issue, previous_state, curriculum):
    correct = body.selected == question['correct'][0]
    now = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(timespec='seconds')
    event = {'attempt_id': uuid.uuid4().hex, 'event_type': 'practice',
        'topic_id': question['topic_id'], 'item_id': question['item_id'],
        'facet': question['facet'], 'at': now, 'subject': 'comprehensive',
        'skill': 'recognition', 'mode': 'practice', 'score': int(correct), 'max_score': 1,
        'duration_seconds': max(1, int(datetime.now().timestamp()) - issue['issued_at']),
        'confidence': body.confidence, 'wrong_reasons': [] if correct else ['knowledge_gap'],
        'source_type': question['source_type'], 'source': question['source_alias'], 'feedback_seen': False}
    tutor.validate_record_event(event, curriculum)
    state = copy.deepcopy(previous_state)
    result = tutor.apply_record_event(state, event, curriculum)
    tutor.validate_state(state)
    report = {'correct': correct, 'correct_answer': question['correct'][0],
        'explanation': question['explanation'] or '先记住这道题的核心概念。',
        'next_review_at': result['next_review_at'], 'topic_status': result['topic_status'],
        'message': '这一步完成了。' if correct else '抓住这个知识点，之后换个场景再练。'}
    return state, event, report
