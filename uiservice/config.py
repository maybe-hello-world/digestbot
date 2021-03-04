"""
Parse configuration variables from env vars and raise Exceptions if needed
"""

from common.config import *

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

# Private messages only
PM_ONLY = os.getenv("PM_ONLY", "False").strip().lower()
PM_ONLY = PM_ONLY == "true"

# App name in slack (important for not answering own messages)
BOT_NAME = os.getenv("BOT_NAME", "digestbot")

# Database service URL
DB_URL = os.getenv("DB_URL", "dbservice:80")

# ODS.ai Q&A system
QNA_REQUEST_URL = os.getenv("QNA_REQUEST_URL", "")
