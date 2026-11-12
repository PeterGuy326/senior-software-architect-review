"""Short audio -> editable draft. No audio files, URLs or arbitrary model IDs."""
import base64
import hashlib
import io
import os
import re
import wave

import httpx
from fastapi import HTTPException
from mutagen.mp3 import MP3

MAX_AUDIO_BYTES=512*1024
ASR_MODEL='XingChenAGI/XingChenASR-V3.2-Ultra'


def decode_audio(body):
    try:
        audio=base64.b64decode(body.audio_base64,validate=True)
        if not 100<=len(audio)<=MAX_AUDIO_BYTES:
            raise ValueError('size')
        if body.format=='wav':
            with wave.open(io.BytesIO(audio),'rb') as source:
                rate=source.getframerate()
                if source.getnchannels() not in (1,2) or not 8000<=rate<=48000:
                    raise ValueError('wave format')
                duration=source.getnframes()/rate
                if source.getnframes()*source.getnchannels()*source.getsampwidth()>len(audio):
                    raise ValueError('incomplete wave')
        else:
            info=MP3(io.BytesIO(audio)).info
            duration=info.length
        if not 0.5<=duration<=61:
            raise ValueError('duration')
    except Exception:
        # Parser exceptions never include the uploaded bytes in the response.
        raise HTTPException(422,'录音格式不正确，或时长不在 0.5–60 秒内，请重新录制') from None
    return audio,hashlib.sha256(audio).hexdigest(),round(duration,2)


class SpeechProvider:
    def __init__(self):
        self.key=os.getenv('ASR_API_KEY') or (os.getenv('MODEL_API_KEY','') if os.getenv('MODEL_PROVIDER')=='siliconflow' else '')

    def transcribe(self,audio,format):
        if not self.key:
            raise HTTPException(503,'语音转写暂未就绪，请先打字输入')
        try:
            response=httpx.post('https://api.siliconflow.cn/v1/audio/transcriptions',
                headers={'Authorization':'Bearer '+self.key},data={'model':ASR_MODEL},
                files={'file':('recording.'+format,audio,'audio/mpeg' if format=='mp3' else 'audio/wav')},timeout=35)
            response.raise_for_status()
            text=response.json()['text']
            if not isinstance(text,str):
                raise ValueError('text')
            text=re.sub(r'<\|[^>]*\|>','',text).strip()
        except (httpx.HTTPError,ValueError,KeyError,TypeError):
            raise HTTPException(503,'语音暂时没转出来，录音还在，可以重试') from None
        if not text:
            raise HTTPException(422,'没有听清内容，请靠近麦克风重新录制')
        if len(text)>2000:
            raise HTTPException(422,'这段话比较长，请分成两段录制')
        return text
