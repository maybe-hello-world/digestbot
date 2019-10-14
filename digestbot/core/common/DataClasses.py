from dataclasses import dataclass

from digestbot.core.common.Enums import SortingType


@dataclass(frozen=True)
class DBTopRequest:
    amount: int = 10
    channel: str = "all"  # channel (starts with #) or preset (without #) name TODO: change it?
    sorting_type: SortingType = SortingType.REPLIES
