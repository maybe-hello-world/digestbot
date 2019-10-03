import slack
from slacker import Slacker
from typing import List
from datetime import datetime, timedelta


slacker: Slacker


def sort_messages(messages: List[dict], topk: int = 20) -> List[dict]:
    """
    Sort messages by unique and mysterious algorithm and return most important

    :param messages: list of messages from a channel
    :param topk: amount of messages to return from each channel
    :return: sorted messages
    """

    return sorted(messages, key=lambda x: x.get("reply_count", 0), reverse=True)[:topk]


def process_message(message: dict) -> None:
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
    slacker.post_to_channel(channel_id=message["channel"], text=text_to_answer)


@slack.RTMClient.run_on(event="message")
def handle_message(**payload) -> None:
    """Preprocess messages"""
    if "data" not in payload:
        return None

    data = payload["data"]
    channel = data.get("channel", "")
    is_im = slacker.is_direct_channel(channel) or False

    message = {
        "text": data.get("text", ""),
        "user": data.get("user", "") or data.get("username", ""),
        "channel": channel,
        "ts": data.get("ts", ""),
        "is_im": is_im,
    }

    process_message(message)


if __name__ == "__main__":
    # get channels list
    slacker = Slacker()

    ch_info = slacker.get_channels_list()
    for ch_id, ch_name in ch_info:
        print(f"Channel: {ch_name}")

        week_ago = datetime.now() - timedelta(days=7)
        messages = slacker.get_channel_messages(ch_id, week_ago)

        messages = sort_messages(messages)
        messages = slacker.update_permalinks(channel_id=ch_id, messages=messages)

        print(messages)
        print("\n\n")
    slacker.start()
