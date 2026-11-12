import base64
import io
import json
import os
import uuid
import unittest
import zipfile
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import text

from apps.api.documents import extract_document,extract_local,DocumentError
from apps.api.subjective import load_pack,rubric_for,grade_submission,apply_review
from apps.api.managed import create_managed_app
from apps.api.uploads import EphemeralUploads,UploadStart,UploadChunk
import tests.test_agent as helpers


TEXT='本项目服务于匿名商城，作者负责订单架构，使用领域边界划分服务，以事务消息解决一致性，通过压测验证性能并持续改进。'*8


def docx_bytes(text_value=TEXT):
    output=io.BytesIO()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'+text_value+'</w:t></w:r></w:p></w:body></w:document>')
    return output.getvalue()


class Grader:
    def __init__(self):
        self.calls=0;self.fail=False;self.fabricate=False

    def complete(self,messages,tools=False,**kwargs):
        self.calls+=1
        if self.fail:
            raise HTTPException(503,'synthetic capacity failure')
        data=json.loads(messages[1]['content']);rubric=data['rubric'];segment=data['answer_segments'][0]['id']
        return {'content':json.dumps({'schema_version':1,'question_ref':rubric['question_ref'],
            'points':[{'id':p['id'],'hit':True,'evidence_ids':['FABRICATED' if self.fabricate else segment]} for p in rubric['key_points']],
            'errors_hit':[],'typos':[],'comment':'已覆盖本次评分点。','final_score':9999})}


class SubjectiveUnitTest(unittest.TestCase):
    def test_chunk_buffers_are_owned_immutable_and_removed_after_use(self):
        cache=EphemeralUploads();encoded=base64.b64encode(b'x'*100000).decode()
        body=UploadStart(request_id='test_upload_1',purpose='essay',filename='paper.txt',byte_size=100000)
        upload=cache.start('goal','token-hash',body);key=upload['upload_id']
        with self.assertRaises(HTTPException):cache.put(key,'other-goal','token-hash',UploadChunk(index=0,data=encoded[:64000]))
        with self.assertRaises(HTTPException):cache.put(key,'goal','other-hash',UploadChunk(index=0,data=encoded[:64000]))
        for i in range(0,len(encoded),64000):cache.put(key,'goal','token-hash',UploadChunk(index=i//64000,data=encoded[i:i+64000]))
        with self.assertRaises(HTTPException):cache.put(key,'goal','token-hash',UploadChunk(index=0,data='B'*64000))
        self.assertEqual(cache.take(key,'goal','token-hash',body.request_id,'essay','paper.txt'),encoded)
        self.assertEqual(cache.items,{})

    def test_essay_practice_event_obeys_existing_progress_protocol(self):
        from apps.api.learning import tutor
        from apps.api.db import ROOT
        curriculum=json.loads((ROOT/'tutor/curriculum.json').read_text())
        task=load_pack()['essay'];report=grade_submission(Grader(),task,'essay',TEXT)
        state,event=apply_review({'state':tutor.new_state(curriculum,tutor.now_iso())},task,'essay',uuid.uuid4().hex,report,0,curriculum)
        self.assertIsNone(state['subjects']['essay'].get('predicted_score'))

    def test_only_deterministic_engine_assigns_score(self):
        content=load_pack();provider=Grader()
        for kind,task,expected in [('case',content['cases'][0],25),('essay',content['essay'],75)]:
            report=grade_submission(provider,task,kind,TEXT)
            self.assertEqual(report['final_score'],expected)
            self.assertEqual(sum(p['weight'] for p in report['points'] if p['hit']),expected)
            self.assertIn('AI 估分',report['label'])
        self.assertIn('片段',report['notice'])

    def test_fabricated_evidence_never_becomes_a_saved_grade(self):
        provider=Grader();provider.fabricate=True
        with self.assertRaises(HTTPException):
            grade_submission(provider,load_pack()['cases'][0],'case',TEXT)
        self.assertEqual(provider.calls,2)

    def test_supported_files_and_private_parser_subprocess(self):
        for name,data in [('paper.txt',TEXT.encode()),('paper.docx',docx_bytes())]:
            actual=extract_document(name,base64.b64encode(data).decode())
            self.assertEqual(actual,TEXT)
        for name,data in [('scan.pdf',b'%PDF-broken'),('old.doc',b'x'),('text.txt',b'x\x00'*100)]:
            with self.assertRaises(HTTPException):extract_document(name,base64.b64encode(data).decode())
        with self.assertRaises(HTTPException):extract_document('paper.txt',base64.b64encode(b'x'*(2*1024*1024+1)).decode())

    def test_docx_zip_bomb_and_external_entity_are_rejected(self):
        output=io.BytesIO()
        with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('word/document.xml','x'*(13*1024*1024))
        with self.assertRaises(DocumentError):extract_local(output.getvalue(),'.docx')
        with self.assertRaises(DocumentError):extract_local(docx_bytes('<!DOCTYPE evil>'),'.docx')

    def test_pdf_text_encryption_and_scan_boundary(self):
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject,NameObject,DecodedStreamObject
        writer=PdfWriter();page=writer.add_blank_page(600,800)
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):font})})
        stream=DecodedStreamObject();stream.set_data(b'BT /F1 12 Tf 30 700 Td ('+b'Synthetic architecture paper describing goals, decisions, tradeoffs and verification. '*4+b') Tj ET')
        page[NameObject('/Contents')]=stream
        out=io.BytesIO();writer.write(out)
        self.assertIn('Synthetic architecture',extract_document('paper.pdf',base64.b64encode(out.getvalue()).decode()))
        writer.encrypt('synthetic-password');out=io.BytesIO();writer.write(out)
        with self.assertRaises(HTTPException):extract_document('locked.pdf',base64.b64encode(out.getvalue()).decode())
        scanned=PdfWriter();scanned.add_blank_page(600,800);out=io.BytesIO();scanned.write(out)
        with self.assertRaises(HTTPException):extract_document('scan.pdf',base64.b64encode(out.getvalue()).decode())


@unittest.skipUnless('127.0.0.1:55439/' in os.getenv('TEST_DATABASE_URL',''),'requires disposable local PostgreSQL')
class ReviewIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        helpers.ChatIntegrationTest.setUpClass.__func__(cls)
        with cls.engine.begin() as c:
            from apps.api.db import ROOT
            c.connection.driver_connection.cursor().execute((ROOT/'cloudbase/migrations/20261102020000_subjective.sql').read_text())

    @classmethod
    def tearDownClass(cls):cls.engine.dispose()

    def setUp(self):
        self.store=helpers.LocalChatStore(self.engine);self.grader=Grader()
        self.auth=[]
        import hashlib,secrets
        for _ in range(2):
            token=secrets.token_urlsafe(32)
            self.store.call('login',{'identity':uuid.uuid4().hex,'user_id':uuid.uuid4().hex,'token_hash':hashlib.sha256(token.encode()).hexdigest()})
            self.auth.append({'Authorization':'Bearer '+token})
        with patch.dict(os.environ,{'CONTENT_RELEASE_ID':self.release}):
            self.client=TestClient(create_managed_app(self.store,self.grader))
        self.goal=self.client.post('/v1/goals',json={},headers=self.auth[0]).json()['goal_id']
        self.url=f'/v1/goals/{self.goal}'

    def tearDown(self):self.client.close()

    def submit(self,kind='case'):
        body={'request_id':uuid.uuid4().hex,'kind':kind}
        if kind=='case':
            task=self.client.post(self.url+'/case',headers=self.auth[0]).json()
            self.assertNotIn('points',json.dumps(task))
            body.update(issue_id=task['case']['issue_id'],answer=TEXT,duration_seconds=30)
        else:body.update(filename='synthetic.docx',file_base64=base64.b64encode(docx_bytes()).decode())
        sent=self.client.post(self.url+'/reviews',headers=self.auth[0],json=body)
        self.assertEqual(sent.status_code,202,sent.text)
        return body

    def test_case_owned_replay_history_and_learning_state(self):
        body=self.submit()
        result=self.client.get(self.url+'/reviews/'+body['request_id'],headers=self.auth[0]).json()
        self.assertEqual(result['status'],'complete')
        self.assertEqual(result['response']['report']['final_score'],25)
        self.assertEqual(self.client.post(self.url+'/reviews',headers=self.auth[0],json=body).json(),result)
        self.assertEqual(self.grader.calls,1)
        self.assertEqual(self.client.post(self.url+'/reviews',headers=self.auth[0],json={**body,'answer':TEXT+'changed'}).status_code,409)
        self.assertEqual(self.client.get(self.url+'/reviews/'+body['request_id'],headers=self.auth[1]).status_code,404)
        self.assertEqual(self.client.get(self.url+'/reviews/'+body['request_id']).status_code,401)
        history=self.client.get(self.url+'/chat',headers=self.auth[0]).json()['items']
        self.assertEqual([x['response']['kind'] for x in history],['case_task','review_report'])
        status=self.client.get(self.url+'/status',headers=self.auth[0]).json()
        self.assertIsNone(status['subjects']['case']['predicted_score'])
        self.assertEqual(self.client.get(self.url+'/reviews/summary',headers=self.auth[0]).json()['case_count'],1)

    def test_essay_document_record_does_not_claim_full_exam_mastery(self):
        body=self.submit('essay')
        result=self.client.get(self.url+'/reviews/'+body['request_id'],headers=self.auth[0]).json()
        self.assertEqual(result['status'],'complete')
        self.assertIn('片段',result['response']['report']['notice'])
        history=self.client.get(self.url+'/chat',headers=self.auth[0]).json()['items']
        self.assertEqual(history[-1]['user'],'上传论文：synthetic.docx')
        with self.engine.connect() as c:
            stored=c.execute(text('SELECT input FROM coach.subjective_reviews WHERE goal_id=:g'),{'g':self.goal}).scalar_one()
        self.assertNotIn('file_base64',stored)
        self.assertEqual(stored['answer'],TEXT)

    def test_failed_grade_is_recoverable_and_dismiss_does_not_count(self):
        self.grader.fail=True;body=self.submit()
        result=self.client.get(self.url+'/reviews/'+body['request_id'],headers=self.auth[0]).json()
        self.assertEqual(result['status'],'failed')
        self.assertEqual(self.client.get(self.url+'/reviews/summary',headers=self.auth[0]).json()['case_count'],0)
        self.grader.fail=False
        response=self.client.post(self.url+'/reviews/'+body['request_id']+'/retry',headers=self.auth[0])
        self.assertEqual(response.status_code,202)
        self.assertEqual(self.client.get(self.url+'/reviews/'+body['request_id'],headers=self.auth[0]).json()['status'],'complete')
        self.grader.fail=True;body=self.submit()
        self.assertEqual(self.client.post(self.url+'/reviews/'+body['request_id']+'/dismiss',headers=self.auth[0]).status_code,200)
        self.assertIsNone(self.client.get(self.url+'/reviews/pending',headers=self.auth[0]).json()['job'])
        self.assertEqual(self.client.get(self.url+'/reviews/summary',headers=self.auth[0]).json()['case_count'],1)

    def test_invalid_file_and_request_do_not_echo_uploaded_contents(self):
        body={'kind':'essay','request_id':uuid.uuid4().hex,'filename':'file.pdf','file_base64':'sensitive-invalid-payload'}
        result=self.client.post(self.url+'/reviews',headers=self.auth[0],json=body)
        self.assertEqual(result.status_code,422)
        self.assertNotIn('sensitive-invalid-payload',result.text)
        result=self.client.post(self.url+'/reviews',headers=self.auth[0],json={**body,'unexpected':'private'})
        self.assertNotIn('private',result.text)

    def test_chunked_document_and_audio_use_the_same_authenticated_gateway(self):
        from tests.test_speech import audio_body
        for purpose,filename,raw in [('essay','paper.docx',base64.b64encode(docx_bytes()).decode()),
                                     ('voice','audio.wav',audio_body(4)['audio_base64'])]:
            rid=uuid.uuid4().hex;size=len(base64.b64decode(raw))
            begun=self.client.post(self.url+'/uploads',headers=self.auth[0],json={
                'request_id':rid,'purpose':purpose,'filename':filename,'byte_size':size})
            self.assertEqual(begun.status_code,200,begun.text)
            upload=begun.json();chunk_url=self.url+'/uploads/'+upload['upload_id']+'/chunks'
            self.assertEqual(self.client.post(chunk_url,headers=self.auth[1],json={'index':0,'data':raw[:64000]}).status_code,404)
            for offset in range(0,len(raw),64000):
                sent=self.client.post(chunk_url,headers=self.auth[0],json={'index':offset//64000,'data':raw[offset:offset+64000]})
                self.assertEqual(sent.status_code,200,sent.text)
            if purpose=='essay':
                sent=self.client.post(self.url+'/reviews',headers=self.auth[0],json={
                    'request_id':rid,'kind':'essay','filename':filename,'upload_id':upload['upload_id']})
                self.assertEqual(sent.status_code,202,sent.text)
                self.assertEqual(self.client.get(self.url+'/reviews/'+rid,headers=self.auth[0]).json()['status'],'complete')
            else:
                # Decode and enqueue the actual multi-chunk audio without calling
                # an external recognizer in a local integration test.
                with patch('apps.api.speech.SpeechProvider.transcribe',return_value='合成语音转写'):
                    sent=self.client.post(self.url+'/voice',headers=self.auth[0],json={
                        'request_id':rid,'format':'wav','upload_id':upload['upload_id']})
                self.assertEqual(sent.status_code,202,sent.text)
                self.assertEqual(self.client.get(self.url+'/voice/'+rid,headers=self.auth[0]).json()['status'],'complete')
