import os
import slack
import asyncio
import digestbot.core.UserProcessing.ReqParser as ReqParser
from digestbot.core.SlackAPI.Slacker import Slacker
from datetime import datetime, timedelta


slacker: Slacker
CRAWL_INTERVAL: int = 60 * 15  # in seconds
bot_name: str


async def crawl_messages() -> None:
    def write_to_db_mock(anything):
        print(anything, end="\n\n")

    while True:
        # get data
        ch_info = await slacker.get_channels_list()
        for ch_id, ch_name in ch_info:
            print(f"Channel: {ch_name}")

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


if __name__ == "__main__":
    user_token = os.environ["SLACK_USER_TOKEN"]
    bot_token = os.environ["SLACK_BOT_TOKEN"]

    bot_name = os.environ.get("bot_name", "digest-bot")

    slacker = Slacker(user_token=user_token, bot_token=bot_token)

    loop = asyncio.get_event_loop()

    # # Instantiate crawler timer with corresponding function
    crawler_task = loop.create_task(crawl_messages())

    # start Real-Time Listener and crawler
    overall_tasks = asyncio.gather(slacker.start_listening(), crawler_task)
    loop.run_until_complete(overall_tasks)
