from dataclasses import dataclass
from typing import Optional
from digestbot.core.common.Enums import SortingType
from decimal import Decimal


# TODO: make similar to digestbot/app/dbrequest/message.py/get_top_*_messages signature
@dataclass(frozen=True)
class DBTopRequest:
    after_ts: Decimal
    amount: int = 5
    is_channel: bool = True
    channel: Optional[str] = None  # channel (starts with #) or preset (without #) name
    sorting_type: SortingType = SortingType.REPLIES
