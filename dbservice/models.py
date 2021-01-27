from typing import List, Optional
from decimal import Decimal
from datetime import timedelta, datetime

from pydantic import BaseModel, Field


class Category(BaseModel):
    id: int
    username: Optional[str] = None
    name: str
    channel_ids: List[str]


class Message(BaseModel):
    username: str
    text: str
    timestamp: Decimal
    reply_count: int = Field(..., ge=0)
    reply_users_count: int = Field(..., ge=0)
    thread_length: int = Field(..., ge=0)
    channel_id: str
    link: Optional[str] = None
    reactions_rate: float = 0.0


class Timer(BaseModel):
    channel_id: str
    username: str
    timer_name: str
    delta: timedelta
    next_start: datetime
    top_command: str
