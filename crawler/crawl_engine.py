import asyncio
from datetime import datetime, timedelta
import json
from logging import Logger
import requests as r

from common.models import Message
from common import Slacker
import crawler.config as config


async def crawl_messages_once(
    slacker: Slacker, logger: Logger, db_service: str
) -> None:
    base_url = f"http://{db_service}/"

    # get messages and insert them into database
    ch_info = await slacker.get_channels_list()
    if ch_info:
        for ch_id, ch_name in ch_info:
            logger.debug(f"Channel: {ch_name}")

            prev_date = datetime.now() - timedelta(days=config.MESSAGE_DELTA_DAYS)
            messages = await slacker.get_channel_messages(ch_id, prev_date)
            if messages:
                answer = r.put(base_url + "message", data=json.dumps(messages), timeout=10)
                if answer.status_code != 200:
                    logger.error(answer.text)
            logger.debug(len(messages))
        logger.info(
            f"Messages from {len(ch_info)} channels parsed and sent to the database."
        )

    # update messages without permalinks
    answer = r.get(base_url + "message/linkless", timeout=10)
    if answer.status_code != 200:
        logger.error(answer.text)
        return

    empty_links_messages = [Message(**x) for x in answer.json()]
    if empty_links_messages:
        messages = await slacker.update_permalinks(messages=empty_links_messages)
        answer = r.patch(base_url + "message/links", data=json.dumps(messages), timeout=10)
        if answer.status_code != 200:
            logger.error(answer.text)
        else:
            logger.debug(f"Updated permalinks for {len(messages)} messages.")


async def crawl_messages(slacker: Slacker, logger: Logger, db_service: str):
    while True:
        # wait for next time
        await asyncio.sleep(config.CRAWL_INTERVAL)

        try:
            await crawl_messages_once(slacker=slacker, logger=logger, db_service=db_service)
        except Exception as e:
            logger.exception(e)
