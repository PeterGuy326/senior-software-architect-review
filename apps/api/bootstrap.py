"""Development deployment bootstrap. Never falls back to local storage."""
import os

from sqlalchemy import text

from .content import compile_pack, publish
from .db import make_engine, migrate


def main():
    if os.getenv('APP_ENV') not in {'development', 'production'}:
        raise RuntimeError('Use npm run api:dev for local development')
    managed = os.getenv('STORAGE_TRANSPORT') == 'cloudbase_rpc'
    required = (['TCB_ENV_ID','CLOUDBASE_SERVER_KEY','CONTENT_RELEASE_ID'] if managed else
                ['DATABASE_URL','WECHAT_APP_ID','WECHAT_APP_SECRET','CONTENT_RELEASE_ID'])
    for key in required:
        if not os.getenv(key):
            raise RuntimeError(f'Missing deployment setting: {key}')
    if not managed and not os.environ['DATABASE_URL'].startswith('postgresql'):
        raise RuntimeError('Cloud deployment requires PostgreSQL')
    release_id, _ = compile_pack()
    if os.environ['CONTENT_RELEASE_ID'] != release_id:
        raise RuntimeError('Content release does not match the deployed source')
    if managed:
        from .managed import ManagedStore
        if not ManagedStore().call('health',{'release_id':release_id}).get('ready'):
            raise RuntimeError('Managed content release is not ready')
    else:
        engine = make_engine()
        # Dedicated connection holds a lock while first-boot DDL/publication runs.
        with engine.connect() as lock:
            lock.execute(text('SELECT pg_advisory_lock(7350911)'))
            try:
                migrate(engine)
                publish(engine)
            finally:
                lock.execute(text('SELECT pg_advisory_unlock(7350911)'))
    import uvicorn
    uvicorn.run('apps.api.main:app', host='0.0.0.0', port=int(os.getenv('PORT', '8080')))


if __name__ == '__main__':
    main()
