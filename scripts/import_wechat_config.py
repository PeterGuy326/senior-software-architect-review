"""Import locally entered WeChat credentials without echoing their values."""
import os
import re
from pathlib import Path

from apps.api.db import ROOT
from scripts.provision_managed import load_env, put_env


def main():
    load_env()
    source = ROOT / '.study/platform/wechat-input.env'
    if not source.exists():
        raise SystemExit('Missing private input file: .study/platform/wechat-input.env')
    values = {}
    for line in source.read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k,v=line.split('=',1)
            values[k.strip()] = v.strip().strip('"\'')
    if values.get('WECHAT_APP_ID') != os.environ.get('WECHAT_APP_ID'):
        raise SystemExit('AppID must match the selected Mini Program')
    secret = values.get('WECHAT_APP_SECRET','')
    if not re.fullmatch(r'[A-Za-z0-9]{32}',secret):
        raise SystemExit('Enter the 32-character AppSecret locally; its value is never printed')
    key = values.get('MINIPROGRAM_PRIVATE_KEY_PATH','')
    if key:
        if os.name != 'nt' and re.match(r'^[A-Za-z]:[\\/]',key):
            key='/mnt/'+key[0].lower()+'/'+key[3:].replace('\\','/')
        path=Path(key).expanduser().resolve()
        if not path.is_file() or path.is_relative_to(ROOT):
            raise SystemExit('Upload key must be an existing file outside this repository')
        put_env('MINIPROGRAM_PRIVATE_KEY_PATH',str(path))
    put_env('WECHAT_APP_SECRET',secret)
    source.chmod(0o600)
    print('WeChat credential imported into private server configuration; no credential value printed.')


if __name__=='__main__':
    main()
