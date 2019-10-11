from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    id: int
    username: str
    text: str
    date: datetime
    reply_count: int
    reply_users_count: int
    thread_length: int
    channel_id: str
    reactions_rate: int = 0
