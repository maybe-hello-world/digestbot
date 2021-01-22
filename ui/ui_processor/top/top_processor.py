import time

from decimal import Decimal
from datetime import datetime
from typing import List

from common.db.models import Message
from common.db.dbengine.PostgreSQLEngine import PostgreSQLEngine
from common.db.dbrequest.message import (
    get_top_messages,
    get_top_messages_by_channel_id,
    get_top_messages_by_category_name,
)
from .top_command import TopCommandArgs


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
            round(x.reactions_rate, 2),
            x.link,
        )
        for i, x in enumerate(messages, start=1)
    )
    return "\n\n\n".join(messages)


async def process_top_request(args: TopCommandArgs, db_engine: PostgreSQLEngine, user_id: str) -> str:
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
            category_name=args.category_name, user_id=user_id, **parameters
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
