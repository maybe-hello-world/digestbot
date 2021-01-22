import asyncio
import time

import slack
import sys

import config
from common.LoggerFactory import create_logger
from common.Slacker import Slacker
from common.db.dbengine.PostgreSQLEngine import PostgreSQLEngine
from ui_processor.common import UserRequest
from ui_processor.request_parser import process_message

_logger = create_logger("UI", config.LOG_LEVEL)
slacker: Slacker
db_engine: PostgreSQLEngine


@slack.RTMClient.run_on(event="message")
async def handle_message(**payload) -> None:
    """Preprocess messages"""
    global slacker

    if "data" not in payload:
        return None

    data = payload["data"]
    channel = data.get("channel", "")
    is_im = await slacker.is_direct_channel(channel) or False
    if config.PM_ONLY and not is_im:
        return None

    message = UserRequest(
        text=data.get("text", ""),
        user=data.get("user", "") or data.get("username", ""),
        channel=channel,
        ts=data.get("ts", ""),
        is_im=is_im,
    )

    await process_message(
        message=message, bot_name=config.BOT_NAME, api=slacker, db_engine=db_engine
    )

if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    # connect to database
    db_engine = PostgreSQLEngine(logger=create_logger("UI_PostreSQLEngine", config.LOG_LEVEL))

    connected = False
    for i in range(5):
        connection = db_engine.connect_to_database(
            user=config.DB_USER,
            password=config.DB_PASS,
            database_name=config.DB_NAME,
            host=config.DB_HOST,
            port=config.DB_PORT,
        )
        status = loop.run_until_complete(connection)
        if status != 0:
            connected = True
            break
        time.sleep(3)

    if not connected:
        _logger.error("Could not connect to database after 5 attempts. Exiting...")
        sys.exit(1)

    slacker = Slacker(
        user_token=config.SLACK_USER_TOKEN,
        bot_token=config.SLACK_BOT_TOKEN,
        logger=create_logger("UI_slacker", config.LOG_LEVEL)
    )

    loop.run_until_complete(slacker.start_listening())
