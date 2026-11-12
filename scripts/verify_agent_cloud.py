"""Real model + owned cloud chat smoke test with a disposable synthetic account."""
import argparse
import hashlib
import json
import os
import secrets
import time
import uuid

import httpx
from fastapi.testclient import TestClient

from apps.api.db import ROOT
from apps.api.managed import ManagedStore, create_managed_app
from scripts.provision_managed import load_env
from scripts.import_model_config import read_config
from scripts.publish_cloud_content import execute, literal


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--deployed',action='store_true')
    parser.add_argument('--source')
    args=parser.parse_args()
    load_env()
    if args.source:
        if args.deployed:
            raise SystemExit('Candidate config can only be used for the in-process shadow test')
        os.environ.update(read_config(args.source))
    env=os.environ['TCB_ENV_ID']
    if env!='wuji-coach-dev-d4gtwqert85ce3eae':
        raise SystemExit('Only the selected development environment is supported')
    # Reapply additive schema in case the publisher ran before the last migration edit.
    execute(env,(ROOT/'cloudbase/migrations/20261101234000_chat.sql').read_text())
    store=ManagedStore()
    user=uuid.uuid4().hex
    token=secrets.token_urlsafe(32)
    store.call('login',{'identity':'disposable-agent-'+user,'user_id':user,
                       'token_hash':hashlib.sha256(token.encode()).hexdigest()})
    try:
        if args.deployed:
            base=os.environ['API_BASE_URL']
            if base!='https://wuji-coach-dev-339504-11-1522840065.sh.run.tcloudbase.com':
                raise RuntimeError('Unexpected deployment URL')
            client=httpx.Client(base_url=base,timeout=90)
        else:
            client=TestClient(create_managed_app(store))
        with client:
            auth={'Authorization':'Bearer '+token}
            goal=client.post('/v1/goals',headers=auth,json={})
            assert goal.status_code==200
            goal_id=goal.json()['goal_id']
            url=f'/v1/goals/{goal_id}/chat'
            body={'request_id':uuid.uuid4().hex,'message':'ATAM 的敏感点和权衡点有什么区别？用两句话解释。'}
            response=client.post(url+'?async_mode=true',headers=auth,json=body)
            assert response.status_code in (200,202), f'Chat HTTP {response.status_code}'
            result=response.json()
            if response.status_code==202:
                for _ in range(45):
                    state=client.get(url+'/'+body['request_id'],headers=auth)
                    assert state.status_code==200
                    if state.json()['status']=='complete':
                        result=state.json()['response']
                        break
                    assert state.json()['status']!='failed','Model job failed'
                    time.sleep(1)
            assert result.get('text') and result.get('sources')
            assert 'reasoning_content' not in json.dumps(result)
            assert token not in json.dumps(result)
            replay=client.post(url,headers=auth,json=body)
            assert replay.status_code==200 and replay.json()==result
            history=client.get(url,headers=auth)
            assert history.status_code==200 and len(history.json()['items'])==1
            practice={'request_id':uuid.uuid4().hex,'message':'今天只有三分钟，请帮我开始练一道选择题。'}
            practiced=client.post(url,headers=auth,json=practice)
            assert practiced.status_code==200
            assert practiced.json()['actions']==[{'type':'practice','label':'开始练一道'}]
            assert 'A.' not in practiced.json()['text'] and '答案是' not in practiced.json()['text']
            assert client.get(url).status_code==401
            assert client.get(f'/v1/goals/{goal_id}/status',headers=auth).json()['answered_count']==0
            artifact=ROOT/'.study/platform/agent-smoke.json'
            artifact.write_text(json.dumps({'deployed':args.deployed,'real_model':True,'text':result['text'],
                'sources':result['sources'],'actions':practiced.json()['actions']},ensure_ascii=False,indent=2))
            artifact.chmod(0o600)
    finally:
        goals=f'SELECT id FROM coach.learning_goals WHERE user_id={literal(user)}'
        execute(env,f'''BEGIN;
          DELETE FROM coach.chat_turns WHERE goal_id IN ({goals});
          DELETE FROM coach.learning_goals WHERE user_id={literal(user)};
          DELETE FROM coach.sessions WHERE user_id={literal(user)};
          DELETE FROM coach.users WHERE id={literal(user)}; COMMIT;''')
        store.client.close()
    print(json.dumps({'real_model':True,'deployed_api':args.deployed,'chat_persistence':True,
        'idempotence':True,'no_grade_writes':True,'synthetic_data_removed':True}))


if __name__=='__main__':
    main()
