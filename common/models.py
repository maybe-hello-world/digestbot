from pydantic import BaseModel
from typing import List, Optional

from datetime import timedelta, datetime


class Preset(BaseModel):
    id: int
    name: str
    channel_ids: List[str]
    username: Optional[str]


class Message(BaseModel):
    username: str
    text: str
    timestamp: str
    channel_id: str
    reply_count: int
    reply_users_count: int
    thread_length: int
    link: Optional[str]
    reactions_rate: float = 0.0


class Timer(BaseModel):
    channel_id: str
    username: str
    timer_name: str
    delta: timedelta
    next_start: datetime
    top_command: str
