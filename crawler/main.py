import asyncio
import config

from common.LoggerFactory import create_logger
from common.Slacker import Slacker

from crawler.crawl_engine import crawl_messages

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
