"""Compile the mapped, self-authored question subset into immutable releases."""
import hashlib
import json
import sys
import uuid

from sqlalchemy import insert, select

from .db import ROOT, make_engine, migrate, packs, questions, transaction

sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tutor'))
import sanitize_bank
import mock_paper

EXAM_ID = 'ruankao.senior.system_architect'


def compile_pack():
    manifest = json.loads((ROOT / 'exam_packs/ruankao-system-architect/manifest.json').read_text())
    curriculum = json.loads((ROOT / manifest['curriculum']).read_text())
    topic_index = {t['id']: t for t in curriculum['topics']}
    items, cache = [], {}
    for alias, topic_id, facet in mock_paper._ITEMS:
        # English items share a passage; defer them until passage rendering exists.
        if alias.startswith('23-english-reading-'):
            continue
        filename, number = alias.rsplit('-', 1)
        source = f'exam-bank/{filename}.md'
        if source not in cache:
            cache[source] = sanitize_bank.split_blocks((ROOT / source).read_text())
        item = sanitize_bank.parse_block(cache[source][str(int(number))])
        labels = [o['label'] for o in item['options']]
        if not item['stem'] or len(labels) != 4 or len(set(labels)) != 4:
            raise ValueError(f'Invalid choice question: {alias}')
        if len(item['correct']) != 1 or item['correct'][0] not in labels:
            raise ValueError(f'Invalid answer key: {alias}')
        if '✅' in item['stem'] or any('✅' in o['text'] for o in item['options']):
            raise ValueError(f'Unstripped answer marker: {alias}')
        if facet and facet not in topic_index[topic_id].get('facets', []):
            raise ValueError(f'Invalid facet: {alias}')
        item.update(item_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f'{EXAM_ID}/{alias}')),
                    source_alias=f'{source}#{int(number)}', topic_id=topic_id, facet=facet,
                    topic_name=topic_index[topic_id]['name'], source_type='self_authored')
        items.append(item)
    payload = {'manifest': manifest, 'curriculum': curriculum, 'items': items}
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    release_id = f'architect-{digest[:24]}'
    return release_id, payload


def publish(engine):
    release_id, payload = compile_pack()
    with transaction(engine) as connection:
        if connection.execute(select(packs.c.id).where(packs.c.id == release_id)).first():
            return release_id, len(payload['items'])
        connection.execute(insert(packs).values(id=release_id, exam_id=EXAM_ID,
                           payload={'manifest': payload['manifest'], 'curriculum': payload['curriculum'],
                                    'publication_status': 'ready'}))
        for item in payload['items']:
            connection.execute(insert(questions).values(key=f"{release_id}/{item['item_id']}",
                               release_id=release_id, item_id=item['item_id'], payload=item))
    return release_id, len(payload['items'])


if __name__ == '__main__':
    engine = make_engine()
    migrate(engine)
    release_id, count = publish(engine)
    print(json.dumps({'release_id': release_id, 'questions': count, 'private_data_imported': False}))
