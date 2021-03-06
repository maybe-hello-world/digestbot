from datetime import timedelta, datetime

from pydantic import BaseModel, Field
from typing import Optional

from common.models import Category, Message, Timer


# noinspection PyRedeclaration
class Category(Category, BaseModel):
    username: Optional[str] = None


# noinspection PyRedeclaration
class Message(Message, BaseModel):
    reply_count: int = Field(..., ge=0)
    reply_users_count: int = Field(..., ge=0)
    thread_length: int = Field(..., ge=0)
    link: Optional[str] = None


# noinspection PyRedeclaration
class Timer(Timer, BaseModel):
    @classmethod
    def from_fastapi_dict(cls, timer_dict: dict) -> Timer:
        timer_dict['delta'] = timedelta(seconds=timer_dict['delta'])
        timer_dict['next_start'] = datetime.fromisoformat(timer_dict['next_start'])
        return cls(**timer_dict)
