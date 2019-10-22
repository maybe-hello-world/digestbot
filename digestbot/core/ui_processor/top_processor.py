from __future__ import annotations

import time

from decimal import Decimal
from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Optional, Any, Dict, List

from digestbot.core import Message
from digestbot.command_parser.argument import (
    StringArgument,
    ChoiceArgument,
    TimeDeltaArgument,
    IntArgument,
)
from digestbot.command_parser.command import CommandBuilder
from digestbot.core.common.Enums import SortingType
from digestbot.core.db.dbengine import PostgreSQLEngine
from digestbot.core.db.dbrequest.message import (
    get_top_messages,
    get_top_messages_by_channel_id,
    get_top_messages_by_category_name,
)

top_command = (
    CommandBuilder("top")
    .add_argument(IntArgument("N", default=5))
    .add_argument(TimeDeltaArgument("time", default=timedelta(days=1)))
    .add_argument(
        ChoiceArgument(
            "sorting_method", ["replies", "length", "reactions"], default="replies"
        )
    )
    .add_argument(StringArgument("channel", default=None))
    .build()
)


@dataclass(frozen=True)
class TopCommandArgs:
    N: int
    time: timedelta
    sorting_method: str

    channel_id: Optional[str] = None
    category_name: Optional[str] = None

    @staticmethod
    def _parse_channel(channel: Optional[str]) -> Dict[str, str]:
        if not channel:
            return {}
        split = channel.strip("<>").split("|")
        if len(split) == 1:
            return {"category_name": split[0]}
        if len(split) == 2:
            return {"channel_id": split[0].lstrip("#")}
        raise ValueError(
            f"Channel Id format is not recognized (split result is {split}). Possible Slack API change"
        )

    def is_all_channels_requested(self) -> bool:
        return self.category_name is None and self.channel_id is None

    def is_channel(self) -> bool:
        return self.channel_id is not None

    @staticmethod
    def from_dict(kwargs: Dict[str, Any]) -> TopCommandArgs:
        sorting_type_mapper = {
            "replies": "reply_count",
            "length": "thread_length",
            "reactions": "reactions_rate",
        }
        kwargs["sorting_method"] = SortingType(
            sorting_type_mapper[kwargs["sorting_method"]]
        )
        channel_parse = TopCommandArgs._parse_channel(kwargs["channel"])
        del kwargs["channel"]
        kwargs.update(channel_parse)
        return TopCommandArgs(**kwargs)


def __pretty_top_format(messages: List[Message]) -> str:
    """
    Create pretty formatted output of top slack messages.

    :param messages: list of slack messages from DB
    :return: string to be send to the channel
    """
    template = (
        "{}. <@{}> | <#{}>\n"
        "{}...\n"
        "Replies: {} from {} users. Reactions rate: {}.\n"
        "Link: {}"
    )
    messages = (
        template.format(
            i,
            x.username,
            x.channel_id,
            x.text[:200],
            x.reply_count,
            x.reply_users_count,
            x.reactions_rate,
            x.link,
        )
        for i, x in enumerate(messages, start=1)
    )
    return "\n\n\n".join(messages)


async def process_top_request(args: TopCommandArgs, db_engine: PostgreSQLEngine) -> str:
    """
    Returns formatted message with top-messages to user

    :param args: arguments parsed from user message (see top_command)
    :param db_engine: db engine for database operations
    :return: formatted message
    """

    parameters = {
        "db_engine": db_engine,
        "sorting_type": args.sorting_method,
        "top_count": args.N,
        "after_ts": Decimal(time.mktime((datetime.now() - args.time).timetuple())),
    }

    if args.N < 0:
        return "Number of messages should be positive."

    if args.is_all_channels_requested():
        req_status, messages = await get_top_messages(**parameters)
    elif args.is_channel():
        req_status, messages = await get_top_messages_by_channel_id(
            channel_id=args.channel_id, **parameters
        )
    else:
        req_status, messages = await get_top_messages_by_category_name(
            category_name=args.category_name, **parameters
        )

    if not req_status:
        formatted_message = (
            "Sorry, some error occured during message handling. "
            "Please, contact bot developers. Thanks."
        )
    elif not messages:
        formatted_message = (
            "No messages to print. Either category/channel/messages not found, "
            "or something gonna wrong."
        )
    else:
        formatted_message = __pretty_top_format(messages)

    return formatted_message
