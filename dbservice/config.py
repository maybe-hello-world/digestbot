"""
Parse configuration variables from env vars and raise Exceptions if needed
"""

import os
import logging
from common.LoggerFactory import create_logger as _create_logger
from common.config import *

_logger = _create_logger(__name__, logging.WARNING)

# Database settings
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "postgres")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", 5432)
try:
    DB_PORT = int(DB_PORT)
except ValueError:
    _logger.warning(
        f"Could not parse DB_PORT: f{DB_PORT}, default value '5432' is used."
    )
    DB_PORT = 5432

# how many timers are available for each user
TIMERS_LIMIT = os.getenv("TIMERS_LIMIT", "5")
try:
    TIMERS_LIMIT = int(TIMERS_LIMIT)
except ValueError:
    _logger.warning(
        f"Could not parse timers limit value: {TIMERS_LIMIT}, default value 5 is used."
    )
    TIMERS_LIMIT = 5

PRESETS_LIMIT = os.getenv("PRESETS_LIMIT", "20")
try:
    PRESETS_LIMIT = int(PRESETS_LIMIT)
except ValueError:
    _logger.warning(
        f"Could not parse presets limit value: {PRESETS_LIMIT}, default value 20 is used."
    )
    PRESETS_LIMIT = 20

IGNORE_LIMIT = os.getenv("IGNORE_LIMIT", "100")
try:
    IGNORE_LIMIT = int(IGNORE_LIMIT)
except ValueError:
    _logger.warning(
        f"Could not parse ignore limit value: {IGNORE_LIMIT}, default value 100 is used."
    )
    IGNORE_LIMIT = 100
