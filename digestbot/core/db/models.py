from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal


@dataclass(frozen=True)
class Category:
    id: int
    username: Optional[str]
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
