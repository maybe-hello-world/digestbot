"""
Parse configuration variables from env vars and raise Exceptions if needed
"""

import os
import logging
from common.LoggerFactory import create_logger as _create_logger

_logger = _create_logger(__name__, logging.WARNING)

SIGNING_SECRET = os.getenv("SIGNING_SECRET", None)
if SIGNING_SECRET is None:
    raise Exception("SIGNING_SECRET is not provided.")

# User token for message access
SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN", None)
if SLACK_USER_TOKEN is None:
    raise Exception("SLACK_USER_TOKEN is not provided.")

# Bot token for bot access (post to channels etc)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", None)
if SLACK_BOT_TOKEN is None:
    raise Exception("SLACK_BOT_TOKEN is not provided.")

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

# App name in slack (important for not answering own messages)
BOT_NAME = os.getenv("BOT_NAME", "digestbot")

# Database service URL
DB_URL = os.getenv("DB_URL", "dbservice:80")
