import asyncio
import config
import sys
import time

from common.LoggerFactory import create_logger
from common.db.dbengine.PostgreSQLEngine import PostgreSQLEngine
from common.Slacker import Slacker

from crawler.crawl_engine import crawl_messages

if __name__ == '__main__':
    _logger = create_logger("crawler", config.LOG_LEVEL)

    loop = asyncio.get_event_loop()

    # connect to database
    db_engine = PostgreSQLEngine(create_logger("PostgreSQLEngine_crawler", config.LOG_LEVEL))

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
        logger=create_logger("Slacker_crawler", config.LOG_LEVEL)
    )

    # Instantiate crawler with corresponding function
    crawler_task = loop.create_task(
        crawl_messages(slacker=slacker, db_engine=db_engine, logger=_logger)
    )

    loop.run_until_complete(crawler_task)
