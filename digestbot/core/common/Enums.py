from enum import Enum, unique


@unique
class SortingType(Enum):
    """Sorting type for database"""

    REPLIES = "replies"
    LENGTH = "length"
    REACTIONS = "reactions"
