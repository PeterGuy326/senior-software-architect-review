"""Read-only verification of the selected development cloud content release."""
import json
import os

from apps.api.content import compile_pack
from scripts.publish_cloud_content import execute, literal


def run():
    from scripts.provision_managed import load_env
    load_env()
    env = os.environ['TCB_ENV_ID']
    release_id, pack = compile_pack()
    result = execute(env, "SELECT r.id, r.payload->>'publication_status', count(q.key) "
        'FROM coach.exam_releases r LEFT JOIN coach.questions q ON q.release_id=r.id '
        f'WHERE r.id={literal(release_id)} GROUP BY r.id;')
    row = json.loads(result['Rows'][0])
    assert row[:2] == [release_id, 'ready'] and int(row[2]) == len(pack['items']), 'Release validation failed'
    access = execute(env, "SELECT count(*) FROM pg_namespace n, LATERAL aclexplode(n.nspacl) a "
                          "WHERE n.nspname='coach' AND a.grantee=0;")
    assert int(json.loads(access['Rows'][0])[0]) == 0, 'Unexpected PUBLIC schema privilege'
    learners = execute(env, 'SELECT count(*) FROM coach.users;')
    print(json.dumps({'env_id':env,'release_id':row[0],'publication_status':row[1],
        'question_count':int(row[2]),'public_schema_access':False,
        'cloud_users':int(json.loads(learners['Rows'][0])[0]),
        'api_deployment_checked':False}, ensure_ascii=False))


if __name__ == '__main__':
    run()
