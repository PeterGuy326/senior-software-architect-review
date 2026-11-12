"""Managed RPC integration against an explicitly disposable local PostgreSQL."""
import hashlib
import json
import os
import secrets
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import text

from apps.api import db
from apps.api.content import publish
from apps.api.managed import ManagedStore, create_managed_app


class LocalRpc(ManagedStore):
    def __init__(self, engine):
        self.engine,self.cache,self.lock=engine,{},threading.Lock()

    def call(self, action, payload=None, token=''):
        with self.engine.begin() as c:
            result=c.execute(text('SELECT public.coach_rpc(:a,CAST(:p AS jsonb),:t)'),
                {'a':action,'p':json.dumps(payload or {}),'t':token}).scalar_one()
        if result.get('error'):
            raise HTTPException({'unauthorized':401,'not_found':404,'conflict':409}.get(result['error'],422),result['error'])
        return result


@unittest.skipUnless('127.0.0.1:55439/' in os.getenv('TEST_DATABASE_URL',''), 'requires disposable local PostgreSQL')
class ManagedApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=db.make_engine(os.environ['TEST_DATABASE_URL'])
        db.migrate(cls.engine)
        cls.release,_=publish(cls.engine)
        with cls.engine.begin() as c:
            c.exec_driver_sql("DO $$ BEGIN CREATE ROLE anon NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$")
            c.exec_driver_sql("DO $$ BEGIN CREATE ROLE authenticated NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$")
            c.exec_driver_sql("DO $$ BEGIN CREATE ROLE service_role NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$")
            c.connection.driver_connection.cursor().execute((db.ROOT/'cloudbase/migrations/20261101220000_managed_rpc.sql').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.store=LocalRpc(self.engine)
        with patch.dict(os.environ,{'CONTENT_RELEASE_ID':self.release}):
            self.client=TestClient(create_managed_app(self.store))
        self.token=secrets.token_urlsafe(32)
        self.hash=hashlib.sha256(self.token.encode()).hexdigest()
        self.store.call('login',{'identity':uuid.uuid4().hex,'user_id':uuid.uuid4().hex,'token_hash':self.hash})
        self.auth={'Authorization':'Bearer '+self.token}
        res=self.client.post('/v1/goals',headers=self.auth,json={})
        self.assertEqual(res.status_code,200,res.text)
        self.goal=res.json()['goal_id']

    def tearDown(self):
        self.client.close()

    def test_full_practice_and_retry(self):
        url=f'/v1/goals/{self.goal}'
        q=self.client.post(url+'/next',headers=self.auth).json()
        self.assertEqual(set(q['question']),{'id','stem','options','topic_name','source_type'})
        answer=f"/v1/issues/{q['issue_id']}/answer"
        r=self.client.post(answer,headers=self.auth,json={'selected':'A'})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(self.client.post(answer,headers=self.auth,json={'selected':'A'}).json(),r.json())
        self.assertEqual(self.client.post(answer,headers=self.auth,json={'selected':'B'}).status_code,409)
        s=self.client.get(url+'/status',headers=self.auth)
        self.assertEqual(s.status_code,200,s.text)
        self.assertEqual(s.json()['answered_count'],1)
        self.assertIsNone(s.json()['subjects']['comprehensive']['predicted_score'])

    def test_concurrent_issue_and_submit(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            q=list(pool.map(lambda _:self.client.post(f'/v1/goals/{self.goal}/next',headers=self.auth).json(),range(4)))
        self.assertEqual(len({x['issue_id'] for x in q}),1)
        with ThreadPoolExecutor(max_workers=4) as pool:
            r=list(pool.map(lambda _:self.client.post(f"/v1/issues/{q[0]['issue_id']}/answer",headers=self.auth,json={'selected':'B'}),range(4)))
        self.assertEqual([x.status_code for x in r],[200]*4)
        self.assertEqual(self.client.get(f'/v1/goals/{self.goal}/status',headers=self.auth).json()['answered_count'],1)

    def test_isolation_and_no_cloud_local_login(self):
        other=secrets.token_urlsafe(32)
        self.store.call('login',{'identity':uuid.uuid4().hex,'user_id':uuid.uuid4().hex,'token_hash':hashlib.sha256(other.encode()).hexdigest()})
        self.assertEqual(self.client.get(f'/v1/goals/{self.goal}/status',headers={'Authorization':'Bearer '+other}).status_code,404)
        self.assertEqual(self.client.post('/v1/auth/local').status_code,404)
        self.assertEqual(self.client.post('/v1/goals',json={}).status_code,401)

    def test_rpc_not_executable_by_anon(self):
        with self.assertRaises(Exception):
            with self.engine.begin() as c:
                c.exec_driver_sql('SET LOCAL ROLE anon')
                c.exec_driver_sql("SELECT public.coach_rpc('health','{}','')")


if __name__=='__main__':
    unittest.main()
