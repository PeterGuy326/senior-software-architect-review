"""Local disposable PostgreSQL smoke test. Never use against a production DB."""
import os
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from apps.api.db import make_engine
from apps.api.main import create_app


def main():
    url = os.environ.get('TEST_DATABASE_URL', '')
    if not url or '127.0.0.1:55432/' not in url:
        raise SystemExit('Only the dedicated local check database on port 55432 is accepted')
    engine = make_engine(url)
    with TestClient(create_app(engine, 'local')) as client:
        auth = {'Authorization':'Bearer ' + client.post('/v1/auth/local').json()['token']}
        goal = client.post('/v1/goals',headers=auth,json={}).json()['goal_id']
        item = client.post(f'/v1/goals/{goal}/next',headers=auth).json()
        def submit(_):
            return client.post(f"/v1/issues/{item['issue_id']}/answer",headers=auth,json={'selected':'A'})
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(submit,range(4)))
        assert all(r.status_code == 200 for r in results), [r.status_code for r in results]
        assert client.get(f'/v1/goals/{goal}/status',headers=auth).json()['answered_count'] == 1
        with TestClient(create_app(engine, 'local')) as restarted:
            assert restarted.get(f'/v1/goals/{goal}/status',headers=auth).json()['answered_count'] == 1
        print('PostgreSQL: authenticated practice, concurrent retry and restart persistence passed.')
    engine.dispose()


if __name__ == '__main__':
    main()
