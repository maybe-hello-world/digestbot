import time

from decimal import Decimal
from datetime import datetime
from typing import List

import requests as r

from common.models import Message
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


async def process_top_request(args: TopCommandArgs, db_service: str, user_id: str) -> str:
    """
    Returns formatted message with top-messages to user

    :param args: arguments parsed from user message (see top_command)
    :param db_service: url of service for database operations
    :param user_id: ID of the user
    :return: formatted message
    """
    base_url = f"http://{db_service}/messages/top"

    parameters = {
        "sorting_type": args.sorting_method,
        "top_count": args.N,
        "after_ts": Decimal(time.mktime((datetime.now() - args.time).timetuple())),
    }

    if args.N < 0:
        return "Number of messages should be positive."

    if args.is_all_channels_requested():
        pass  # Nothing to add
    elif args.is_channel():
        parameters['channel_id'] = args.channel_id
    else:
        parameters['category_name'] = args.category_name
        parameters['user_id'] = user_id

    answer = r.get(base_url, params=parameters, timeout=10)
    if answer.status_code != 200:
        return (
            "Sorry, some error occurred during message handling. "
            "Please, contact bot developers. Thanks."
        )

    messages = answer.json()
    if not messages:
        return (
            "No messages to print. Either category/channel/messages not found "
            "or something went wrong."
        )
    else:
        return __pretty_top_format(messages)
