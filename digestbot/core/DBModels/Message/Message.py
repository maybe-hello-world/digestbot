from dataclasses import dataclass
from decimal import Decimal


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
