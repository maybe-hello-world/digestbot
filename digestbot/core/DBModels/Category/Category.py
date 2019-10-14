from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Category:
    name: str
    channel_ids: List[str]
