"""Publish only the allowlisted public study notes and additive chat schema."""
import json
import os

from apps.api.db import ROOT
from apps.api.knowledge import compile_knowledge
from scripts.provision_managed import load_env, put_env
from scripts.publish_cloud_content import execute, literal


def main():
    load_env()
    env = os.environ['TCB_ENV_ID']
    if env != 'wuji-coach-dev-d4gtwqert85ce3eae':
        raise SystemExit('Only the selected development environment is supported')
    execute(env,(ROOT/'cloudbase/migrations/20261101234000_chat.sql').read_text())
    release,chunks = compile_knowledge()
    execute(env,f"INSERT INTO coach.knowledge_releases(id,exam_id) VALUES({literal(release)},'ruankao.senior.system_architect') ON CONFLICT DO NOTHING;")
    for start in range(0,len(chunks),12):
        rows = ','.join('('+','.join(literal(v) for v in [c['id'],release,json.dumps(c,ensure_ascii=False)])+')'
                        for c in chunks[start:start+12])
        execute(env,'INSERT INTO coach.knowledge_chunks(id,release_id,payload) VALUES '+rows+' ON CONFLICT DO NOTHING;')
    checked = execute(env,f'SELECT count(*) FROM coach.knowledge_chunks WHERE release_id={literal(release)};')
    if int(json.loads(checked['Rows'][0])[0]) != len(chunks):
        raise RuntimeError('Knowledge count mismatch')
    execute(env,f'UPDATE coach.knowledge_releases SET ready=true WHERE id={literal(release)};')
    put_env('KNOWLEDGE_RELEASE_ID',release)
    print(json.dumps({'knowledge_release':release,'public_chunks':len(chunks),'private_data_imported':False}))


if __name__ == '__main__':
    main()
