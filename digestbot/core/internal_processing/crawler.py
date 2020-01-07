import asyncio
from datetime import datetime, timedelta
from logging import Logger

from digestbot.core.common import config
from digestbot.core.db.dbengine.PostgreSQLEngine import PostgreSQLEngine
from digestbot.core.db.dbrequest.message import (
    upsert_messages,
    get_messages_without_links,
    update_message_links,
)
from digestbot.core.slack_api import Slacker


async def crawl_messages_once(
    slacker: Slacker, logger: Logger, db_engine: PostgreSQLEngine
) -> None:
    # get messages and insert them into database
    ch_info = await slacker.get_channels_list()
    if ch_info:
        for ch_id, ch_name in ch_info:
            logger.debug(f"Channel: {ch_name}")

            prev_date = datetime.now() - timedelta(days=config.MESSAGE_DELTA_DAYS)
            messages = await slacker.get_channel_messages(ch_id, prev_date)
            if messages:
                await upsert_messages(db_engine=db_engine, messages=messages)
            logger.debug(str(messages))
        logger.info(
            f"Messages from {len(ch_info)} channels parsed and sent to the database."
        )

    # update messages without permalinks
    req_status, empty_links_messages = await get_messages_without_links(
        db_engine=db_engine
    )
    if req_status and empty_links_messages:
        messages = await slacker.update_permalinks(messages=empty_links_messages)
        await update_message_links(db_engine=db_engine, messages=messages)
        logger.debug(f"Updated permalinks for {len(messages)} messages.")


async def crawl_messages(slacker: Slacker, logger: Logger, db_engine: PostgreSQLEngine):
    while True:
        await crawl_messages_once(slacker=slacker, logger=logger, db_engine=db_engine)

        # wait for next time
        await asyncio.sleep(config.CRAWL_INTERVAL)
