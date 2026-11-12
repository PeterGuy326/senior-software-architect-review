"""Create/revoke a disposable native-preview session without logging credentials."""
import argparse
import hashlib
import json
import os
import secrets
import uuid

from apps.api.db import ROOT
from apps.api.managed import ManagedStore
from scripts.provision_managed import load_env
from scripts.publish_cloud_content import execute,literal

PATH=ROOT/'.study/platform/native-review-session.json'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--cleanup',action='store_true');args=parser.parse_args()
    load_env();env=os.environ['TCB_ENV_ID']
    if env!='wuji-coach-dev-d4gtwqert85ce3eae':raise SystemExit('Only selected dev environment is supported')
    if args.cleanup:
        if not PATH.exists():print('No disposable native session remains.');return
        data=json.loads(PATH.read_text());user=data['user_id'];identity='disposable-native-review-'+user
        predicate=f'id={literal(user)} AND identity={literal(identity)}'
        match=execute(env,f'SELECT count(*) FROM coach.users WHERE {predicate};')
        if int(json.loads(match['Rows'][0])[0])!=1:raise SystemExit('Disposable identity marker did not match; no data removed')
        goals=f'SELECT id FROM coach.learning_goals WHERE user_id={literal(user)}'
        execute(env,f'''BEGIN;DELETE FROM coach.subjective_reviews WHERE goal_id IN ({goals});
          DELETE FROM coach.subjective_issues WHERE goal_id IN ({goals});DELETE FROM coach.chat_turns WHERE goal_id IN ({goals});
          DELETE FROM coach.voice_jobs WHERE goal_id IN ({goals});DELETE FROM coach.learning_goals WHERE user_id={literal(user)};
          DELETE FROM coach.sessions WHERE user_id={literal(user)};DELETE FROM coach.users WHERE {predicate};COMMIT;''')
        PATH.unlink();print('Disposable native test identity and only its records removed.');return
    if PATH.exists():raise SystemExit('Clean up the existing disposable fixture before creating another')
    store=ManagedStore();user=uuid.uuid4().hex;token=secrets.token_urlsafe(32);hashed=hashlib.sha256(token.encode()).hexdigest()
    store.call('login',{'identity':'disposable-native-review-'+user,'user_id':user,'token_hash':hashed})
    pack=store.pack(os.environ['CONTENT_RELEASE_ID'])['release']
    from apps.api.learning import tutor
    goal=store.call('goal',{'goal_id':uuid.uuid4().hex,'release_id':os.environ['CONTENT_RELEASE_ID'],
        'exam_id':pack['manifest']['id'],'profile':{'daily_minutes':15,'timezone':'Asia/Shanghai','created_at':tutor.now_iso()},
        'state':tutor.new_state(pack['curriculum'],tutor.now_iso())},hashed)['goal_id']
    PATH.write_text(json.dumps({'user_id':user,'session':token,'goal':goal}));PATH.chmod(0o600)
    store.client.close();print('Disposable native session saved privately; no credentials printed.')


if __name__=='__main__':main()
