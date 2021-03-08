from datetime import timedelta, datetime
from pydantic import Field
from typing import Optional

from common.models import Preset, Message, Timer


# noinspection PyRedeclaration
class Preset(Preset):
    username: Optional[str] = None


# noinspection PyRedeclaration
class Message(Message):
    reply_count: int = Field(..., ge=0)
    reply_users_count: int = Field(..., ge=0)
    thread_length: int = Field(..., ge=0)
    link: Optional[str] = None


# noinspection PyRedeclaration
class Timer(Timer):
    pass
