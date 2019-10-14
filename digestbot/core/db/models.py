from dataclasses import dataclass
from typing import List
from decimal import Decimal


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
    link: str
    reactions_rate: int = 0
