import os
import slack
import asyncio
import logging
from .slacker import Slacker, ChannelMessage
from typing import List
from datetime import datetime, timedelta
from dataclasses import dataclass


slacker: Slacker
CRAWL_INTERVAL: int = 60 * 15  # in seconds
bot_name: str


@dataclass(frozen=True)
class UserRequest:
    text: str  # user text
    user: str  # author's username
    channel: str  # ID of channel from Slack
    ts: str  # timestamp of the message
    is_im: bool  # is it private message to bot (or in public channel)


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


def sort_messages(
    messages: List[ChannelMessage], topk: int = 20, criterion: str = "replies"
) -> List[ChannelMessage]:
    """
    Sort messages by unique and mysterious algorithm and return most important

    :param messages: list of messages from a channel
    :param topk: amount of messages to return from each channel
    :param criterion: criterion for message sorting (replies / length / reactions)
    :return: sorted messages
    """

    if criterion not in {"replies", "length", "reactions"}:
        logging.warning(f"Wrong criterion: {criterion}, using 'replies'")
        criterion = "replies"

    if criterion == "replies":
        key = "reply_count"
    elif criterion == "length":
        key = "char_length"
    else:
        logging.info("Ha-ha, reactions are not supported yet, using replies")
        key = "reply_count"

    return sorted(messages, key=lambda x: x.__getattr__(key), reverse=True)[:topk]


async def process_message(message: UserRequest) -> None:
    """Answer only on needed messages"""
    global bot_name

    # do not answer on own messages
    if message.user == bot_name:
        return

    # answer only on direct messages and mentions in chats
    if slacker.user_id not in message.text and not message.is_im:
        return

    text_to_answer = (
        f"Hello, <@{message.user}>! Right now I'm too lazy to calculate the top,"
        f" but I'll be able in the future. Stay tuned!"
    )
    await slacker.post_to_channel(channel_id=message.channel, text=text_to_answer)


@slack.RTMClient.run_on(event="message")
async def handle_message(**payload) -> None:
    """Preprocess messages"""
    if "data" not in payload:
        return None

    data = payload["data"]
    channel = data.get("channel", "")
    is_im = await slacker.is_direct_channel(channel) or False

    message = UserRequest(
        text=data.get("text", ""),
        user=data.get("user", "") or data.get("username", ""),
        channel=channel,
        ts=data.get("ts", ""),
        is_im=is_im,
    )

    await process_message(message)


if __name__ == "__main__":
    user_token = os.environ["SLACK_USER_TOKEN"]
    bot_token = os.environ["SLACK_BOT_TOKEN"]

    global bot_name
    bo_name = os.environ.get("bot_name", "digest-bot")

    slacker = Slacker(user_token=user_token, bot_token=bot_token)

    loop = asyncio.get_event_loop()

    # # Instantiate crawler timer with corresponding function
    crawler_task = loop.create_task(crawl_messages())

    # start Real-Time Listener and crawler
    overall_tasks = asyncio.gather(slacker.start_listening(), crawler_task)
    loop.run_until_complete(overall_tasks)
