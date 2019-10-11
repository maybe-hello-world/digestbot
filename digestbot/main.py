import os
import sys
import slack
import asyncio
import digestbot.core.UserProcessing.ReqParser as ReqParser
from digestbot.core.SlackAPI.Slacker import Slacker
from digestbot.core.DBEngine.PostgreSQLEngine import PostgreSQLEngine
from datetime import datetime, timedelta
import logging
import signal


__logger: logging.Logger
slacker: Slacker
CRAWL_INTERVAL: int = 60 * 15  # in seconds
bot_name: str


async def crawl_messages() -> None:
    def write_to_db_mock(anything):
        __logger.info(str(anything) + "\n\n")

    while True:
        # get data
        ch_info = await slacker.get_channels_list()
        for ch_id, ch_name in ch_info:
            __logger.info(f"Channel: {ch_name}")

            day_ago = datetime.now() - timedelta(days=1)
            messages = await slacker.get_channel_messages(ch_id, day_ago)
            write_to_db_mock(messages)

        # wait for next time
        await asyncio.sleep(CRAWL_INTERVAL)


@slack.RTMClient.run_on(event="message")
async def handle_message(**payload) -> None:
    """Preprocess messages"""
    global bot_name, slacker

    if "data" not in payload:
        return None

    data = payload["data"]
    channel = data.get("channel", "")
    is_im = await slacker.is_direct_channel(channel) or False

    message = ReqParser.UserRequest(
        text=data.get("text", ""),
        user=data.get("user", "") or data.get("username", ""),
        channel=channel,
        ts=data.get("ts", ""),
        is_im=is_im,
    )

    await ReqParser.process_message(message=message, bot_name=bot_name, api=slacker)


def set_logger():
    global __logger
    __logger = logging.getLogger("root")
    __logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%m.%d.%Y-%I:%M:%S",
    )
    handler.setFormatter(formatter)
    __logger.addHandler(handler)


if __name__ == "__main__":
    set_logger()

    user_token = os.environ["SLACK_USER_TOKEN"]
    bot_token = os.environ["SLACK_BOT_TOKEN"]

    bot_name = os.environ.get("bot_name", "digest-bot")
    slacker = Slacker(user_token=user_token, bot_token=bot_token)

    loop = asyncio.get_event_loop()

    # connect to database
    dbEngine = PostgreSQLEngine()
    status = dbEngine.connect_to_database(
        user=os.environ.get("DB_USER", "postgres"),
        password=os.environ.get("DB_PASSWORD", "postgres"),
        database_name=os.environ.get("DB_NAME", "postgres"),
        host=os.environ.get("DB_HOST", "postgres"),
        port=os.environ.get("DB_PORT", None)
    )
    loop.run_until_complete(status)
    if status == 0:
        # TODO: change?
        __logger.error("Could not connect to database. Exiting...")
        sys.exit(1)

    # Instantiate crawler timer with corresponding function
    crawler_task = loop.create_task(crawl_messages())

    # start Real-Time Listener and crawler
    overall_tasks = asyncio.gather(slacker.start_listening(), crawler_task)
    try:
        signal.signal(signal.SIGTERM, lambda *args: exec("raise KeyboardInterrupt"))  # correct exit handler
        loop.run_until_complete(overall_tasks)
    except KeyboardInterrupt as e:
        __logger.info("Received exit signal, exiting...")
        dbEngine.close()
        sys.exit(0)
