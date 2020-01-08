import sys

import slack
import asyncio

import digestbot.core.ui_processor.common
from digestbot.core.internal_processing.crawler import (
    crawl_messages,
    crawl_messages_once,
)
from digestbot.core.internal_processing.timer import (
    timer_processor,
    timers_update_once,
    timers_updater,
)
from digestbot.core.ui_processor.request_parser import process_message
from digestbot.core.slack_api.Slacker import Slacker
from digestbot.core.db.dbengine.PostgreSQLEngine import PostgreSQLEngine
from digestbot.core.common import config, LoggerFactory
import signal
import time

_logger = LoggerFactory.create_logger(__name__, config.LOG_LEVEL)
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

    message = digestbot.core.ui_processor.common.UserRequest(
        text=data.get("text", ""),
        user=data.get("user", "") or data.get("username", ""),
        channel=channel,
        ts=data.get("ts", ""),
        is_im=is_im,
    )

    await process_message(
        message=message, bot_name=config.BOT_NAME, api=slacker, db_engine=db_engine
    )


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    # connect to database
    db_engine = PostgreSQLEngine()

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
        user_token=config.SLACK_USER_TOKEN, bot_token=config.SLACK_BOT_TOKEN
    )

    # initial crawling before starting UI
    loop.run_until_complete(
        crawl_messages_once(slacker=slacker, db_engine=db_engine, logger=_logger)
    )

    # check and update user timers and send users notifications about overdue timers
    loop.run_until_complete(
        timers_update_once(slacker=slacker, db_engine=db_engine, logger=_logger)
    )

    # Instantiate crawler with corresponding function
    crawler_task = loop.create_task(
        crawl_messages(slacker=slacker, db_engine=db_engine, logger=_logger)
    )

    # Instantiate timer processor with corresponding function
    timer_task = loop.create_task(
        timer_processor(slacker=slacker, db_engine=db_engine, logger=_logger)
    )

    # Instantiate timers_updater
    timers_updater_task = loop.create_task(
        timers_updater(slacker=slacker, db_engine=db_engine, logger=_logger)
    )

    # start Real-Time Listener and crawler
    overall_tasks = asyncio.gather(
        slacker.start_listening(), crawler_task, timer_task, timers_updater_task
    )
    try:
        signal.signal(
            signal.SIGTERM, lambda *args: exec("raise KeyboardInterrupt")
        )  # correct exit handler
        loop.run_until_complete(overall_tasks)
    except KeyboardInterrupt:
        # TODO: graceful shutdown doesn't work, need to fix
        _logger.info("Received exit signal, exiting...")
        db_engine.close()
        sys.exit(0)
