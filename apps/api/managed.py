"""Managed free-PG transport: fixed RPC + atomic compare-and-swap commits."""
import hashlib
import os
import secrets
import threading
import time
import uuid
from collections import defaultdict, deque

import httpx
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler

from .contracts import Answer, ChatInput, GoalInput, Login, VoiceInput
from .agent import create_provider, respond
from .speech import ASR_MODEL, SpeechProvider, decode_audio
from .learning import choose_question, evaluate, public_question, tutor
from .reviews import install_review_routes
from .uploads import EphemeralUploads,install_upload_routes


class ManagedStore:
    def __init__(self):
        self.env = os.environ['TCB_ENV_ID']
        self.key = os.environ['CLOUDBASE_SERVER_KEY']
        self.base = f'https://{self.env}.api.tcloudbasegateway.com/v1/rdb/rest/rpc/coach_rpc'
        self.cache = {}
        self.lock = threading.Lock()
        self.client = httpx.Client(timeout=15)

    def call(self, action, payload=None, token='', rpc='coach_rpc'):
        try:
            response = self.client.post(self.base.rsplit('/',1)[0]+'/'+rpc, headers={'Authorization':'Bearer '+self.key},
                json={'p_action':action,'p_payload':payload or {},'p_token':token})
            response.raise_for_status()
            result = response.json()
        except (httpx.HTTPError, ValueError):
            raise HTTPException(503, '数据库暂不可用，请稍后重试')
        if not isinstance(result, dict):
            raise HTTPException(503, '数据库返回格式异常')
        if result.get('error'):
            code = {'unauthorized':401,'not_found':404,'conflict':409,
                    'invalid_exam':422,'invalid_answer':422,'busy':409,'rate_limit':429}.get(result['error'],503)
            raise HTTPException(code, {401:'请重新登录',404:'学习记录不存在',409:'原始作答不能改写',
                                      422:'请求不符合当前练习要求',429:'今天先歇一歇，对话额度明天恢复',503:'服务暂不可用'}[code] if result['error']!='busy' else '私教正在回复，请稍后用原消息重试')
        return result

    def chat(self, action, payload=None, token=''):
        return self.call(action,payload,token,rpc='coach_chat_rpc')

    def voice(self, action, payload=None, token=''):
        return self.call(action,payload,token,rpc='coach_voice_rpc')

    def subjective(self, action, payload=None, token=''):
        return self.call(action,payload,token,rpc='coach_subjective_rpc')

    def pack(self, release):
        with self.lock:
            if release not in self.cache:
                if len(self.cache) >= 4:
                    self.cache.pop(next(iter(self.cache)))
                self.cache[release] = self.call('pack', {'release_id':release})
            return self.cache[release]


def token_hash(authorization):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(401, '请先登录')
    value = authorization[7:]
    if not 20 <= len(value) <= 256:
        raise HTTPException(401, '登录已失效')
    return hashlib.sha256(value.encode()).hexdigest()


def create_managed_app(store=None, provider=None, speech=None):
    if not os.getenv('CONTENT_RELEASE_ID'):
        raise RuntimeError('Missing CONTENT_RELEASE_ID')
    store = store or ManagedStore()
    provider = provider or create_provider()
    speech = speech or SpeechProvider()
    knowledge_cache = {}
    release = os.environ['CONTENT_RELEASE_ID']
    app = FastAPI(title='无极架构笔记 API',docs_url=None,redoc_url=None,openapi_url=None)
    uploads=EphemeralUploads()
    attempts = defaultdict(deque)
    rate_lock = threading.Lock()

    @app.middleware('http')
    async def guards(request, call_next):
        if request.method=='POST' and '/uploads' in request.url.path:
            data=bytearray()
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data)>70000:return JSONResponse({'detail':'上传分片过大，请重新选择文件'},413)
            request._body=bytes(data)
        if request.method=='POST' and request.url.path.endswith('/reviews'):
            data=bytearray()
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data)>2900000:
                    return JSONResponse({'detail':'请选择 2 MB 以内的论文文件'},413)
            request._body=bytes(data)
        if request.method=='POST' and request.url.path.endswith('/voice'):
            try:
                if int(request.headers.get('content-length','0'))>750000:
                    return JSONResponse({'detail':'录音较大，请分段录制'},413)
            except ValueError:
                return JSONResponse({'detail':'请求格式不正确'},400)
        # Ingress should also enforce global limits. This bounds expensive login calls per instance.
        if request.url.path == '/v1/auth/wechat':
            identity = request.client.host if request.client else 'unknown'
            with rate_lock:
                if len(attempts) > 5000:
                    attempts.clear()
                times = attempts[identity]
                now = time.monotonic()
                while times and times[0] < now - 60:
                    times.popleft()
                if len(times) >= 15:
                    return JSONResponse({'detail':'请稍后再试'},429)
                times.append(now)
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.exception_handler(Exception)
    async def unknown(request, exc):
        return JSONResponse({'detail':'服务暂不可用，请稍后重试'},503)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request,error):
        if '/uploads' in request.url.path:
            return JSONResponse({'detail':'文件分片格式不正确，请重试'},422)
        if '/voice' in request.url.path or '/reviews' in request.url.path:
            if '/reviews' in request.url.path:
                return JSONResponse({'detail':'批改请求格式不正确，请检查文件或答案后重试'},422)
            return JSONResponse({'detail':'录音请求格式不正确，请重新录制'},422)
        return await request_validation_exception_handler(request,error)

    @app.get('/healthz')
    def health():
        ready = store.call('health', {'release_id':release})
        if not ready.get('ready'):
            raise HTTPException(503, '内容尚未发布')
        return {'status':'ok','version':'0.5.0','storage':'cloudbase_rpc','subjective_ready':True,'uploads_ready':True,
                'agent_configured':bool(os.getenv('MODEL_API_KEY') and os.getenv('KNOWLEDGE_RELEASE_ID')),
                'agent_provider':os.getenv('MODEL_PROVIDER','siliconflow'),
                'agent_model':os.getenv('MODEL_NAME') or None,
                'agent_free_only':os.getenv('MODEL_FREE_ONLY','false')=='true',
                'speech_model':ASR_MODEL,
                'speech_ready':bool(os.getenv('ASR_API_KEY') or (os.getenv('MODEL_API_KEY') and os.getenv('MODEL_PROVIDER')=='siliconflow')),
                'wechat_ready':bool(os.getenv('WECHAT_APP_ID') and os.getenv('WECHAT_APP_SECRET'))}

    @app.post('/v1/auth/wechat')
    def login(body: Login):
        app_id, secret = os.getenv('WECHAT_APP_ID'),os.getenv('WECHAT_APP_SECRET')
        if not app_id or not secret:
            raise HTTPException(503, '微信接入配置尚未完成')
        try:
            response = httpx.get('https://api.weixin.qq.com/sns/jscode2session',params={
                'appid':app_id,'secret':secret,'js_code':body.code,'grant_type':'authorization_code'},timeout=10)
            response.raise_for_status()
            identity = response.json()
        except (httpx.HTTPError, ValueError):
            raise HTTPException(502, '微信登录暂不可用')
        if identity.get('errcode') or not identity.get('openid'):
            raise HTTPException(401, '微信登录失败，请重试')
        token = secrets.token_urlsafe(32)
        store.call('login', {'identity':hashlib.sha256(f"{app_id}:{identity['openid']}".encode()).hexdigest(),
            'user_id':uuid.uuid4().hex,'token_hash':hashlib.sha256(token.encode()).hexdigest()})
        return {'token':token,'expires_in':604800}

    @app.get('/v1/exams')
    def exams():
        return store.call('catalog',{'release_id':release})['items']

    @app.post('/v1/goals')
    def goal(body: GoalInput, authorization: str | None = Header(default=None)):
        token = token_hash(authorization)
        if body.release_id and body.release_id != release:
            raise HTTPException(422, '请选择当前发布版本')
        pack = store.pack(release)['release']
        if body.exam_id != pack['manifest']['id']:
            raise HTTPException(422, '该考试尚未开放')
        if pack['manifest']['adapter'] != 'legacy_architect_v1':
            raise HTTPException(422, '该考试适配器尚未启用')
        now = tutor.now_iso()
        return store.call('goal',{'goal_id':uuid.uuid4().hex,'release_id':release,'exam_id':body.exam_id,
            'profile':{'exam_date':body.exam_date.isoformat() if body.exam_date else None,
                'daily_minutes':body.daily_minutes,'timezone':'Asia/Shanghai','created_at':now},
            'state':tutor.new_state(pack['curriculum'],now)},token)

    @app.get('/v1/goals/{goal_id}/status')
    def status(goal_id: str, authorization: str | None = Header(default=None)):
        result = store.call('status',{'goal_id':goal_id},token_hash(authorization))
        goal = result['goal']
        return {**tutor.status_payload(goal['profile'],goal['state']),
                'answered_count':result['answered_count'], 'notice':'短练习不能预测完整考试成绩'}

    @app.post('/v1/goals/{goal_id}/next')
    def next_question(goal_id: str, authorization: str | None = Header(default=None)):
        token = token_hash(authorization)
        for _ in range(4):
            snapshot = store.call('snapshot',{'goal_id':goal_id},token)
            g = snapshot['goal']
            pack = store.pack(g['release_id'])
            pool = {q['key']:q for q in pack['questions']}
            if snapshot['pending']:
                issue = snapshot['pending']
            else:
                question = choose_question(g['profile'],g['state'],pack['release']['curriculum'],
                                           list(pool.values()),snapshot['last'])
                issue = store.call('issue',{'goal_id':goal_id,'issue_id':uuid.uuid4().hex,
                    'question_key':question['key'],'expected_state':g['state']},token)
                if issue.get('retry'):
                    continue
            return public_question(issue['id'],pool[issue['question_key']])
        raise HTTPException(503, '学习状态正在更新，请重试')

    @app.post('/v1/issues/{issue_id}/answer')
    def answer(issue_id: str, body: Answer, authorization: str | None = Header(default=None)):
        token = token_hash(authorization)
        for _ in range(4):
            snapshot = store.call('answer_snapshot',{'issue_id':issue_id},token)
            old = snapshot['attempt']
            if old:
                if old['request'] != body.model_dump():
                    raise HTTPException(409, '原始作答不能改写')
                return old['report']
            g,i = snapshot['goal'],snapshot['issue']
            pack = store.pack(g['release_id'])
            q = next(q for q in pack['questions'] if q['key']==i['question_key'])
            if body.selected not in {o['label'] for o in q['options']}:
                raise HTTPException(422, '选项无效')
            state,event,report = evaluate(q,body,i,g['state'],pack['release']['curriculum'])
            result = store.call('commit_answer',{'issue_id':issue_id,'expected_state':g['state'],
                'request':body.model_dump(),'state':state,'event':event,'report':report},token)
            if not result.get('retry'):
                return result['report']
        raise HTTPException(503, '学习状态正在更新，请重试')

    @app.get('/v1/goals/{goal_id}/chat')
    def chat_history(goal_id: str, authorization: str | None = Header(default=None)):
        return store.chat('history',{'goal_id':goal_id},token_hash(authorization))

    @app.get('/v1/goals/{goal_id}/chat/{request_id}')
    def chat_result(goal_id: str, request_id: str, authorization: str | None = Header(default=None)):
        return store.chat('result',{'goal_id':goal_id,'request_id':request_id},token_hash(authorization))

    def generate_chat(payload, token, history):
        try:
            kb_release = os.getenv('KNOWLEDGE_RELEASE_ID')
            if not kb_release:
                raise HTTPException(503,'私教知识库尚未就绪')
            if kb_release not in knowledge_cache:
                knowledge_cache[kb_release] = store.chat('knowledge',{'release_id':kb_release})['chunks']
            snapshot = store.call('status',{'goal_id':payload['goal_id']},token)
            practice = store.call('snapshot',{'goal_id':payload['goal_id']},token)
            goal_record = snapshot['goal']
            raw = tutor.status_payload(goal_record['profile'],goal_record['state'])
            raw['answered_count'] = snapshot['answered_count']
            raw['notice'] = '短练习不能预测完整考试成绩'
            curriculum = store.pack(goal_record['release_id'])['release']['curriculum']
            recommendations = tutor.recommend_payload(goal_record['profile'],goal_record['state'],curriculum,subject='comprehensive',limit=3)
            context = {'answered_count':raw['answered_count'],
                       'daily_minutes':raw['profile'].get('daily_minutes'),
                       'exam_date':raw['profile'].get('exam_date'),
                       'subjects':{name:{key:item.get(key) for key in ('status','evidence_level','predicted_score','latest_mock_score')}
                                   for name,item in raw['subjects'].items()},
                       'notice':raw['notice'],'practice_pending':bool(practice['pending']),
                       'next_practice_topics':[{key:item[key] for key in ('topic_id','name','review_due','reason')}
                                               for item in recommendations['recommendations']]}
            # Only aggregate status crosses the model boundary, never identity/tokens/raw attempts.
            result = respond(provider,payload['message'],history,context,knowledge_cache[kb_release])
            return store.chat('complete',{**payload,'response':result},token)['response']
        except Exception:
            try:
                store.chat('fail',payload,token)
            except Exception:
                pass
            raise

    def background_chat(payload,token,history):
        try:
            generate_chat(payload,token,history)
        except Exception:
            # generate_chat marks failure; polling can retry the same leased request.
            pass

    @app.post('/v1/goals/{goal_id}/chat')
    def chat(goal_id: str, body: ChatInput, tasks: BackgroundTasks, async_mode: bool = False,
             authorization: str | None = Header(default=None)):
        token = token_hash(authorization)
        payload = {'goal_id':goal_id,'request_id':body.request_id,'message':body.message,'lease':uuid.uuid4().hex}
        turn = store.chat('begin',payload,token)
        if 'response' in turn:
            return turn['response']
        if turn.get('pending'):
            return JSONResponse({'status':'pending'},202)
        if async_mode:
            tasks.add_task(background_chat,payload,token,turn['history'])
            return JSONResponse({'status':'pending'},202)
        return generate_chat(payload,token,turn['history'])

    def generate_voice(payload,token,audio,format):
        try:
            text=speech.transcribe(audio,format)
            store.voice('complete',{**payload,'text':text},token)
        except Exception:
            try:
                store.voice('fail',payload,token)
            except Exception:
                pass

    @app.post('/v1/goals/{goal_id}/voice')
    def voice(goal_id: str,body: VoiceInput,tasks: BackgroundTasks,authorization: str | None = Header(default=None)):
        token=token_hash(authorization)
        store.call('status',{'goal_id':goal_id},token)
        if body.upload_id:
            if body.audio_base64:raise HTTPException(422,'请只提交一份录音。')
            body=body.model_copy(update={'audio_base64':uploads.take(body.upload_id,goal_id,token,body.request_id,'voice')})
        audio,audio_hash,duration=decode_audio(body)
        payload={'goal_id':goal_id,'request_id':body.request_id,'audio_hash':audio_hash,'lease':uuid.uuid4().hex}
        job=store.voice('begin',payload,token)
        if job.get('generate'):
            tasks.add_task(generate_voice,payload,token,audio,body.format)
        return JSONResponse({key:job[key] for key in ('status','text') if key in job},
                            200 if job.get('status')=='complete' else 202)

    @app.get('/v1/goals/{goal_id}/voice/{request_id}')
    def voice_result(goal_id: str,request_id: str,authorization: str | None = Header(default=None)):
        return store.voice('result',{'goal_id':goal_id,'request_id':request_id},token_hash(authorization))
    install_upload_routes(app,store,token_hash,uploads)
    install_review_routes(app,store,provider,release,token_hash,uploads)
    return app
