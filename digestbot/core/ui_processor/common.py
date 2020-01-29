import re

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

    # example: <#C6JKNA63|#channel_name>
    channel_id_regexp = r"<#(?P<id>[A-Z\d]+)\|.+>"

    match = re.fullmatch(pattern=channel_id_regexp, string=channel)
    if not match:
        return None
    return match.group("id")
