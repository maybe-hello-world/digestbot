from enum import Enum, unique

# TODO: fix it
# TODO: maybe https://stackoverflow.com/questions/37183612/how-to-define-a-mapping-of-enum-members-in-the-enum-type?
SORTING_TYPE_MAPPER = {
    "replies": "reply_count",
    "length": "thread_length",
    "reactions": "reactions_rate",
}


@unique
class SortingType(Enum):
    """Sorting type for database"""

    REPLIES = "reply_count"
    LENGTH = "thread_length"
    REACTIONS = "reactions_rate"
