"""First cloud vertical slice: authenticated, persistent choice-question practice."""
import hashlib
import os
import secrets
import sys
import time
import uuid
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import func, insert, select, update

from . import db
from .content import publish
from .contracts import Login, GoalInput, Answer
from .learning import choose_question, evaluate, public_question

sys.path.insert(0, str(db.ROOT / 'scripts'))
import tutor


def uid():
    return uuid.uuid4().hex


def create_app(engine=None, environment=None):
    if engine is None and os.getenv('STORAGE_TRANSPORT') == 'cloudbase_rpc':
        from .managed import create_managed_app
        return create_managed_app()
    environment = environment or os.getenv('APP_ENV', 'local')
    if environment not in {'local', 'development', 'production'}:
        raise RuntimeError('Invalid APP_ENV')
    if environment != 'local':
        required = ['DATABASE_URL', 'WECHAT_APP_ID', 'WECHAT_APP_SECRET', 'CONTENT_RELEASE_ID']
        missing = [key for key in required if not os.getenv(key)]
        if missing:
            raise RuntimeError('Missing deployment settings: ' + ', '.join(missing))
        if not os.getenv('DATABASE_URL', '').startswith('postgresql'):
            raise RuntimeError('Cloud environments require persistent PostgreSQL storage')
    engine = engine or db.make_engine()

    @asynccontextmanager
    async def lifespan(_):
        if environment == 'local':
            db.migrate(engine)
            publish(engine)
        yield

    app = FastAPI(title='无极架构笔记 API', version='0.1.0', lifespan=lifespan,
                  docs_url='/docs' if environment == 'local' else None,
                  redoc_url=None, openapi_url='/openapi.json' if environment == 'local' else None)
    app.state.engine = engine

    @app.middleware('http')
    async def response_headers(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        # Do not expose SQL, identities, tokens or credentials in responses.
        return JSONResponse({'detail': '服务暂时不可用，请稍后重试'}, status_code=503)

    def user_id(connection, authorization):
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(401, '请先登录')
        token = authorization[7:]
        if not 20 <= len(token) <= 256:
            raise HTTPException(401, '登录已失效')
        row = connection.execute(select(db.sessions).where(
            db.sessions.c.token_hash == hashlib.sha256(token.encode()).hexdigest(),
            db.sessions.c.expires_at > int(time.time()))).mappings().first()
        if not row:
            raise HTTPException(401, '登录已失效')
        return row['user_id']

    def owned_goal(connection, goal_id, owner, lock=False):
        stmt = select(db.goals).where(db.goals.c.id == goal_id, db.goals.c.user_id == owner)
        if lock:
            stmt = stmt.with_for_update()
        row = connection.execute(stmt).mappings().first()
        if not row:
            raise HTTPException(404, '学习目标不存在')
        return row

    def login_identity(identity):
        with db.transaction(engine) as connection:
            # Serializes first login too, without accepting a client-supplied user ID.
            if engine.dialect.name == 'postgresql':
                lock_id = int.from_bytes(hashlib.sha256(identity.encode()).digest()[:8], 'big', signed=True)
                connection.exec_driver_sql('SELECT pg_advisory_xact_lock(%s)', (lock_id,))
            owner = connection.execute(select(db.users.c.id).where(db.users.c.identity == identity)).scalar_one_or_none()
            if not owner:
                owner = uid()
                connection.execute(insert(db.users).values(id=owner, identity=identity))
            token = secrets.token_urlsafe(32)
            connection.execute(insert(db.sessions).values(
                token_hash=hashlib.sha256(token.encode()).hexdigest(), user_id=owner,
                expires_at=int(time.time()) + 7 * 86400))
        return {'token': token, 'expires_in': 7 * 86400}

    @app.get('/healthz')
    def health():
        with engine.connect() as connection:
            connection.execute(select(db.packs.c.id).limit(1)).first()
        return {'status': 'ok', 'version': '0.1.0'}

    @app.post('/v1/auth/wechat')
    def wechat_login(body: Login):
        if not os.getenv('WECHAT_APP_ID') or not os.getenv('WECHAT_APP_SECRET'):
            raise HTTPException(503, '尚未配置微信登录')
        try:
            response = httpx.get('https://api.weixin.qq.com/sns/jscode2session', params={
                'appid': os.environ['WECHAT_APP_ID'], 'secret': os.environ['WECHAT_APP_SECRET'],
                'js_code': body.code, 'grant_type': 'authorization_code'}, timeout=10)
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError):
            raise HTTPException(502, '微信登录暂不可用')
        if data.get('errcode') or not data.get('openid'):
            raise HTTPException(401, '微信登录失败，请重试')
        identity = hashlib.sha256(f"{os.environ['WECHAT_APP_ID']}:{data['openid']}".encode()).hexdigest()
        return login_identity(identity)

    @app.post('/v1/auth/local')
    def local_login(request: Request):
        if environment != 'local' or request.client.host not in {'127.0.0.1', '::1', 'testclient'}:
            raise HTTPException(404)
        # Every call creates a new isolated test identity, not a cloud bypass.
        return login_identity('local:' + uid())

    @app.get('/v1/exams')
    def exams():
        with engine.connect() as connection:
            rows = connection.execute(select(db.packs)).mappings().all()
        release = os.getenv('CONTENT_RELEASE_ID')
        return [{'release_id': r['id'], **r['payload']['manifest']}
                for r in rows if (not release or r['id'] == release)
                and r['payload'].get('publication_status', 'ready') == 'ready']

    @app.post('/v1/goals')
    def create_goal(body: GoalInput, authorization: str | None = Header(default=None)):
        with db.transaction(engine) as connection:
            owner = user_id(connection, authorization)
            # A user row lock prevents duplicate concurrent goal creation.
            connection.execute(select(db.users.c.id).where(db.users.c.id == owner).with_for_update()).first()
            release = body.release_id or os.getenv('CONTENT_RELEASE_ID')
            stmt = select(db.packs).where(db.packs.c.exam_id == body.exam_id)
            if release:
                stmt = stmt.where(db.packs.c.id == release)
            rows = connection.execute(stmt).mappings().all()
            if len(rows) != 1:
                raise HTTPException(422, '请选择有效的考试与内容版本')
            pack = rows[0]
            if pack['payload'].get('publication_status', 'ready') != 'ready':
                raise HTTPException(503, '内容仍在发布中，请稍后再试')
            existing = connection.execute(select(db.goals.c.id).where(
                db.goals.c.user_id == owner, db.goals.c.release_id == pack['id'])).scalar_one_or_none()
            if existing:
                return {'goal_id': existing, 'release_id': pack['id']}
            if pack['payload']['manifest']['adapter'] != 'legacy_architect_v1':
                raise HTTPException(422, '该考试适配器尚未启用')
            goal_id = uid()
            now = tutor.now_iso()
            profile = {'exam_date': body.exam_date.isoformat() if body.exam_date else None,
                       'daily_minutes': body.daily_minutes, 'timezone': 'Asia/Shanghai', 'created_at': now}
            connection.execute(insert(db.goals).values(id=goal_id, user_id=owner,
                release_id=pack['id'], profile=profile,
                state=tutor.new_state(pack['payload']['curriculum'], now)))
        return {'goal_id': goal_id, 'release_id': pack['id']}

    @app.get('/v1/goals/{goal_id}/status')
    def status(goal_id: str, authorization: str | None = Header(default=None)):
        with engine.connect() as connection:
            goal = owned_goal(connection, goal_id, user_id(connection, authorization))
            count = connection.execute(select(func.count()).select_from(db.attempts).where(db.attempts.c.goal_id == goal_id)).scalar_one()
        return {**tutor.status_payload(goal['profile'], goal['state']), 'answered_count': count,
                'notice': '短练习不代表完整限时考试成绩；案例与论文仍待诊断'}

    @app.post('/v1/goals/{goal_id}/next')
    def next_question(goal_id: str, authorization: str | None = Header(default=None)):
        with db.transaction(engine) as connection:
            goal = owned_goal(connection, goal_id, user_id(connection, authorization), lock=True)
            pending = connection.execute(select(db.issues).where(db.issues.c.goal_id == goal_id,
                ~db.issues.c.id.in_(select(db.attempts.c.issue_id)))).mappings().first()
            if pending:
                issue = pending
                qrow = connection.execute(select(db.questions).where(db.questions.c.key == issue['question_key'])).mappings().one()
            else:
                pack = connection.execute(select(db.packs.c.payload).where(db.packs.c.id == goal['release_id'])).scalar_one()
                pool = connection.execute(select(db.questions).where(db.questions.c.release_id == goal['release_id'])).mappings().all()
                previous = connection.execute(select(db.attempts.c.event).where(db.attempts.c.goal_id == goal_id)).scalars().all()
                if not pool:
                    raise HTTPException(503, '题库尚未发布')
                last = {}
                for e in previous:
                    last[e['item_id']] = max(last.get(e['item_id'],''), e['at'])
                chosen = choose_question(goal['profile'],goal['state'],pack['curriculum'],
                    [dict(row['payload'],key=row['key']) for row in pool],last)
                qrow = next(row for row in pool if row['key']==chosen['key'])
                issue = {'id': uid(), 'goal_id': goal_id, 'question_key': qrow['key'], 'issued_at': int(time.time())}
                connection.execute(insert(db.issues).values(**issue))
            q = qrow['payload']
            # Explicit allowlist: never send answers, explanations, or private source files.
            return public_question(issue['id'],q)

    @app.post('/v1/issues/{issue_id}/answer')
    def answer(issue_id: str, body: Answer, authorization: str | None = Header(default=None)):
        with db.transaction(engine) as connection:
            owner = user_id(connection, authorization)
            issue = connection.execute(select(db.issues).where(db.issues.c.id == issue_id)).mappings().first()
            if not issue:
                raise HTTPException(404)
            goal = owned_goal(connection, issue['goal_id'], owner, lock=True)
            existing = connection.execute(select(db.attempts).where(db.attempts.c.issue_id == issue_id)).mappings().first()
            if existing:
                if existing['request'] != body.model_dump():
                    raise HTTPException(409, '这道题已提交，不能改写原始作答')
                return existing['report']
            q = connection.execute(select(db.questions.c.payload).where(db.questions.c.key == issue['question_key'])).scalar_one()
            if body.selected not in {o['label'] for o in q['options']}:
                raise HTTPException(422, '选项无效')
            curriculum = connection.execute(select(db.packs.c.payload).where(db.packs.c.id == goal['release_id'])).scalar_one()['curriculum']
            state,event,report = evaluate(q,body,issue,goal['state'],curriculum)
            connection.execute(insert(db.attempts).values(id=event['attempt_id'], issue_id=issue_id,
                goal_id=goal['id'], request=body.model_dump(), event=event, report=report))
            connection.execute(update(db.goals).where(db.goals.c.id == goal['id']).values(state=state))
            return report

    return app


app = create_app()
