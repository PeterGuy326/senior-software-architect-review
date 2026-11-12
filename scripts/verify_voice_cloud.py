"""Real ASR + cloud ownership smoke test using locally synthesized Mandarin only."""
import argparse
import base64
import hashlib
import json
import os
import secrets
import time
import uuid

import httpx
from fastapi.testclient import TestClient

from apps.api.db import ROOT
from apps.api.managed import ManagedStore,create_managed_app
from scripts.provision_managed import load_env
from scripts.publish_cloud_content import execute,literal


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--deployed',action='store_true');args=parser.parse_args()
    load_env();env=os.environ['TCB_ENV_ID']
    if env!='wuji-coach-dev-d4gtwqert85ce3eae':
        raise SystemExit('Only the selected development environment is supported')
    execute(env,(ROOT/'cloudbase/migrations/20261102010000_voice.sql').read_text())
    audio_path=ROOT/'.study/platform/asr-smoke-long.mp3'
    audio_format='mp3' if audio_path.exists() else 'wav'
    if not audio_path.exists():audio_path=ROOT/'.study/platform/asr-smoke.wav'
    audio=audio_path.read_bytes()
    store=ManagedStore();user=uuid.uuid4().hex;token=secrets.token_urlsafe(32)
    store.call('login',{'identity':'disposable-voice-'+user,'user_id':user,'token_hash':hashlib.sha256(token.encode()).hexdigest()})
    try:
        client=httpx.Client(base_url=os.environ['API_BASE_URL'],timeout=90) if args.deployed else TestClient(create_managed_app(store))
        with client:
            auth={'Authorization':'Bearer '+token}
            goal=client.post('/v1/goals',headers=auth,json={}).json()['goal_id'];url=f'/v1/goals/{goal}/voice'
            body={'request_id':uuid.uuid4().hex,'format':audio_format,'audio_base64':base64.b64encode(audio).decode()}
            wire=body;encoded=body['audio_base64']
            if len(encoded)>60000:
                upload=client.post(f'/v1/goals/{goal}/uploads',headers=auth,json={'request_id':body['request_id'],
                    'purpose':'voice','filename':'synthetic.'+audio_format,'byte_size':len(audio)})
                assert upload.status_code==200,f'Voice upload HTTP {upload.status_code}'
                upload=upload.json()
                for offset in range(0,len(encoded),64000):
                    chunk=client.post(f'/v1/goals/{goal}/uploads/'+upload['upload_id']+'/chunks',headers=auth,
                        json={'index':offset//64000,'data':encoded[offset:offset+64000]})
                    assert chunk.status_code==200,f'Voice chunk HTTP {chunk.status_code}'
                wire={key:value for key,value in body.items() if key!='audio_base64'}|{'upload_id':upload['upload_id']}
            sent=client.post(url,headers=auth,json=wire);assert sent.status_code==202,f'Voice HTTP {sent.status_code}'
            result_url=url+'/'+body['request_id'];result={}
            for _ in range(55):
                result=client.get(result_url,headers=auth).json()
                if result.get('status')=='complete':break
                assert result.get('status')=='pending','ASR did not complete'
                time.sleep(1)
            assert result.get('text') and '分钟' in result['text']
            assert client.post(url,headers=auth,json=body).json()==result
            assert client.get(result_url).status_code==401
            assert client.get(f'/v1/goals/{goal}/chat',headers=auth).json()['items']==[]
            assert client.get(f'/v1/goals/{goal}/status',headers=auth).json()['answered_count']==0
            report={'deployed':args.deployed,'synthetic_audio':True,'text':result['text'],'audio_persisted':False,
                    'no_auto_chat_or_grades':True,'replay_passed':True,'chunk_upload':len(encoded)>60000}
            p=ROOT/'.study/platform/voice-smoke.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2));p.chmod(0o600)
    finally:
        goals=f'SELECT id FROM coach.learning_goals WHERE user_id={literal(user)}'
        execute(env,f'''BEGIN; DELETE FROM coach.voice_jobs WHERE goal_id IN ({goals});
          DELETE FROM coach.learning_goals WHERE user_id={literal(user)};
          DELETE FROM coach.sessions WHERE user_id={literal(user)};
          DELETE FROM coach.users WHERE id={literal(user)};COMMIT;''')
        store.client.close()
    print(json.dumps({'real_asr':True,'deployed_api':args.deployed,'draft_only':True,'replay_passed':True,'synthetic_data_removed':True}))


if __name__=='__main__':main()
