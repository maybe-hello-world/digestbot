from enum import Enum, unique


@unique
class SortingType(Enum):
    """Sorting type for database"""

    REPLIES = "reply_count"
    LENGTH = "thread_length"
    REACTIONS = "reactions_rate"

# TODO: remove duplication
