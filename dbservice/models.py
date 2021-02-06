from datetime import timedelta, datetime
from pydantic import BaseModel, Field
from typing import Optional

from common.models import Category, Message, Timer


class Category(Category, BaseModel):
    username: Optional[str] = None


class Message(Message, BaseModel):
    reply_count: int = Field(..., ge=0)
    reply_users_count: int = Field(..., ge=0)
    thread_length: int = Field(..., ge=0)
    link: Optional[str] = None


class Timer(Timer, BaseModel):
    channel_id: str
    username: str
    timer_name: str
    delta: timedelta
    next_start: datetime
    top_command: str
