from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class UserRequest:
    text: str  # user text
    user: str  # author's username
    channel: str  # ID of channel from Slack
    ts: str  # timestamp of the message
    is_im: bool  # is it private message to bot (or in public channel)


def parse_channel_id(channel: str) -> Optional[str]:
    if not channel:
        return None
    split = channel.strip("<>").split("|")
    if len(split) == 2:
        return split[0].lstrip("#")
    return None
