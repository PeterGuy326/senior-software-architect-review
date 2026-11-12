"""Import the selected model credential from a private local file, never echo it."""
import re
import argparse
from pathlib import Path
from scripts.provision_managed import ROOT,put_env
from apps.api.agent import PROVIDER_ENDPOINTS, VERIFIED_FREE_MODELS


def read_config(source):
    source=Path(source).resolve()
    if not source.is_relative_to((ROOT/'.study/platform').resolve()):
        raise ValueError('Model input must stay in the private project platform directory')
    values={}
    for line in source.read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k,v=line.split('=',1);values[k.strip()]=v.strip().strip('"\'')
    provider=values.get('MODEL_PROVIDER')
    if provider not in PROVIDER_ENDPOINTS or values.get('MODEL_BASE_URL','')!=PROVIDER_ENDPOINTS[provider]:
        raise ValueError('Model provider and official endpoint must match the allowlist')
    if not re.fullmatch(r'[A-Za-z0-9_./-]{3,160}',values.get('MODEL_NAME','')):
        raise ValueError('Enter an exact model ID from the provider catalog')
    if provider=='bigmodel' and values['MODEL_NAME']!='glm-4.7-flash':
        raise ValueError('This integration is restricted to the free glm-4.7-flash model')
    key=values.get('MODEL_API_KEY','')
    if not 20<=len(key)<=512 or re.search(r'\s',key):
        raise ValueError('Enter the API Key locally; its value is never printed')
    free_only=values.get('MODEL_FREE_ONLY','false')
    if free_only not in ('true','false'):
        raise ValueError('MODEL_FREE_ONLY must be true or false')
    if free_only=='true' and values['MODEL_NAME'] not in VERIFIED_FREE_MODELS[provider]:
        raise ValueError('Free-only configuration requires an explicitly verified free model ID')
    return {**{name:values[name] for name in ('MODEL_PROVIDER','MODEL_BASE_URL','MODEL_NAME','MODEL_API_KEY')},
            'MODEL_FREE_ONLY':free_only}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--source',default=str(ROOT/'.study/platform/model-input.env'))
    args=parser.parse_args()
    source=Path(args.source)
    try:
        values=read_config(source)
    except ValueError as e:
        raise SystemExit(str(e))
    for name in ['MODEL_PROVIDER','MODEL_BASE_URL','MODEL_NAME','MODEL_API_KEY','MODEL_FREE_ONLY']:
        put_env(name,values[name])
    source.chmod(0o600)
    print('Selected model configuration imported privately; key not printed.')

if __name__=='__main__':
    main()
