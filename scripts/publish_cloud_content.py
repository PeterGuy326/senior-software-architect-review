"""Publish authored content through the authorized CloudBase CLI, no DB password.

Only operates on the project's coach schema. Never reads learner records.
The shared trial instance does not expose a PostgreSQL protocol endpoint.
"""
import json
import os
import subprocess
from pathlib import Path

from sqlalchemy import MetaData
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from apps.api.content import compile_pack
from apps.api.db import ROOT, metadata


def execute(env, sql):
    process = subprocess.run([
        str(ROOT / 'node_modules/.bin/tcb'), 'db', 'execute', '-e', env,
        '--sql', sql, '--json'], cwd=ROOT, text=True, capture_output=True)
    if process.returncode:
        # The caller's SQL includes answer keys. Do not dump commands or raw errors.
        try:
            code = json.loads(process.stdout).get('error', {}).get('code', 'unknown')
        except ValueError:
            code = 'unknown'
        raise RuntimeError('Cloud SQL operation failed (' + code + '); no SQL or credentials printed')
    result = json.loads(process.stdout)
    if result.get('error'):
        raise RuntimeError('Cloud SQL reported an error; publication not activated')
    return result['data']


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def run():
    env = os.getenv('TCB_ENV_ID')
    if not env:
        raise SystemExit('Set TCB_ENV_ID to the explicitly selected development environment')
    if env != 'wuji-coach-dev-d4gtwqert85ce3eae':
        raise SystemExit('This initial publisher is restricted to the selected development environment')
    release_id, pack = compile_pack()
    copied = MetaData(schema='coach')
    for table in metadata.sorted_tables:
        table.to_metadata(copied, schema='coach')
    statements = ['CREATE SCHEMA IF NOT EXISTS coach', 'REVOKE ALL ON SCHEMA coach FROM PUBLIC']
    for table in copied.sorted_tables:
        statements.append(str(CreateTable(table, if_not_exists=True).compile(dialect=postgresql.dialect())))
    execute(env, ';\n'.join(statements) + ';')
    published = {k:pack[k] for k in ['manifest','curriculum']}
    published['publication_status'] = 'draft'
    execute(env, 'INSERT INTO coach.exam_releases (id,exam_id,payload) VALUES (' +
        ','.join([literal(release_id),literal(pack['manifest']['id']),literal(json.dumps(published,ensure_ascii=False))]) +
        ') ON CONFLICT (id) DO NOTHING;')
    for start in range(0,len(pack['items']),10):
        values = []
        for q in pack['items'][start:start+10]:
            values.append('(' + ','.join(literal(x) for x in [release_id+'/'+q['item_id'],release_id,
                q['item_id'],json.dumps(q,ensure_ascii=False)]) + ')')
        execute(env, 'INSERT INTO coach.questions (key,release_id,item_id,payload) VALUES ' +
                ','.join(values) + ' ON CONFLICT (key) DO NOTHING;')
        print(f'Content uploaded: {min(start+10,len(pack["items"]))}/{len(pack["items"])}')
    count = execute(env, f'SELECT count(*) FROM coach.questions WHERE release_id={literal(release_id)};')
    rows = count.get('Rows',[])
    if not rows or int(json.loads(rows[0])[0]) != len(pack['items']):
        raise RuntimeError('Question count mismatch; release remains unpublished')
    published['publication_status'] = 'ready'
    execute(env, f'UPDATE coach.exam_releases SET payload={literal(json.dumps(published,ensure_ascii=False))}'
                f' WHERE id={literal(release_id)};')
    print(json.dumps({'env_id':env,'release_id':release_id,'questions':len(pack['items']),
                      'publication_status':'ready','learner_data_imported':False},ensure_ascii=False))


if __name__ == '__main__':
    run()
