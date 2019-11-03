from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal

from datetime import timedelta, datetime


@dataclass(frozen=True)
class Category:
    name: str
    channel_ids: List[str]


@dataclass(frozen=True)
class Message:
    username: str
    text: str
    timestamp: Decimal
    reply_count: int
    reply_users_count: int
    thread_length: int
    channel_id: str
    link: Optional[str]
    reactions_rate: float = 0.0


@dataclass(frozen=True)
class Timer:
    channel_id: str
    timer_name: str
    delta: timedelta
    next_start: datetime
    top_command: str
