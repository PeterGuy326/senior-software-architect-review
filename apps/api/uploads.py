"""Short-lived bounded RAM uploads for WeChat's small request envelopes."""
import math
import threading
import time
import uuid
from typing import Literal

from fastapi import Header,HTTPException
from pydantic import Field

from .contracts import Input

CHUNK_CHARS=64000


class UploadStart(Input):
    request_id: str=Field(pattern='^[a-zA-Z0-9_-]{8,80}$')
    purpose: Literal['essay','voice']
    filename: str=Field(min_length=1,max_length=160)
    byte_size: int=Field(ge=1,le=2*1024*1024)


class UploadChunk(Input):
    index: int=Field(ge=0,le=43)
    data: str=Field(min_length=1,max_length=CHUNK_CHARS,pattern='^[A-Za-z0-9+/=]+$')


class EphemeralUploads:
    def __init__(self):
        self.items={};self.lock=threading.Lock()

    def expire(self,upload_id):
        with self.lock:self.items.pop(upload_id,None)

    def start(self,goal,owner,body):
        if body.purpose=='voice' and body.byte_size>512*1024:
            raise HTTPException(413,'录音较大，请分段说。')
        with self.lock:
            for key in list(self.items):
                if self.items[key]['expires']<time.monotonic():self.items.pop(key)
            for upload_id,item in self.items.items():
                if item['goal']==goal and item['request_id']==body.request_id:
                    if (item['purpose'],item['filename'],item['size'])!=(body.purpose,body.filename,body.byte_size):
                        raise HTTPException(409,'原上传内容不能改写，请重新选择文件。')
                    # The caller has just revalidated goal ownership; allow normal
                    # session refresh without retaining access for the old token.
                    item['owner']=owner
                    return {'upload_id':upload_id,'chunk_chars':CHUNK_CHARS}
            if len(self.items)>=8:raise HTTPException(429,'当前上传较多，请稍后重试。')
            upload_id=uuid.uuid4().hex
            self.items[upload_id]={'goal':goal,'owner':owner,'request_id':body.request_id,
                'purpose':body.purpose,'filename':body.filename,'size':body.byte_size,'chunks':{},
                'encoded_size':4*math.ceil(body.byte_size/3),'expires':time.monotonic()+300}
        timer=threading.Timer(300,self.expire,args=(upload_id,));timer.daemon=True;timer.start()
        with self.lock:
            if upload_id in self.items:self.items[upload_id]['timer']=timer
        return {'upload_id':upload_id,'chunk_chars':CHUNK_CHARS}

    def owned(self,upload_id,goal,owner):
        item=self.items.get(upload_id)
        if not item or item['goal']!=goal or item['owner']!=owner or item['expires']<time.monotonic():
            raise HTTPException(404,'上传已中断或过期，点重试会重新上传。')
        return item

    def put(self,upload_id,goal,owner,body):
        with self.lock:
            item=self.owned(upload_id,goal,owner)
            offset=body.index*CHUNK_CHARS
            if offset>=item['encoded_size'] or len(body.data)!=min(CHUNK_CHARS,item['encoded_size']-offset):
                raise HTTPException(422,'文件分片不完整，请重试。')
            if body.index in item['chunks'] and item['chunks'][body.index]!=body.data:
                raise HTTPException(409,'原上传内容不能改写。')
            item['chunks'][body.index]=body.data
        return {'ok':True}

    def take(self,upload_id,goal,owner,request_id,purpose,filename=None):
        with self.lock:
            item=self.owned(upload_id,goal,owner)
            if item['request_id']!=request_id or item['purpose']!=purpose or (filename is not None and item['filename']!=filename):
                raise HTTPException(409,'文件与当前提交不匹配。')
            count=math.ceil(item['encoded_size']/CHUNK_CHARS)
            if len(item['chunks'])!=count:raise HTTPException(422,'文件尚未传完整，请重试。')
            encoded=''.join(item['chunks'][i] for i in range(count))
            self.items.pop(upload_id)
            if item.get('timer'):item['timer'].cancel()
        return encoded


def install_upload_routes(app,store,token_hash,uploads):
    @app.post('/v1/goals/{goal_id}/uploads')
    def start_upload(goal_id: str,body: UploadStart,authorization: str | None=Header(default=None)):
        owner=token_hash(authorization)
        store.call('status',{'goal_id':goal_id},owner)
        return uploads.start(goal_id,owner,body)

    @app.post('/v1/goals/{goal_id}/uploads/{upload_id}/chunks')
    def upload_chunk(goal_id: str,upload_id: str,body: UploadChunk,authorization: str | None=Header(default=None)):
        return uploads.put(upload_id,goal_id,token_hash(authorization),body)
