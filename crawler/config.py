"""
Parse configuration variables from env vars and raise Exceptions if needed
"""

import os
import logging
from common.LoggerFactory import create_logger as _create_logger
from common.config import *

_logger = _create_logger(__name__, logging.WARNING)

# User token for message access
SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN", None)
if SLACK_USER_TOKEN is None:
    raise Exception("SLACK_USER_TOKEN is not provided.")

# Bot token for bot access (post to channels etc)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", None)
if SLACK_BOT_TOKEN is None:
    raise Exception("SLACK_BOT_TOKEN is not provided.")

# How often to crawl messages from chats
CRAWL_INTERVAL = os.getenv("CRAWL_INTERVAL", "900")
try:
    CRAWL_INTERVAL = int(CRAWL_INTERVAL)
except ValueError:
    _logger.warning(
        f"Could not parse crawl interval: f{CRAWL_INTERVAL}, default value 900 seconds is used."
    )
    CRAWL_INTERVAL = 900

# what oldest messages to get (in days)
MESSAGE_DELTA_DAYS = os.getenv("MESSAGE_DELTA_DAYS", "1")
try:
    MESSAGE_DELTA_DAYS = int(MESSAGE_DELTA_DAYS)
except ValueError:
    _logger.warning(
        f"Could not parse message delta interval: f{MESSAGE_DELTA_DAYS}, default value 1 is used."
    )
    MESSAGE_DELTA_DAYS = 1

# Database service URL
DB_URL = os.getenv("DB_URL", "dbservice:80")
