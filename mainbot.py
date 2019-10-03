import slack
import asyncio
from slacker import Slacker
from typing import List
from datetime import datetime, timedelta


slacker: Slacker
CRAWL_INTERVAL: int = 60 * 15  # in seconds


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


def sort_messages(messages: List[dict], topk: int = 20) -> List[dict]:
    """
    Sort messages by unique and mysterious algorithm and return most important

    :param messages: list of messages from a channel
    :param topk: amount of messages to return from each channel
    :return: sorted messages
    """

    return sorted(messages, key=lambda x: x.get("reply_count", 0), reverse=True)[:topk]


async def process_message(message: dict) -> None:
    """Answer only on needed messages"""

    # do not answer on own messages
    if message["user"] == "digest-bot":
        return

    # answer only on direct messages and mentions in chats
    if slacker.user_id not in message["text"] and not message["is_im"]:
        return

    text_to_answer = (
        f"Hello, <@{message['user']}>! Right now I'm too lazy to calculate the top,"
        f" but I'll be able in the future. Stay tuned!"
    )
    await slacker.post_to_channel(channel_id=message["channel"], text=text_to_answer)


@slack.RTMClient.run_on(event="message")
async def handle_message(**payload) -> None:
    """Preprocess messages"""
    if "data" not in payload:
        return None

    data = payload["data"]
    channel = data.get("channel", "")
    is_im = await slacker.is_direct_channel(channel) or False

    message = {
        "text": data.get("text", ""),
        "user": data.get("user", "") or data.get("username", ""),
        "channel": channel,
        "ts": data.get("ts", ""),
        "is_im": is_im,
    }

    await process_message(message)


if __name__ == "__main__":
    # get channels list
    slacker = Slacker()

    loop = asyncio.get_event_loop()

    # # Instantiate crawler timer with corresponding function
    crawler_task = loop.create_task(crawl_messages())

    # start Real-Time Listener and crawler
    overall_tasks = asyncio.gather(slacker.start(), crawler_task)
    loop.run_until_complete(overall_tasks)
