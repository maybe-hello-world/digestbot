import os
import json
from typing import List
from collections import defaultdict
from digestbot.core.common import LoggerFactory, config

_logger = LoggerFactory.create_logger(__name__, config.LOG_LEVEL)


def get_react_score(reactions: List[dict]) -> float:
    """
    Returns score of the post according to reactions weights.

    :reactions: list of dictionaries containing post info
    """

    react_score = 0

    for react in reactions:
        react_score += reactions_dict[react.get("name", "")] * react.get("count", 0)

    return react_score


# yes, during import time
reactions_dict = defaultdict(lambda: 0)
try:
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__))
    )
    with open(os.path.join(__location__, "reactions_dict.json"), "rt") as f:
        reactions_dict.update(json.load(f))
except json.JSONDecodeError:
    _logger.warning(
        "Improper reactions_dict format - can't parse json. Reaction ranking will be unavailable."
    )
except IOError:
    _logger.warning(
        "Dictionary with reactions is not found. Reaction ranking will be unavailable."
    )
