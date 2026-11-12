"""Versioned public-note index. Never traverses learner data or question answers."""
import hashlib
import json
import math
import re
from collections import Counter

from .db import ROOT


def compile_knowledge():
    chunks = []
    for folder in ('cheatsheets', 'knowledge-index'):
        for path in sorted((ROOT / folder).glob('*.md')):
            if path.is_symlink():
                continue
            title = path.stem
            content = path.read_text(encoding='utf-8')
            for part in re.split(r'(?m)(?=^#{1,3} )', content):
                if not part.strip():
                    continue
                heading = part.splitlines()[0].lstrip('# ').strip()
                # Bounded chunks retain source attribution; no arbitrary filesystem tool.
                for offset in range(0, len(part), 1600):
                    body = part[offset:offset + 1600].strip()
                    if len(body) < 35:
                        continue
                    source = path.relative_to(ROOT).as_posix()
                    identifier = hashlib.sha256(f'{source}:{heading}:{offset}:{body}'.encode()).hexdigest()[:24]
                    chunks.append({'id':identifier,'source':source,'title':heading or title,'text':body})
    digest = hashlib.sha256(json.dumps(chunks,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:24]
    return 'architect-kb-' + digest, chunks


def terms(text):
    text = text.lower()
    return re.findall(r'[a-z0-9_]{2,}', text) + [text[i:i+2] for i in range(len(text)-1)
        if '\u4e00' <= text[i] <= '\u9fff' and '\u4e00' <= text[i+1] <= '\u9fff']


def search(chunks, query, limit=3):
    query_terms = set(terms(query[:2000])) - {'今天','怎么','什么','一个','可以','学习','只有','分钟','比较',
        '轻松','我们','你们','这个','一下','知道','开始','练习','帮我','想要','安排'}
    if not query_terms:
        return []
    counts = [Counter(terms(c['title'] + ' ' + c['text'])) for c in chunks]
    document_frequency = Counter(t for count in counts for t in count)
    scores = []
    for chunk, count in zip(chunks, counts):
        matches = query_terms.intersection(count)
        if len(matches)<2 and not any(re.fullmatch(r'[a-z0-9_]{2,}',t) for t in matches):
            continue
        score = sum(math.log(1 + len(chunks)/(1 + document_frequency[t])) *
                    count[t]/(count[t] + 1.2) for t in query_terms if count[t])
        if score:
            scores.append((score, chunk))
    return [c for _,c in sorted(scores,key=lambda item:(-item[0],item[1]['id']))[:limit]]
