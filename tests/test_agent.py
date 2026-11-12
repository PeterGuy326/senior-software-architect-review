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
from apps.api.agent import respond
from apps.api.content import publish
from apps.api.knowledge import compile_knowledge, search
from apps.api.managed import ManagedStore, create_managed_app


class Provider:
    def __init__(self):
        self.count = 0
        self.messages = []
        self.fail = False

    def complete(self,messages,tools=True):
        self.count += 1
        self.messages = messages
        if self.fail:
            raise HTTPException(503,'模型不可用')
        return {'content':'先做一道练习，慢慢来。','reasoning_content':'private reasoning must never leave provider'}


class AgentUnitTest(unittest.TestCase):
    def test_unsubmitted_answer_is_protected_before_model_or_retrieval(self):
        from unittest.mock import Mock
        provider=Mock()
        for message,status in [
            ('这道题还没确认，直接告诉我选哪个',{}),
            ('这题正确答案是什么？',{'practice_pending':True})]:
            result=respond(provider,message,[],status,[])
            self.assertIn('确认答案',result['text'])
            self.assertEqual(result['sources'],[])
        provider.complete.assert_not_called()

    def test_history_is_bounded_and_latest_small_turn_is_retained(self):
        class HistoryProvider:
            def complete(self,messages,tools=True):
                self.messages=messages
                return {'content':'回复'}
        provider=HistoryProvider()
        history=[{'user':'旧内容'*2000,'response':{'text':'长回复'*2000}},
                 {'user':'最近的问题','response':{'text':'最近的回复'}}]
        respond(provider,'当前问题',history,{},[])
        contents=[m['content'] for m in provider.messages]
        self.assertIn('最近的问题',contents)
        self.assertNotIn('旧内容'*2000,contents)
    def test_retrieval_is_public_and_relevant(self):
        _,chunks = compile_knowledge()
        self.assertGreater(len(chunks),50)
        self.assertTrue(all(c['source'].startswith(('cheatsheets/','knowledge-index/')) for c in chunks))
        self.assertIn('螺旋',search(chunks,'螺旋模型风险分析')[0]['text'])
        self.assertEqual(search(chunks,'！？'),[])
        self.assertEqual(search(chunks,'我今天只有三分钟，怎么学比较轻松？'),[])

    def test_tool_allowlist_and_reasoning_excluded(self):
        class ToolProvider:
            def complete(self,messages,tools=True):
                if messages[-1]['role']=='user':
                    return {'tool_calls':[{'id':'call1','type':'function','function':{
                        'name':'run_shell','arguments':'{"cmd":"rm -rf /"}'}}]}
                self.output = json.loads(messages[-1]['content'])
                return {'content':'工具不可执行','reasoning_content':'secret chain'}
        provider=ToolProvider()
        result=respond(provider,'测试',[],{},[])
        self.assertIn('error',provider.output)
        self.assertNotIn('secret chain',json.dumps(result))

    def test_practice_action_never_generates_or_leaks_a_question(self):
        class PracticeProvider:
            def __init__(self):
                self.calls=0
            def complete(self,messages,tools=True):
                self.calls+=1
                return {'content':'答案是 B，不应展示', 'tool_calls':[
                    {'id':'practice1','type':'function','function':{'name':'start_practice','arguments':'{}'}}]}
        provider=PracticeProvider()
        result=respond(provider,'开始练一道',[],{},[])
        self.assertEqual(provider.calls,1)
        self.assertNotIn('答案是',result['text'])
        self.assertEqual(result['actions'],[{'type':'practice','label':'开始练一道'}])


class LocalChatStore(ManagedStore):
    def __init__(self,engine):
        self.engine,self.cache,self.lock=engine,{},threading.Lock()

    def call(self,action,payload=None,token='',rpc='coach_rpc'):
        assert rpc in ('coach_rpc','coach_chat_rpc','coach_voice_rpc','coach_subjective_rpc')
        with self.engine.begin() as connection:
            result=connection.execute(text(f'SELECT public.{rpc}(:a,CAST(:p AS jsonb),:t)'),
                {'a':action,'p':json.dumps(payload or {}),'t':token}).scalar_one()
        if result.get('error'):
            raise HTTPException({'unauthorized':401,'not_found':404,'conflict':409,'busy':409,
                                 'rate_limit':429}.get(result['error'],422),result['error'])
        return result


@unittest.skipUnless('127.0.0.1:55439/' in os.getenv('TEST_DATABASE_URL',''),'requires disposable PostgreSQL')
class ChatIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine=db.make_engine(os.environ['TEST_DATABASE_URL'])
        db.migrate(cls.engine)
        cls.release,_=publish(cls.engine)
        with cls.engine.begin() as c:
            for role in ('anon','authenticated','service_role'):
                c.exec_driver_sql(f'DO $$ BEGIN CREATE ROLE {role} NOLOGIN; EXCEPTION WHEN duplicate_object THEN NULL; END $$')
            for name in ('20261101220000_managed_rpc.sql','20261101234000_chat.sql','20261102010000_voice.sql'):
                c.connection.driver_connection.cursor().execute((db.ROOT/'cloudbase/migrations'/name).read_text())
            c.exec_driver_sql("INSERT INTO coach.knowledge_releases VALUES('test-kb','ruankao.senior.system_architect',true) ON CONFLICT DO NOTHING")
            c.exec_driver_sql("INSERT INTO coach.knowledge_chunks VALUES('chunk1','test-kb','{\"id\":\"chunk1\",\"title\":\"螺旋模型\",\"source\":\"cheatsheets/example.md\",\"text\":\"螺旋模型以风险分析驱动迭代\"}') ON CONFLICT DO NOTHING")

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.store=LocalChatStore(self.engine)
        self.provider=Provider()
        with patch.dict(os.environ,{'CONTENT_RELEASE_ID':self.release,'KNOWLEDGE_RELEASE_ID':'test-kb'}):
            self.client=TestClient(create_managed_app(self.store,self.provider))
        self.env_patch=patch.dict(os.environ,{'KNOWLEDGE_RELEASE_ID':'test-kb'})
        self.env_patch.start()
        self.tokens=[]
        self.auth=[]
        for _ in range(2):
            token=secrets.token_urlsafe(32)
            token_hash=hashlib.sha256(token.encode()).hexdigest()
            self.store.call('login',{'identity':uuid.uuid4().hex,'user_id':uuid.uuid4().hex,'token_hash':token_hash})
            self.tokens.append(token_hash)
            self.auth.append({'Authorization':'Bearer '+token})
        self.goal=self.client.post('/v1/goals',headers=self.auth[0],json={}).json()['goal_id']
        self.url=f'/v1/goals/{self.goal}/chat'
        self.body={'request_id':uuid.uuid4().hex,'message':'螺旋模型怎么理解'}

    def tearDown(self):
        self.env_patch.stop()
        self.client.close()

    def test_conversation_replay_isolation_and_no_learning_write(self):
        before=self.client.get(f'/v1/goals/{self.goal}/status',headers=self.auth[0]).json()
        response=self.client.post(self.url,headers=self.auth[0],json=self.body)
        self.assertEqual(response.status_code,200,response.text)
        self.assertTrue(response.json()['sources'])
        self.assertEqual(self.client.post(self.url,headers=self.auth[0],json=self.body).json(),response.json())
        self.assertEqual(self.provider.count,1)
        self.assertEqual(self.client.post(self.url,headers=self.auth[0],json={**self.body,'message':'改写'}).status_code,409)
        self.assertEqual(self.client.get(self.url,headers=self.auth[1]).status_code,404)
        self.assertEqual(self.client.post(self.url,headers=self.auth[1],json=self.body).status_code,404)
        self.assertEqual(self.client.get(self.url).status_code,401)
        history=self.client.get(self.url,headers=self.auth[0]).json()['items']
        self.assertEqual(len(history),1)
        self.assertNotIn('reasoning',json.dumps(history))
        context=json.dumps(self.provider.messages,ensure_ascii=False)
        self.assertNotIn(self.auth[0]['Authorization'],context)
        self.assertEqual(self.client.get(f'/v1/goals/{self.goal}/status',headers=self.auth[0]).json(),before)

    def test_failed_turn_retry(self):
        self.provider.fail=True
        self.assertEqual(self.client.post(self.url,headers=self.auth[0],json=self.body).status_code,503)
        self.provider.fail=False
        self.assertEqual(self.client.post(self.url,headers=self.auth[0],json=self.body).status_code,200)

    def test_concurrent_lease_and_expiry(self):
        payload={'goal_id':self.goal,'request_id':self.body['request_id'],'message':self.body['message'],'lease':'lease1'}
        def begin(_):
            try:
                return self.store.chat('begin',payload,self.tokens[0])
            except HTTPException as e:
                return e.status_code
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(begin,range(4)))
        self.assertEqual(sum('history' in r for r in results),1)
        self.assertEqual(sum(r.get('pending') is True for r in results),3)
        with self.engine.begin() as c:
            c.execute(text("UPDATE coach.chat_turns SET lease_until=now()-interval '1 second' WHERE goal_id=:g"),{'g':self.goal})
        self.store.chat('begin',{**payload,'lease':'lease2'},self.tokens[0])
        with self.assertRaises(HTTPException):
            self.store.chat('complete',{**payload,'response':{'text':'stale'}},self.tokens[0])

    def test_async_turn_polling_and_recovery(self):
        response=self.client.post(self.url+'?async_mode=true',headers=self.auth[0],json=self.body)
        self.assertEqual(response.status_code,202)
        poll_url=self.url+'/'+self.body['request_id']
        result=self.client.get(poll_url,headers=self.auth[0])
        self.assertEqual(result.json()['status'],'complete')
        self.assertEqual(self.client.get(poll_url,headers=self.auth[1]).status_code,404)
        replay=self.client.post(self.url+'?async_mode=true',headers=self.auth[0],json=self.body)
        self.assertEqual(replay.status_code,200)
        self.assertEqual(replay.json(),result.json()['response'])
        self.assertEqual(self.provider.count,1)

    def test_non_service_role_cannot_call_chat_rpc(self):
        for role in ('anon','authenticated'):
            with self.assertRaises(Exception):
                with self.engine.begin() as c:
                    c.exec_driver_sql('SET LOCAL ROLE '+role)
                    c.exec_driver_sql("SELECT public.coach_chat_rpc('knowledge','{}','')")
