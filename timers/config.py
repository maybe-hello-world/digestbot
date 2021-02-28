import logging
import os
from common.LoggerFactory import create_logger as _create_logger

_logger = _create_logger(__name__, logging.WARNING)

# Log level
__available_log_levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").lower()
if LOG_LEVEL not in __available_log_levels:
    _logger.warning(
        f"Could not parse log level: f{LOG_LEVEL}, default value 'info' is used."
    )
    LOG_LEVEL = "info"
LOG_LEVEL = __available_log_levels[LOG_LEVEL]

# how much time is allowed to miss and not count and overdue timer
OVERDUE_MINUTES = os.getenv("OVERDUE_MINUTES", "10")
try:
    OVERDUE_MINUTES = int(OVERDUE_MINUTES)
except ValueError:
    _logger.warning(
        f"Could not parse overdue minutes value: {OVERDUE_MINUTES}, default value 10 is used."
    )
    OVERDUE_MINUTES = 10
