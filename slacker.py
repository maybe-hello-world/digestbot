"""
Slack API wrapper for unification.
"""

import os
import sys
import time
import logging
from typing import List, Tuple, Optional
from datetime import datetime, timedelta

import slack
import slack.errors as errors

logger = logging.getLogger("SlackAPI")
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))

client: slack.WebClient


def get_channels_list(
    exclude_archive: bool = True, public_only: bool = True
) -> Optional[List[Tuple[str, str]]]:
    """
    Get channel names and IDs

    :param exclude_archive: whether to exclude archived chats
    :param public_only: whether to use private channels
    :return: List of tuples (channel_name, channel_id) or None if any error
    """

    global client

    # get channels
    exclude_archive = str(exclude_archive).lower()
    types = "public_channel" if public_only else "public_channel, private_channel"

    try:
        channels = client.channels_list(exclude_archive=exclude_archive, types=types)
    except errors.SlackClientError as e:
        logger.exception(e)
        return None

    # get ids
    ch_info = [(x["id"], x["name"]) for x in channels["channels"]]

    return ch_info


def get_channel_messages(
    channel_id: str,
    oldest: datetime = None,
    latest: datetime = None,
    limit: int = 100000,
) -> Optional[List[dict]]:
    """
    Get list of messages and their statistics from the given channel from _oldest_ until now

    :param channel_id: ID of channel in slack workspace
    :param oldest: DateTime of oldest message to be returned (None equals to yesterday)
    :param latest: DateTime of newest message to be returned (None equals to now)
    :param limit: limit for amount of returned messages
    :return: List of messages from the channel or None if any error
    """

    global client
    allowed_subtypes = {"thread_broadcast", "bot_message", "file_share", None}

    # to unixtime
    oldest = oldest or datetime.now() - timedelta(days=1)
    oldest = int(time.mktime(oldest.utctimetuple()))

    kws = {"channel": channel_id, "oldest": oldest, "limit": limit}
    if latest is not None:
        latest = int(time.mktime(latest.utctimetuple()))
        kws.update({"latest": latest})

    try:
        answer = client.conversations_history(**kws)
    except errors.SlackClientError as e:
        logger.exception(e)
        return None

    # TODO: "'has_more': True" handling
    messages = (
        x for x in answer["messages"] if x.get("subtype", None) in allowed_subtypes
    )

    # return only needed statistics
    messages = [
        {
            "user": x.get("user", x.get("username", "")),
            "text": x["text"],
            "ts": x["ts"],
            "reply_count": x.get("reply_count", 0),
            "reply_users_count": x.get("reply_users_count", 0),
            "reactions": x.get("reactions", []),
        }
        for x in messages
    ]

    return messages


def get_permalink(channel_id: str, message_ts: str) -> Optional[str]:
    """
    Get permalink for given message in given channel

    :param channel_id: channel ID where message is located
    :param message_ts: timestamp (unixtime) of the message
    :return: permalink or None if not found or any error
    """

    global client

    try:
        answer = client.chat_getPermalink(channel=channel_id, message_ts=message_ts)
    except errors.SlackClientError as e:
        logger.exception(e)
        return None

    link = answer["permalink"]
    return link


def _init() -> None:
    """
    Initialize slack client instance
    :return: None
    """
    global client

    if "SLACK_API_TOKEN" not in os.environ:
        raise Exception("SLACK_API_TOKEN not provided in env variables")

    client = slack.WebClient(token=os.environ["SLACK_API_TOKEN"])

    try:
        client.auth_test()
    except errors.SlackClientError as e:
        logger.exception(e)
        raise

    logger.info("Slack API connection successfully established.")


_init()
