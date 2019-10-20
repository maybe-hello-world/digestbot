import re
import time
from decimal import Decimal
from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Optional, List

from digestbot.core import Message
from digestbot.core.common import LoggerFactory, config
from digestbot.core.common.Enums import SortingType
from digestbot.core.db.dbengine import PostgreSQLEngine
from digestbot.core.db.dbrequest.message import (
    get_top_messages,
    get_top_messages_by_channel_id,
    get_top_messages_by_category_name,
)
from digestbot.core.ui_processor.common import UserRequest


_logger = LoggerFactory.create_logger(__name__, config.LOG_LEVEL)


@dataclass(frozen=True)
class DBTopRequest:
    after_ts: Decimal
    top_count: int = 5
    is_channel: bool = True
    channel_id: Optional[
        str
    ] = None  # channel (starts with #) or preset (without #) name
    sorting_type: SortingType = SortingType.REPLIES


__SORTING_TYPE_MAPPER = {
    "replies": "reply_count",
    "length": "thread_length",
    "reactions": "reactions_rate",
}


def __pretty_top_format(messages: List[Message]) -> str:
    """
    Create pretty formatted output of top slack messages.

    :param messages: list of slack messages from DB
    :return: string to be send to the channel
    """
    template = (
        "{}. Author: <@{}>, text: {}.... "
        "The message has {} replies from {} users and reaction rate equal to {}.\n"
        "Link to the message: {}"
    )
    messages = (
        template.format(
            i,
            x.username,
            x.text[:50],
            x.reply_count,
            x.reply_users_count,
            x.reactions_rate,
            x.link,
        )
        for i, x in enumerate(messages, start=1)
    )
    return "\n\n".join(messages)


async def __process_top_request(
    message: UserRequest, db_engine: PostgreSQLEngine
) -> Optional[str]:
    """
    Parse TOP_REQUEST command from user message

    :param message: user message
    :param db_engine: db engine for database operations
    :return: formatted message if parsed, None otherwise
    """

    def __parse_text(_mes: UserRequest) -> Optional[DBTopRequest]:
        """
        Parse request and create DBTopRequest

        :param _mes: user message
        :return: DBTopRequest if valid command, None otherwise
        """
        command_text = _mes.text.strip()

        # remove bot mention
        if re.match(r"<@[A-Z\d]+>", command_text):
            command_text = command_text[command_text.index(">") + 1 :].strip()

        # damn regexps
        channel_name = r"<#[\d_\-a-zA-Z\|]+>"  # channel name
        preset_name = r"[A-Za-z]+"  # preset name
        channel_pattern = fr"(?:{channel_name}|{preset_name})"
        time_pattern = r"\d+(?:m|h|d|w)"
        sorting_types = " " + "| ".join(
            __SORTING_TYPE_MAPPER.keys()
        )  # one of several sorting types
        command_pattern = (
            fr""
            fr"top(?P<amount> [\d]+)?"
            fr"(?P<channel> {channel_pattern})?"
            fr"(?P<time> {time_pattern})?"
            fr"(?P<sorting>{sorting_types})?"
        )
        parse_result = re.fullmatch(command_pattern, command_text)

        if parse_result is None:
            return None
        amount = parse_result.group("amount")
        channel = parse_result.group("channel")
        time_str = parse_result.group("time")
        sorting = parse_result.group("sorting")

        if amount is not None:
            try:
                amount = int(amount.strip())
            except TypeError as e:
                _logger.exception(e)
                amount = None

        if sorting is not None:
            try:
                sorting = __SORTING_TYPE_MAPPER[sorting.strip()]
                sorting = SortingType(sorting)
            except (ValueError, KeyError) as e:
                _logger.exception(e)
                sorting = None

        try:
            assert time_str is not None
            time_str = time_str.strip()
            time_amount = int(time_str[:-1])
            time_type = time_str[-1]
            _mapper = {"m": "minutes", "h": "hours", "d": "days", "w": "weeks"}
            time_type = _mapper[time_type]
            kwargs = {time_type: time_amount}
            td = timedelta(**kwargs)
        except (AssertionError, ZeroDivisionError, KeyError):
            td = timedelta(days=1)

        is_channel = False
        if channel is not None:
            channel = channel.strip()
            if channel.startswith("<#"):
                is_channel = True
                channel = channel.strip("<>#")
                channel = channel[: channel.index("|")]  # AJLK323BKJ|general

        ts = datetime.now() - td
        ts = Decimal(time.mktime(ts.timetuple()))

        kwargs = {
            "after_ts": ts,
            "top_count": amount,
            "is_channel": is_channel,
            "channel_id": channel,
            "sorting_type": sorting,
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        return DBTopRequest(**kwargs)

    db_request = __parse_text(_mes=message)
    if db_request is None:
        return None

    pars = {
        "db_engine": db_engine,
        "sorting_type": db_request.sorting_type,
        "top_count": db_request.top_count,
        "after_ts": db_request.after_ts,
    }
    if db_request.channel_id is None:
        req_status, messages = await get_top_messages(**pars)
    elif db_request.is_channel:
        req_status, messages = await get_top_messages_by_channel_id(
            channel_id=db_request.channel_id, **pars
        )
    else:
        req_status, messages = await get_top_messages_by_category_name(
            category_name=db_request.channel_id, **pars
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
