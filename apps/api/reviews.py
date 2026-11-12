"""Owned asynchronous subjective review routes; originals stay in memory only."""
import uuid

from fastapi import BackgroundTasks, Header, HTTPException
from fastapi.responses import JSONResponse

from .contracts import ReviewInput
from .documents import extract_document
from .subjective import load_pack, public_case, grade_submission, apply_review, input_hash


def install_review_routes(app,store,provider,release,token_hash,uploads):
    def pack():
        exam=store.pack(release)['release']['manifest']['id']
        return load_pack(exam)

    def task_for(ref):
        content=pack()
        task=next((t for t in [*content['cases'],content['essay']] if t['id']==ref),None)
        if not task:
            raise HTTPException(422,'练习版本已更新，请重新打开练习。')
        return task

    @app.post('/v1/goals/{goal_id}/case')
    def next_case(goal_id: str,authorization: str | None = Header(default=None)):
        token=token_hash(authorization)
        content=pack()
        issue=store.subjective('case_next',{'goal_id':goal_id,'issue_id':uuid.uuid4().hex,
                              'task_refs':[t['id'] for t in content['cases']]},token)
        case=public_case(issue,task_for(issue['task_ref']))
        response={'text':case['prompt'],'kind':'case_task','case':case,'sources':[],'actions':[]}
        store.subjective('case_message',{'goal_id':goal_id,'issue_id':issue['id'],'response':response},token)
        return response

    @app.get('/v1/goals/{goal_id}/reviews/summary')
    def summary(goal_id: str,authorization: str | None = Header(default=None)):
        return store.subjective('summary',{'goal_id':goal_id},token_hash(authorization))

    @app.get('/v1/goals/{goal_id}/reviews/pending')
    def pending(goal_id: str,authorization: str | None = Header(default=None)):
        return store.subjective('pending',{'goal_id':goal_id},token_hash(authorization))

    @app.get('/v1/goals/{goal_id}/reviews/{request_id}')
    def review_result(goal_id: str,request_id: str,authorization: str | None = Header(default=None)):
        return store.subjective('result',{'goal_id':goal_id,'request_id':request_id},token_hash(authorization))

    def generate(payload,token,value,kind):
        try:
            task=task_for(value['task_ref'])
            report=grade_submission(provider,task,kind,value['answer'],value.get('prompt',''))
            missed=[p['desc'] for p in report['points'] if not p['hit']]
            report['next_step']=missed[0] if missed else ''
            text=f"{report['label']}：{report['final_score']} / {report['max_score']}。"
            text+='\n优先补这一点：'+missed[0] if missed else '\n这次覆盖了评分点，继续用新的场景检验。'
            response={'text':text,'kind':'review_report','review_id':payload['request_id'],
                      'report':report,'review_kind':kind,'title':task['title'],
                      'filename':value.get('filename',''),'case_issue_id':payload.get('issue_id'),
                      'sources':[],'actions':[]}
            message=value['answer'] if kind=='case' else '上传论文：'+value.get('filename','论文文稿')
            for _ in range(4):
                snapshot=store.call('status',{'goal_id':payload['goal_id']},token)
                curriculum=store.pack(snapshot['goal']['release_id'])['release']['curriculum']
                state,event=apply_review(snapshot['goal'],task,kind,'subjective_'+payload['request_id'],
                                         report,value['duration_seconds'],curriculum)
                saved=store.subjective('complete',{**payload,'expected_state':snapshot['goal']['state'],
                    'state':state,'event':event,'response':response,'message':message},token)
                if not saved.get('retry'):
                    return
            raise HTTPException(503,'学习状态正在更新，请重试。')
        except Exception:
            try:
                store.subjective('fail',payload,token)
            except Exception:
                pass

    def begin(goal_id,request_id,kind,issue_id,value,token,tasks):
        payload={'goal_id':goal_id,'request_id':request_id,'kind':kind,'issue_id':issue_id,
                 'input':value,'input_hash':input_hash(value),'lease':uuid.uuid4().hex}
        result=store.subjective('begin',payload,token)
        if result.get('generate'):
            tasks.add_task(generate,payload,token,value,kind)
        return JSONResponse({key:result[key] for key in ('status','response') if key in result},
                            200 if result.get('status')=='complete' else 202)

    @app.post('/v1/goals/{goal_id}/reviews')
    def review(goal_id: str,body: ReviewInput,tasks: BackgroundTasks,authorization: str | None = Header(default=None)):
        token=token_hash(authorization)
        store.call('status',{'goal_id':goal_id},token)
        if body.kind=='case':
            if not body.issue_id or not body.answer.strip() or body.file_base64 or body.upload_id or body.filename or body.prompt:
                raise HTTPException(422,'请先打开案例，再提交语音转写或文字答案。')
            issue=store.subjective('issue',{'goal_id':goal_id,'issue_id':body.issue_id},token)
            ref=issue['task_ref']
            answer=body.answer.strip()
        else:
            if body.issue_id or body.answer or not body.filename or not (body.file_base64 or body.upload_id) or (body.file_base64 and body.upload_id):
                raise HTTPException(422,'请选择要批改的论文文件。')
            ref=pack()['essay']['id']
            encoded=uploads.take(body.upload_id,goal_id,token,body.request_id,'essay',body.filename) if body.upload_id else body.file_base64
            answer=extract_document(body.filename,encoded)
        value={'task_ref':ref,'answer':answer,'filename':body.filename,'prompt':body.prompt,
               'duration_seconds':body.duration_seconds}
        return begin(goal_id,body.request_id,body.kind,body.issue_id,value,token,tasks)

    @app.post('/v1/goals/{goal_id}/reviews/{request_id}/retry')
    def retry_review(goal_id: str,request_id: str,tasks: BackgroundTasks,authorization: str | None = Header(default=None)):
        token=token_hash(authorization)
        if not 8<=len(request_id)<=80:
            raise HTTPException(422,'评分请求无效。')
        old=store.subjective('input',{'goal_id':goal_id,'request_id':request_id},token)
        return begin(goal_id,request_id,old['kind'],old['issue_id'],old['input'],token,tasks)

    @app.post('/v1/goals/{goal_id}/reviews/{request_id}/dismiss')
    def dismiss_review(goal_id: str,request_id: str,authorization: str | None = Header(default=None)):
        return store.subjective('dismiss',{'goal_id':goal_id,'request_id':request_id},token_hash(authorization))
