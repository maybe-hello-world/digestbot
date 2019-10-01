import os
import slack
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import time

client = slack.WebClient(token=os.environ['SLACK_API_TOKEN'])


def get_channels_list(
        cl: slack.WebClient,
        exclude_archive: bool = True,
        public_only: bool = True) -> Optional[List[Tuple[str, str]]]:
    """
    Get channel names and IDs

    :param cl: slack client instance
    :param exclude_archive: whether to exclude archived chats
    :param public_only: whether to use private channels
    :return: List of tuples (channel_name, channel_id) or None if any error
    """

    # get channels
    exclude_archive = 'true' if exclude_archive else 'false'
    types = 'public_channel' if public_only else 'public_channel, private_channel'
    channels = cl.channels_list(exclude_archive=exclude_archive, types=types)

    # get ids
    ch_info = [(x['id'], x['name']) for x in channels['channels']]

    # TODO: logging & error handling
    return ch_info


def get_channel_top_messages(
        cl: slack.WebClient,
        channel_id: str,
        oldest: datetime = None,
        limit=100000) -> Optional[List[dict]]:
    """
    Get list of messages and their statistics from the given channel from _oldest_ until now

    :param cl: slack WebClient instance
    :param channel_id: ID of channel in slack workspace
    :param oldest: DateTime of oldest message to be returned (None equals to yesterday)
    :param limit: limit for amount of returned messages
    :return: List of messages from the channel or None if any error
    """

    # to unixtime
    oldest = oldest or datetime.now() - timedelta(days=1)
    oldest = int(time.mktime(oldest.utctimetuple()))

    answer = cl.conversations_history(channel=channel_id, oldest=oldest, limit=limit)

    # TODO: logging & error handling & "'has_more': True" handling
    messages = answer['messages']

    return messages


if __name__ == '__main__':
    # get channels list
    ch_info = get_channels_list(client)

    for ch_id, ch_name in ch_info:
        print(f"Channel: {ch_name}")
        print(get_channel_top_messages(client, ch_id))
        print('\n\n')
