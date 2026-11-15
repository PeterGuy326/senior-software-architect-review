from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .content import EXAM_ID


class Input(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Login(Input):
    code: str = Field(min_length=1, max_length=256)


class GoalInput(Input):
    exam_id: str = EXAM_ID
    release_id: str | None = None
    daily_minutes: int = Field(default=15, ge=1, le=240)
    exam_date: date | None = None


class Answer(Input):
    selected: str = Field(pattern='^[A-F]$')
    confidence: Literal['sure', 'unsure', 'guess'] = 'sure'


class ChatInput(Input):
    request_id: str = Field(pattern='^[a-zA-Z0-9_-]{8,80}$')
    message: str = Field(min_length=1,max_length=2000)


class VoiceInput(Input):
    request_id: str = Field(pattern='^[a-zA-Z0-9_-]{8,80}$')
    audio_base64: str = Field(default='',max_length=700000)
    upload_id: str | None = Field(default=None,pattern='^[a-f0-9]{32}$')
    format: Literal['mp3','wav'] = 'mp3'


class ReviewInput(Input):
    request_id: str = Field(pattern='^[a-zA-Z0-9_-]{8,80}$')
    kind: Literal['case','essay']
    issue_id: str | None = Field(default=None,pattern='^[a-f0-9]{32}$')
    answer: str = Field(default='',max_length=6000)
    filename: str = Field(default='',max_length=160)
    file_base64: str = Field(default='',max_length=2800000)
    upload_id: str | None = Field(default=None,pattern='^[a-f0-9]{32}$')
    prompt: str = Field(default='',max_length=600)
    topic_ref: str | None = Field(default=None,max_length=60,pattern='^essay-[a-z0-9-]+$')
    duration_seconds: int = Field(default=0,ge=0,le=10800)
