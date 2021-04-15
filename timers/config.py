import logging
import os
from common.LoggerFactory import create_logger as _create_logger
from common.config import *

_logger = _create_logger(__name__, logging.WARNING)

# how much time is allowed to miss and not count and overdue timer
OVERDUE_MINUTES = os.getenv("OVERDUE_MINUTES", "10")
try:
    OVERDUE_MINUTES = int(OVERDUE_MINUTES)
except ValueError:
    _logger.warning(
        f"Could not parse overdue minutes value: {OVERDUE_MINUTES}, default value 10 is used."
    )
    OVERDUE_MINUTES = 10
