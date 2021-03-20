import asyncio
import json
import requests as r
from datetime import datetime, timedelta
from logging import Logger

from common.LoggerFactory import create_logger
from common.Slacker import Slacker
from common.extras import try_request, TimerEncoder
from common.models import Message
import crawler.config as config
from influxdb_client import Point

from config import INFLUX_API_WRITE


async def crawl_messages_once(slacker: Slacker, logger: Logger) -> None:
    base_url = f"http://{config.DB_URL}/"

    # get messages and insert them into database
    ch_info = await slacker.get_channels_list() or []
    if ch_info:
        for ch_id, ch_name in ch_info:
            logger.debug(f"Channel: {ch_name}")

            prev_date = datetime.now() - timedelta(days=config.MESSAGE_DELTA_DAYS)
            messages = await slacker.get_channel_messages(ch_id, prev_date)
            if messages:
                try_request(logger, r.put, base_url + "message",
                            data=json.dumps([x.dict() for x in messages], cls=TimerEncoder))

        logger.info(
            f"Messages from {len(ch_info)} channels parsed and sent to the database."
        )
    channels_point = Point("workspace").field("channels", len(ch_info)).time(datetime.utcnow())

    # update messages without permalinks
    answer = try_request(logger, r.get, base_url + "message/linkless")
    if answer.is_err():
        return
    answer = answer.value

    empty_links_messages = [Message(**x) for x in answer.json()]
    if empty_links_messages:
        messages = await slacker.update_permalinks(messages=empty_links_messages)
        answer = try_request(logger, r.patch, base_url + "message/links",
                             data=json.dumps([x.dict() for x in messages], cls=TimerEncoder))
        if answer.is_ok():
            logger.debug(f"Updated permalinks for {len(messages)} messages.")
    linkless_messages_point = Point("workspace").field("linkless_messages", len(empty_links_messages)).time(datetime.utcnow())
    INFLUX_API_WRITE([linkless_messages_point, channels_point])


async def crawl_messages(slacker: Slacker, logger: Logger):
    logger.info("Wait for 15 seconds to allow DB services to start...")
    await asyncio.sleep(15)
    logger.info("Starting crawling...")
    while True:
        try:
            await crawl_messages_once(slacker=slacker, logger=logger)
        except Exception as e:
            logger.exception(e)

        # wait for next time
        await asyncio.sleep(config.CRAWL_INTERVAL)


if __name__ == '__main__':
    logger = create_logger("crawler", config.LOG_LEVEL)

    loop = asyncio.get_event_loop()

    slacker = Slacker(
        user_token=config.SLACK_USER_TOKEN,
        bot_token=config.SLACK_BOT_TOKEN,
        logger=logger
    )

    # Instantiate crawler with corresponding function
    crawler_task = loop.create_task(
        crawl_messages(slacker=slacker, logger=logger)
    )

    loop.run_until_complete(crawler_task)
