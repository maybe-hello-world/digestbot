import asyncio
from dataclasses import asdict
from datetime import datetime, timedelta
import json
from logging import Logger
import requests as r

from common.extras import try_request, TimerEncoder
from common.models import Message
from common import Slacker
import crawler.config as config


async def crawl_messages_once(
    slacker: Slacker, logger: Logger
) -> None:
    base_url = f"http://{config.DB_URL}/"

    # get messages and insert them into database
    ch_info = await slacker.get_channels_list()
    if ch_info:
        for ch_id, ch_name in ch_info:
            logger.debug(f"Channel: {ch_name}")

            prev_date = datetime.now() - timedelta(days=config.MESSAGE_DELTA_DAYS)
            messages = await slacker.get_channel_messages(ch_id, prev_date)
            if messages:
                try_request(logger, r.put, base_url + "message",
                            data=json.dumps([asdict(x) for x in messages], cls=TimerEncoder))

        logger.info(
            f"Messages from {len(ch_info)} channels parsed and sent to the database."
        )

    # update messages without permalinks
    answer = try_request(logger, r.get, base_url + "message/linkless")
    if answer.is_err():
        return
    answer = answer.value

    empty_links_messages = [Message(**x) for x in answer.json()]
    if empty_links_messages:
        messages = await slacker.update_permalinks(messages=empty_links_messages)
        answer = try_request(logger, r.patch, base_url + "message/links",
                             data=json.dumps([asdict(x) for x in messages], cls=TimerEncoder))
        if answer.is_ok():
            logger.debug(f"Updated permalinks for {len(messages)} messages.")


async def crawl_messages(slacker: Slacker, logger: Logger):
    while True:
        # wait for next time
        await asyncio.sleep(config.CRAWL_INTERVAL)

        try:
            await crawl_messages_once(slacker=slacker, logger=logger)
        except Exception as e:
            logger.exception(e)
