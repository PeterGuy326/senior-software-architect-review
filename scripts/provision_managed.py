"""Provision the fixed RPC and a backend-only expiring key without printing it."""
import json
import os
import re
import subprocess
from pathlib import Path

from apps.api.db import ROOT
from scripts.publish_cloud_content import execute


def put_env(key, value):
    path = ROOT / '.env'
    content = path.read_text() if path.exists() else ''
    line = f'{key}={value}'
    if re.search(rf'^{key}=.*$',content,re.M):
        content = re.sub(rf'^{key}=.*$',lambda _:line,content,flags=re.M)
    else:
        content = content.rstrip() + '\n' + line + '\n'
    path.write_text(content)
    path.chmod(0o600)


def load_env():
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text().splitlines():
            match = re.match(r'^([A-Z_][A-Z0-9_]*)=(.*)$',line)
            if match and not os.getenv(match[1]):
                os.environ[match[1]] = match[2].strip('"\'')


def find_key(value):
    if isinstance(value,dict):
        for k,v in value.items():
            if isinstance(v,str) and k.lower() in {'apikey','api_key','key','token'} and len(v)>80:
                return v
        for v in value.values():
            result = find_key(v)
            if result:
                return result
    return None


def main():
    load_env()
    env = os.environ['TCB_ENV_ID']
    if env != 'wuji-coach-dev-d4gtwqert85ce3eae':
        raise SystemExit('Only the selected development environment is supported')
    migration = ROOT / 'cloudbase/migrations/20261101220000_managed_rpc.sql'
    execute(env,migration.read_text())
    key = os.getenv('CLOUDBASE_SERVER_KEY')
    if not key:
        result = subprocess.run([str(ROOT/'node_modules/.bin/tcb'),'env','apikey','create',
            'wuji-api-dev','-e',env,'--type','api_key','--expire','2592000','--json'],
            cwd=ROOT,text=True,capture_output=True)
        if result.returncode:
            raise SystemExit('Backend key provisioning failed; credentials not printed')
        data = json.loads(result.stdout)
        private = ROOT / '.study/platform/server-key.json'
        private.write_text(json.dumps(data))
        private.chmod(0o600)
        key = find_key(data)
        if not key:
            raise SystemExit('Key saved privately but its response format needs inspection; top-level fields: '+','.join(data.keys()))
        put_env('CLOUDBASE_SERVER_KEY',key)
    put_env('STORAGE_TRANSPORT','cloudbase_rpc')
    print('Fixed backend RPC provisioned; server key saved only in private local configuration.')


if __name__ == '__main__':
    main()
