import sys
import slack
import asyncio
import digestbot.core.UserProcessing.ReqParser as ReqParser
from digestbot.core.SlackAPI.Slacker import Slacker
from digestbot.core.DBEngine.PostgreSQLEngine import PostgreSQLEngine
from digestbot.core.common import config, LoggerFactory
from datetime import datetime, timedelta
import signal


_logger = LoggerFactory.create_logger(__name__, config.LOG_LEVEL)
slacker: Slacker


async def crawl_messages() -> None:
    def write_to_db_mock(anything):
        _logger.info(str(anything) + "\n\n")

    while True:
        # get data
        ch_info = await slacker.get_channels_list()
        for ch_id, ch_name in ch_info:
            _logger.info(f"Channel: {ch_name}")

            day_ago = datetime.now() - timedelta(days=1)
            messages = await slacker.get_channel_messages(ch_id, day_ago)
            write_to_db_mock(messages)

        # wait for next time
        await asyncio.sleep(config.CRAWL_INTERVAL)


@slack.RTMClient.run_on(event="message")
async def handle_message(**payload) -> None:
    """Preprocess messages"""
    global slacker

    if "data" not in payload:
        return None

    data = payload["data"]
    channel = data.get("channel", "")
    is_im = await slacker.is_direct_channel(channel) or False

    message = ReqParser.__UserRequest(
        text=data.get("text", ""),
        user=data.get("user", "") or data.get("username", ""),
        channel=channel,
        ts=data.get("ts", ""),
        is_im=is_im,
    )

    await ReqParser.process_message(
        message=message, bot_name=config.BOT_NAME, api=slacker
    )


if __name__ == "__main__":
    slacker = Slacker(
        user_token=config.SLACK_USER_TOKEN, bot_token=config.SLACK_BOT_TOKEN
    )

    loop = asyncio.get_event_loop()

    # connect to database
    dbEngine = PostgreSQLEngine()
    status = dbEngine.connect_to_database(
        user=config.DB_USER,
        password=config.DB_PASS,
        database_name=config.DB_NAME,
        host=config.DB_HOST,
        port=config.DB_PORT,
    )
    loop.run_until_complete(status)
    if status == 0:
        # TODO: change?
        _logger.error("Could not connect to database. Exiting...")
        sys.exit(1)

    # Instantiate crawler timer with corresponding function
    crawler_task = loop.create_task(crawl_messages())

    # start Real-Time Listener and crawler
    overall_tasks = asyncio.gather(slacker.start_listening(), crawler_task)
    try:
        signal.signal(
            signal.SIGTERM, lambda *args: exec("raise KeyboardInterrupt")
        )  # correct exit handler
        loop.run_until_complete(overall_tasks)
    except KeyboardInterrupt:
        _logger.info("Received exit signal, exiting...")
        dbEngine.close()
        sys.exit(0)
