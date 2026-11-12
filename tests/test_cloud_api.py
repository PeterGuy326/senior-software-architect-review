"""Critical API boundaries, using synthetic users and isolated databases."""
import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api import db
from apps.api.content import compile_pack, publish
from apps.api.main import create_app


class CloudApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.engine = db.make_engine('sqlite:///' + str(Path(self.temp.name) / 'test.db'))
        self.client = TestClient(create_app(self.engine, 'local'))
        self.client.__enter__()
        self.auth = {'Authorization': 'Bearer ' + self.client.post('/v1/auth/local').json()['token']}
        self.goal = self.client.post('/v1/goals',json={},headers=self.auth).json()['goal_id']

    def tearDown(self):
        self.client.__exit__(None,None,None)
        self.engine.dispose()
        self.temp.cleanup()

    def next(self):
        return self.client.post(f'/v1/goals/{self.goal}/next',headers=self.auth).json()

    def test_no_answer_leaks_or_client_score(self):
        item = self.next()
        self.assertEqual(set(item['question']), {'id','stem','options','topic_name','source_type'})
        self.assertNotIn('✅',str(item))
        rejected = self.client.post(f"/v1/issues/{item['issue_id']}/answer",headers=self.auth,
            json={'selected':'A','score':1})
        self.assertEqual(rejected.status_code,422)
        self.assertEqual(self.next()['issue_id'],item['issue_id'])

    def test_isolation_and_cannot_rewrite(self):
        item = self.next()
        other = {'Authorization':'Bearer ' + self.client.post('/v1/auth/local').json()['token']}
        self.assertEqual(self.client.get(f'/v1/goals/{self.goal}/status',headers=other).status_code,404)
        self.assertEqual(self.client.post(f"/v1/issues/{item['issue_id']}/answer",headers=other,json={'selected':'A'}).status_code,404)
        url = f"/v1/issues/{item['issue_id']}/answer"
        a = self.client.post(url,headers=self.auth,json={'selected':'A'})
        self.assertEqual(a.status_code,200,a.text)
        self.assertEqual(a.json(),self.client.post(url,headers=self.auth,json={'selected':'A'}).json())
        self.assertEqual(self.client.post(url,headers=self.auth,json={'selected':'B'}).status_code,409)
        self.assertEqual(self.client.get(f'/v1/goals/{self.goal}/status',headers=self.auth).json()['answered_count'],1)

    def test_concurrent_retry_records_once(self):
        item = self.next()
        def answer(_):
            return self.client.post(f"/v1/issues/{item['issue_id']}/answer",headers=self.auth,json={'selected':'B'}).status_code
        with ThreadPoolExecutor(max_workers=4) as executor:
            self.assertEqual(list(executor.map(answer,range(4))),[200]*4)
        status = self.client.get(f'/v1/goals/{self.goal}/status',headers=self.auth).json()
        self.assertEqual(status['answered_count'],1)
        self.assertIsNone(status['subjects']['comprehensive']['predicted_score'])
        self.assertNotEqual(self.next()['question']['id'],item['question']['id'])

    def test_release_immutable_and_no_import_of_private_material(self):
        release,count = publish(self.engine)
        self.assertEqual(count,70)
        with self.engine.connect() as c:
            self.assertEqual(len(c.execute(select(db.questions)).all()),70)
        _,pack = compile_pack()
        self.assertTrue(all(i['source_alias'].startswith('exam-bank/') for i in pack['items']))
        self.assertTrue(all(i['source_type']=='self_authored' for i in pack['items']))

    def test_cloud_requires_credentials_and_postgres(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(RuntimeError,'Missing deployment'):
                create_app(self.engine,'development')

    def test_wechat_does_not_accept_identity_from_client(self):
        self.assertEqual(self.client.post('/v1/auth/wechat',json={'code':'x','openid':'forged'}).status_code,422)
        with patch.dict(os.environ,{'WECHAT_APP_ID':'wx-test','WECHAT_APP_SECRET':'secret'}):
            with patch('apps.api.main.httpx.get') as exchange:
                exchange.return_value.json.return_value={'errcode':40029}
                self.assertEqual(self.client.post('/v1/auth/wechat',json={'code':'bad'}).status_code,401)


if __name__ == '__main__':
    unittest.main()
