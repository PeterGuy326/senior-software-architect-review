"""Exercise the real managed database with disposable synthetic identities only.

The web API executes in-process; this does NOT claim a deployed endpoint or real
WeChat login. Cleanup is restricted to the random users created in this run.
"""
import hashlib
import os
import secrets
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
from fastapi.testclient import TestClient

from apps.api.managed import ManagedStore, create_managed_app
from scripts.provision_managed import load_env
from scripts.publish_cloud_content import execute, literal


def run():
    load_env()
    env = os.environ['TCB_ENV_ID']
    if env != 'wuji-coach-dev-d4gtwqert85ce3eae':
        raise SystemExit('Smoke test restricted to the selected development environment')
    store, users = ManagedStore(), []
    try:
        with TestClient(create_managed_app(store)) as client:
            assert client.get('/healthz').status_code == 200
            assert len(client.get('/v1/exams').json()) == 1
            # A service-role key is never included in this unauthenticated probe.
            response = httpx.post(store.base, json={'p_action':'health'},timeout=15)
            assert response.status_code in (401,403,404), 'Anonymous RPC unexpectedly accessible'
            auth=[]
            for _ in range(2):
                user, token = uuid.uuid4().hex, secrets.token_urlsafe(32)
                users.append(user)
                store.call('login', {'identity':'disposable-smoke-'+user,'user_id':user,
                    'token_hash':hashlib.sha256(token.encode()).hexdigest()})
                auth.append({'Authorization':'Bearer '+token})
            goal = client.post('/v1/goals',headers=auth[0],json={})
            assert goal.status_code == 200
            url='/v1/goals/'+goal.json()['goal_id']
            with ThreadPoolExecutor(max_workers=4) as pool:
                issued=list(pool.map(lambda _:client.post(url+'/next',headers=auth[0]),range(4)))
            assert all(r.status_code == 200 for r in issued)
            assert len({r.json()['issue_id'] for r in issued}) == 1
            question=issued[0].json()
            assert set(question['question']) == {'id','stem','options','topic_name','source_type'}
            answer='/v1/issues/'+question['issue_id']+'/answer'
            with ThreadPoolExecutor(max_workers=4) as pool:
                results=list(pool.map(lambda _:client.post(answer,headers=auth[0],json={'selected':'A'}),range(4)))
            assert all(r.status_code == 200 for r in results)
            assert all(r.json() == results[0].json() for r in results)
            assert client.post(answer,headers=auth[0],json={'selected':'B'}).status_code == 409
            assert client.get(url+'/status',headers=auth[0]).json()['answered_count'] == 1
            assert client.get(url+'/status',headers=auth[1]).status_code == 404
            assert client.post('/v1/auth/local').status_code == 404
    finally:
        if users:
            ids=','.join(literal(user) for user in users)
            goals=f'SELECT id FROM coach.learning_goals WHERE user_id IN ({ids})'
            execute(env, f'''BEGIN;
                DELETE FROM coach.learning_attempts WHERE goal_id IN ({goals});
                DELETE FROM coach.question_issues WHERE goal_id IN ({goals});
                DELETE FROM coach.learning_goals WHERE user_id IN ({ids});
                DELETE FROM coach.sessions WHERE user_id IN ({ids});
                DELETE FROM coach.users WHERE id IN ({ids}); COMMIT;''')
        store.client.close()
    print('Real CloudBase RPC: health, practice, concurrent retries, user isolation and anonymous denial passed; synthetic records removed. API deployment and WeChat login are separate checks.')


if __name__ == '__main__':
    run()
