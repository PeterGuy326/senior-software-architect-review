import base64
import io
import json
import os
import secrets
import hashlib
import unittest
import uuid
import wave
from unittest.mock import patch

import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import text

from apps.api.contracts import VoiceInput
from apps.api.speech import ASR_MODEL, SpeechProvider, decode_audio
from apps.api.managed import create_managed_app
import tests.test_agent as helpers


def audio_body(seconds=1):
    buffer=io.BytesIO()
    with wave.open(buffer,'wb') as output:
        output.setparams((1,2,16000,0,'NONE','not compressed'))
        output.writeframes(b'\0\0'*int(16000*seconds))
    return {'request_id':uuid.uuid4().hex,'format':'wav','audio_base64':base64.b64encode(buffer.getvalue()).decode()}


class SpeechUnitTest(unittest.TestCase):
    def test_audio_validation_and_duration(self):
        raw,digest,duration=decode_audio(VoiceInput(**audio_body()))
        self.assertEqual(duration,1)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
        for body in [audio_body(.1),{**audio_body(),'audio_base64':'x'*100},
                     {**audio_body(),'format':'mp3'}]:
            with self.assertRaises(HTTPException):
                decode_audio(VoiceInput(**body))
        with self.assertRaises(HTTPException):
            decode_audio(VoiceInput.model_construct(**audio_body(20)))

    def test_fixed_free_asr_provider_and_no_secret_errors(self):
        response=httpx.Response(200,json={'text':'<|zh|><|NEUTRAL|>今天练一道题'},request=httpx.Request('POST','https://example.invalid'))
        with patch.dict(os.environ,{'MODEL_PROVIDER':'siliconflow','MODEL_API_KEY':'synthetic-secret','ASR_API_KEY':''}):
            with patch('apps.api.speech.httpx.post',return_value=response) as post:
                self.assertEqual(SpeechProvider().transcribe(b'bytes','wav'),'今天练一道题')
                self.assertEqual(post.call_args.kwargs['data'],{'model':ASR_MODEL})
                self.assertEqual(post.call_args.args[0],'https://api.siliconflow.cn/v1/audio/transcriptions')
            with patch('apps.api.speech.httpx.post',side_effect=httpx.ConnectError('synthetic-secret')):
                with self.assertRaises(HTTPException) as error:
                    SpeechProvider().transcribe(b'bytes','wav')
                self.assertNotIn('synthetic-secret',str(error.exception))
        with patch.dict(os.environ,{'MODEL_PROVIDER':'bigmodel','MODEL_API_KEY':'other-provider-key','ASR_API_KEY':''}):
            self.assertEqual(SpeechProvider().key,'')


@unittest.skipUnless('127.0.0.1:55439/' in os.getenv('TEST_DATABASE_URL',''),'requires disposable PostgreSQL')
class VoiceIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        helpers.ChatIntegrationTest.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        self.store=helpers.LocalChatStore(self.engine)
        class FakeSpeech:
            calls=0
            fail=False
            def transcribe(self,audio,format):
                self.calls+=1
                if self.fail:
                    raise HTTPException(503,'busy')
                return '今天只练一道题'
        self.speech=FakeSpeech()
        with patch.dict(os.environ,{'CONTENT_RELEASE_ID':self.release}):
            self.client=TestClient(create_managed_app(self.store,helpers.Provider(),self.speech))
        self.auth=[]
        for _ in range(2):
            token=secrets.token_urlsafe(32)
            self.store.call('login',{'identity':uuid.uuid4().hex,'user_id':uuid.uuid4().hex,'token_hash':hashlib.sha256(token.encode()).hexdigest()})
            self.auth.append({'Authorization':'Bearer '+token})
        self.goal=self.client.post('/v1/goals',headers=self.auth[0],json={}).json()['goal_id']
        self.url=f'/v1/goals/{self.goal}/voice'

    def tearDown(self):
        self.client.close()

    def test_transcript_is_owned_idempotent_and_does_not_send_chat_or_grade(self):
        body=audio_body()
        response=self.client.post(self.url,headers=self.auth[0],json=body)
        self.assertEqual(response.status_code,202,response.text)
        result_url=self.url+'/'+body['request_id']
        self.assertEqual(self.client.get(result_url,headers=self.auth[0]).json(),{'status':'complete','text':'今天只练一道题'})
        self.assertEqual(self.client.post(self.url,headers=self.auth[0],json=body).json()['text'],'今天只练一道题')
        self.assertEqual(self.speech.calls,1)
        self.assertEqual(self.client.get(result_url,headers=self.auth[1]).status_code,404)
        self.assertEqual(self.client.post(self.url,headers=self.auth[1],json=body).status_code,404)
        self.assertEqual(self.client.get(result_url).status_code,401)
        self.assertEqual(self.client.post(self.url,headers=self.auth[0],json={**audio_body(2),'request_id':body['request_id']}).status_code,409)
        self.assertEqual(self.client.get(f'/v1/goals/{self.goal}/chat',headers=self.auth[0]).json()['items'],[])
        self.assertEqual(self.client.get(f'/v1/goals/{self.goal}/status',headers=self.auth[0]).json()['answered_count'],0)
        with self.engine.begin() as connection:
            stored=connection.execute(text('SELECT to_jsonb(v) FROM coach.voice_jobs v WHERE goal_id=:g'),{'g':self.goal}).scalar_one()
            self.assertNotIn(body['audio_base64'],json.dumps(stored))
            connection.execute(text("UPDATE coach.voice_jobs SET expires_at=now()-interval '1 second' WHERE goal_id=:g"),{'g':self.goal})
        self.assertEqual(self.client.get(result_url,headers=self.auth[0]).json(),{'status':'expired','text':None})

    def test_failed_transcription_can_retry_the_same_audio(self):
        body=audio_body()
        self.speech.fail=True
        self.client.post(self.url,headers=self.auth[0],json=body)
        self.assertEqual(self.client.get(self.url+'/'+body['request_id'],headers=self.auth[0]).json()['status'],'failed')
        self.speech.fail=False
        self.client.post(self.url,headers=self.auth[0],json=body)
        self.assertEqual(self.client.get(self.url+'/'+body['request_id'],headers=self.auth[0]).json()['status'],'complete')
        self.assertEqual(self.speech.calls,2)

    def test_invalid_audio_request_does_not_echo_audio_or_call_provider(self):
        body={**audio_body(),'format':'unsupported'}
        response=self.client.post(self.url,headers=self.auth[0],json=body)
        self.assertEqual(response.status_code,422)
        self.assertNotIn(body['audio_base64'],response.text)
        self.assertEqual(self.speech.calls,0)
