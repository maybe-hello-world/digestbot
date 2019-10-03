import os
import sys
import time
import logging
from typing import List, Tuple, Optional, NoReturn
from datetime import datetime, timedelta
from functools import reduce

import nest_asyncio

import slack
import slack.errors as errors

# Bug in slackclient v2.2.0:
# https://stackoverflow.com/questions/57154308/why-am-i-getting-runtimeerror-this-event-loop-is-already-running
nest_asyncio.apply()


class Slacker:
    """
    Slack API wrapper
    """

    def __init__(self):
        self.logger = logging.getLogger("SlackAPI")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler(sys.stdout))

        if "SLACK_USER_TOKEN" not in os.environ:
            raise Exception("SLACK_USER_TOKEN not provided in env variables")
        if "SLACK_BOT_TOKEN" not in os.environ:
            raise Exception("SLACK_BOT_TOKEN not provided in env variables")

        self.web_client = slack.WebClient(
            token=os.environ["SLACK_USER_TOKEN"], run_async=True
        )
        self.rtm_client = slack.RTMClient(
            token=os.environ["SLACK_BOT_TOKEN"], run_async=True
        )

        try:
            self.web_client.auth_test()
            ans = slack.WebClient(token=os.environ["SLACK_BOT_TOKEN"]).auth_test()
        except errors.SlackClientError as e:
            self.logger.exception(e)
            raise
        else:
            self.user_id = ans["user_id"]

        self.logger.info("Slack API connection successfully established.")

    async def start(self) -> NoReturn:
        """
        Start to listen to messages. ATTENTION: this function never ends.
        """
        self.logger.info("RTM listener started")
        await self.rtm_client.start()

    async def is_direct_channel(self, channel_id: str) -> Optional[bool]:
        """
        Check whether given channel is direct messages channel or public

        :param channel_id: Slack channel ID
        :return: True if direct messages, False if not, None if have no connections or other problems
        """
        try:
            ch_info = await self.web_client.conversations_info(channel=channel_id)
        except errors.SlackClientError as e:
            self.logger.exception(e)
            return None

        is_im = ch_info.get("channel", dict()).get("is_im", False)
        return is_im

    async def get_channels_list(
        self, exclude_archive: bool = True, public_only: bool = True
    ) -> Optional[List[Tuple[str, str]]]:
        """
        Get channel names and IDs

        :param exclude_archive: whether to exclude archived chats
        :param public_only: whether to use private channels
        :return: List of tuples (channel_name, channel_id) or None if any error
        """

        # get channels
        exclude_archive = str(exclude_archive).lower()
        types = "public_channel" if public_only else "public_channel, private_channel"

        try:
            channels = await self.web_client.channels_list(
                exclude_archive=exclude_archive, types=types
            )
        except errors.SlackClientError as e:
            self.logger.exception(e)
            return None

        # get ids
        ch_info = [(x["id"], x["name"]) for x in channels["channels"]]

        return ch_info

    async def __count_th_len(self, ch_id: str, mes: dict) -> int:
        """
        Count length of the entire thread (with all replies)

        :param ch_id: channel ID
        :param mes: message to be updated
        :return: count of chars in thread's messages
        """

        if "replies" not in mes:
            return len(mes.get("text", []))

        try:
            answer = await self.web_client.conversations_replies(
                channel=ch_id, ts=mes.get("ts", 0)
            )
        except errors.SlackClientError as e:
            self.logger.exception(e)
            return 0

        sum_length = reduce(
            lambda x, y: x + len(y.get("text", 0)), answer.get("messages", []), 0
        )
        return sum_length

    async def _count_thread_lengths(
        self, channel_id: str, messages: List[dict]
    ) -> List[dict]:
        """
        Update messages with length in chars

        :param channel_id: channel ID (where message is)
        :param messages: message list
        :return: messages with counted length in chars
        """

        for mess in messages:
            mess.update(
                {"char_length": await self.__count_th_len(ch_id=channel_id, mes=mess)}
            )

        return messages

    async def get_channel_messages(
        self,
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

        allowed_subtypes = {"thread_broadcast", "bot_message", "file_share", None}

        # to unixtime
        oldest = oldest or datetime.now() - timedelta(days=1)
        oldest = int(time.mktime(oldest.utctimetuple()))

        kws = {"channel": channel_id, "oldest": oldest, "limit": limit}
        if latest is not None:
            latest = int(time.mktime(latest.utctimetuple()))
            kws.update({"latest": latest})

        try:
            answer = await self.web_client.conversations_history(**kws)
        except errors.SlackClientError as e:
            self.logger.exception(e)
            return None

        # TODO: "'has_more': True" handling
        messages = [
            x for x in answer["messages"] if x.get("subtype", None) in allowed_subtypes
        ]

        messages = await self._count_thread_lengths(channel_id, messages)

        # return only needed statistics
        messages = [
            {
                "user": x.get("user", x.get("username", "")),
                "text": x["text"],
                "ts": x["ts"],
                "reply_count": x.get("reply_count", 0),
                "reply_users_count": x.get("reply_users_count", 0),
                "reactions": x.get("reactions", []),
                "char_length": x.get("char_length", 0),
                "channel": channel_id,
            }
            for x in messages
        ]

        return messages

    async def get_permalink(self, channel_id: str, message_ts: str) -> Optional[str]:
        """
        Get permalink for given message in given channel

        :param channel_id: channel ID where message is located
        :param message_ts: timestamp (unixtime) of the message
        :return: permalink or None if not found or any error
        """

        try:
            answer = await self.web_client.chat_getPermalink(
                channel=channel_id, message_ts=message_ts
            )
        except errors.SlackClientError as e:
            self.logger.exception(e)
            return None

        link = answer["permalink"]
        return link

    async def update_permalinks(
        self, channel_id: str, messages: List[dict]
    ) -> List[dict]:
        """
        Take messages and return them with permalinks added

        :param channel_id: Message's origin
        :param messages: List of messages to be updated
        :return: List of these messages with added permalinks
        """

        for mess in messages:
            mess.update({"permalink": await self.get_permalink(channel_id, mess["ts"])})

        return messages

    async def post_to_channel(self, channel_id: str, text: str) -> None:
        """
        Post given text to given chat

        :param channel_id: Slack channel ID
        :param text: text to be posted
        :return: Nothing
        """
        try:
            await self.web_client.chat_postMessage(
                channel=channel_id, text=text, as_user="false", link_names="true"
            )
        except errors.SlackClientError as e:
            self.logger.exception(e)
