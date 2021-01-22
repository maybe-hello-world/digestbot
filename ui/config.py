"""
Parse configuration variables from env vars and raise Exceptions if needed
"""

import os
import logging
from common.LoggerFactory import create_logger as _create_logger


_logger = _create_logger(__name__, logging.WARNING)



# User token for message access
SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN", None)
if SLACK_USER_TOKEN is None:
    raise Exception("SLACK_USER_TOKEN is not provided.")


# Bot token for bot access (post to channels etc)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", None)
if SLACK_BOT_TOKEN is None:
    raise Exception("SLACK_BOT_TOKEN is not provided.")


# App name in slack (important for not answering own messages)
BOT_NAME = os.getenv("BOT_NAME", "digestbot")


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

# Private messages only
PM_ONLY = os.getenv("PM_ONLY", "False").strip().lower()
PM_ONLY = PM_ONLY == "true"


PRESETS_LIMIT = os.getenv("PRESETS_LIMIT", "20")
try:
    PRESETS_LIMIT = int(PRESETS_LIMIT)
except ValueError:
    _logger.warning(
        f"Could not parse presets limit value: {PRESETS_LIMIT}, default value 20 is used."
    )
    PRESETS_LIMIT = 20

# how many timers are available for each user
TIMERS_LIMIT = os.getenv("TIMERS_LIMIT", "5")
try:
    TIMERS_LIMIT = int(TIMERS_LIMIT)
except ValueError:
    _logger.warning(
        f"Could not parse timers limit value: {TIMERS_LIMIT}, default value 5 is used."
    )
    TIMERS_LIMIT = 5