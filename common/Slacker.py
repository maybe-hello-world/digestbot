import time
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
from functools import reduce
from logging import Logger

import asyncio

from result import Result

from .models import Message
from .utils import reaction_ranking
from .resilence_library.retryafter import RetryAfterSlack, RetryAfterError

import slack
import slack.errors as errors


class Slacker:
    """
    Slack API wrapper
    """

    def __init__(self, user_token: str, bot_token: str, logger: Logger, async_init: bool = False):
        self.logger = logger
        self.retry_policy = RetryAfterSlack(repeat=5)

        self.bot_web_client = slack.WebClient(token=bot_token, run_async=True)
        self.user_web_client = slack.WebClient(token=user_token, run_async=True)

        if async_init:
            return

        try:
            self.bot_web_client.auth_test()
            ans = slack.WebClient(token=bot_token).auth_test()
            self.user_web_client.auth_test()
        except errors.SlackClientError as e:
            self.logger.exception(e)
            raise
        else:
            self.user_id = ans["user_id"]

        self.logger.info("Slack API connection successfully established.")

    async def __ainit__(self, bot_token: str):
        try:
            await self.bot_web_client.auth_test()
            ans = await slack.WebClient(token=bot_token, run_async=True).auth_test()
            await self.user_web_client.auth_test()
        except errors.SlackClientError as e:
            self.logger.exception(e)
            raise
        else:
            self.user_id = ans["user_id"]

        self.logger.info("Slack API connection successfully established.")

    async def get_channels_list(
            self, exclude_archive: bool = True, public_only: bool = True
    ) -> Optional[List[Tuple[str, str]]]:
        """
        Get channel names and IDs

        :param exclude_archive: whether to exclude archived chats
        :param public_only: whether to use private channels
        :return: List of tuples (channel_id, channel_name) or None if any error
        """

        # get channels
        exclude_archive = str(exclude_archive).lower()
        types = "public_channel" if public_only else "public_channel, private_channel"

        try:
            channels = await self.retry_policy.execute(
                lambda: self.bot_web_client.conversations_list(
                    exclude_archive=exclude_archive, types=types, limit=999
                )
            )
        except (RetryAfterError, asyncio.TimeoutError):
            self.logger.warning("Timeout during get_channel_list request")
            return None
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
            answer = await self.retry_policy.execute(
                lambda: self.user_web_client.conversations_replies(
                    channel=ch_id, ts=mes.get("ts", 0)
                )
            )
        except (RetryAfterError, asyncio.TimeoutError):
            self.logger.warning("Timeout during count_thread_length request")
            return 0
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

    @staticmethod
    def _count_reaction_rate(messages: List[dict]) -> List[dict]:
        for mess in messages:
            mess.update(
                {
                    "reaction_rate": reaction_ranking.get_react_score(
                        mess.get("reactions", [])
                    )
                }
            )

        return messages

    @staticmethod
    def __remove_dangerous_substrings(x: str) -> str:
        return (x
                .replace("<!everyone>", "everyone")
                .replace("@everyone", "everyone")
                .replace("<!channel>", "channel")
                .replace("@channel", "channel")
                .replace("<!here>", "here")
                .replace("@here", "here")
                )

    async def get_channel_messages(
            self,
            channel_id: str,
            oldest: datetime = None,
            latest: datetime = None,
            limit: int = 100000,
    ) -> Optional[List[Message]]:
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
        oldest = oldest or (datetime.now() - timedelta(days=1))
        oldest = int(time.mktime(oldest.utctimetuple()))

        kws = {"channel": channel_id, "oldest": oldest, "limit": limit}
        if latest is not None:
            latest = int(time.mktime(latest.utctimetuple()))
            kws.update({"latest": latest})

        try:
            answer = await self.retry_policy.execute(
                lambda: self.user_web_client.conversations_history(**kws)
            )
        except (RetryAfterError, asyncio.TimeoutError):
            self.logger.warning("Timeout during get_channel_messages request")
            return None
        except errors.SlackClientError as e:
            self.logger.exception(e)
            return None

        # TODO: "'has_more': True" handling
        messages = [
            x for x in answer["messages"] if x.get("subtype", None) in allowed_subtypes
        ]

        messages = await self._count_thread_lengths(channel_id, messages)
        messages = self._count_reaction_rate(messages)

        # return only needed statistics
        messages = [
            Message(
                username=x.get("user", "") or x.get("username", ""),
                timestamp=x["ts"],
                reply_count=x.get("reply_count", 0),
                reply_users_count=x.get("reply_users_count", 0),
                reactions_rate=x.get("reaction_rate", 0),
                thread_length=x.get("char_length", 0),
                channel_id=channel_id,
                link=None,
            )
            for x in messages
        ]

        return messages

    async def get_permalink(
            self, channel_id: str, message_ts: str
    ) -> Result[str, str]:
        """
        Get permalink for given message in given channel

        :param channel_id: channel ID where message is located
        :param message_ts: timestamp (unixtime) of the message
        :return: permalink or None if not found or any error
        """

        try:
            answer = await self.retry_policy.execute(
                lambda: self.bot_web_client.chat_getPermalink(
                    channel=channel_id, message_ts=message_ts
                )
            )

            link = answer.get("permalink", "")
            return Result.Ok(link)
        except (asyncio.TimeoutError, RetryAfterError):
            self.logger.debug("Too much permalinks requested, will try next time.")
        except errors.SlackApiError as e:
            if e.response.get("error", "") == "message_not_found":
                return Result.Err("Sorry, the message was deleted :(")
            if e.response.get("error", "") == "channel_not_found":
                return Result.Err("Sorry, the channel was deleted :(")
            self.logger.exception(e)
        except Exception as e:
            self.logger.exception(e)

        return Result.Err("")

    async def update_permalinks(self, messages: List[Message]) -> List[Message]:
        """
        Take messages and return them with permalinks added

        :param messages: List of messages to be updated
        :return: List of these messages with added permalinks
        """

        links = await asyncio.gather(
            *[self.get_permalink(mess.channel_id, mess.timestamp) for mess in messages]
        )

        messages = [
            Message(
                username=mess.username,
                timestamp=mess.timestamp,
                reply_count=mess.reply_count,
                reply_users_count=mess.reply_users_count,
                thread_length=mess.thread_length,
                channel_id=mess.channel_id,
                reactions_rate=mess.reactions_rate,
                link=link.value,
            )
            for mess, link in zip(messages, links)
        ]

        return messages

    async def post_to_channel(
            self,
            channel_id: str,
            text: str = "",
            blocks: Optional[str] = None,
            ephemeral: bool = False,
            user_id: str = ""
    ) -> None:
        if blocks:
            blocks = self.__remove_dangerous_substrings(blocks)
            params = {"blocks": blocks}
        else:
            text = self.__remove_dangerous_substrings(text)
            params = {"text": text}

        params.update({
            "channel": channel_id,
            "link_names": "true",
            "unfurl_links": "true",
            "unfurl_media": "true"
        })

        if not ephemeral:
            post = lambda: self.bot_web_client.chat_postMessage(**params)
        else:
            post = lambda: self.bot_web_client.chat_postEphemeral(**params, user=user_id)

        try:
            if text or blocks:
                await self.retry_policy.execute(post)
        except (RetryAfterError, asyncio.TimeoutError):
            self.logger.warning("Couldn't post to channel due to timeout.")
            return None
        except errors.SlackClientError as e:
            self.logger.error("Request params: " + str(params))
            self.logger.exception(e)

    async def get_user_info(self, user_id: str) -> Optional[dict]:
        """
        Receive information about the user

        :param user_id: ID of the user
        :return: dict with user's info from https://api.slack.com/methods/users.info
        """

        try:
            answer = await self.retry_policy.execute(lambda: self.bot_web_client.users_info(user=user_id))
            return answer['user']
        except (asyncio.TimeoutError, RetryAfterError):
            self.logger.warning("Couldn't receive user's info.")
            return None
        except errors.SlackClientError as e:
            self.logger.exception(e)
            return None

    async def open_view(self, trigger_id: str, view: dict):
        """
        Open modal window with given trigger_id and window description
        :param trigger_id: trigger_id from recent interaction
        :param view: modal window description (Slack Block Kit payload)
        """
        try:
            answer = await self.retry_policy.execute(
                lambda: self.bot_web_client.views_open(trigger_id=trigger_id, view=view))
            return answer['user']
        except (asyncio.TimeoutError, RetryAfterError):
            self.logger.warning("Couldn't receive user's info.")
            return None
        except errors.SlackClientError as e:
            self.logger.exception(e)
            return None

    async def get_im_latest_user_message_text(
            self, channel_id, user_id: str, oldest: Optional[datetime] = None
    ) -> Optional[str]:

        oldest = oldest or (datetime.now() - timedelta(minutes=5))
        oldest = int(time.mktime(oldest.utctimetuple()))

        try:
            answer = await self.retry_policy.execute(
                lambda: self.bot_web_client.conversations_history(channel=channel_id, oldest=oldest, limit=5)
            )
        except (RetryAfterError, asyncio.TimeoutError):
            self.logger.warning("Timeout during get_im_latest_user_message request")
            return None
        except errors.SlackClientError as e:
            self.logger.exception(e)
            return None

        messages = filter(
            lambda elem: elem.get("user", "") == user_id or elem.get("username", "") == user_id,
            answer['messages']
        )
        message = max(messages, key=lambda elem: float(elem.get("ts", "0")), default=None)
        if message is not None:
            message = self.__remove_dangerous_substrings(message.get("text", " "))
        return message
