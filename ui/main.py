import asyncio

import slack

import config
from common.LoggerFactory import create_logger
from common.Slacker import Slacker
from timer import update_timers_once, process_timers, update_timers
from ui_processor.common import UserRequest
from ui_processor.request_parser import process_message

_logger = create_logger("UI", config.LOG_LEVEL)
slacker: Slacker


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
        message=message, bot_name=config.BOT_NAME, api=slacker, db_service="dbservice:80"
    )

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    db_service = "dbservice:80"

    slacker = Slacker(
        user_token=config.SLACK_USER_TOKEN,
        bot_token=config.SLACK_BOT_TOKEN,
        logger=create_logger("UI_slacker", config.LOG_LEVEL)
    )

    loop.run_until_complete(
        update_timers_once(slacker=slacker, db_service=db_service, logger=_logger)
    )

    # Instantiate timer processor with corresponding function
    timer_task = loop.create_task(
        process_timers(slacker=slacker, db_service=db_service, logger=_logger)
    )

    # Instantiate timers_updater
    timers_updater_task = loop.create_task(
        update_timers(slacker=slacker, db_service=db_service, logger=_logger)
    )

    # start Real-Time Listener and crawler
    overall_tasks = asyncio.gather(
        slacker.start_listening(),
        timer_task,
        timers_updater_task
    )

    loop.run_until_complete(overall_tasks)
