import re
from dataclasses import dataclass
from enum import Enum, auto
from datetime import datetime, timedelta
import time
from decimal import Decimal

from digestbot.core.db.dbengine import PostgreSQLEngine
from digestbot.core.SlackAPI.Slacker import Slacker
from typing import Optional, List

from digestbot.core.common.DataClasses import DBTopRequest
from digestbot.core.common.Enums import SortingType, SORTING_TYPE_MAPPER
from digestbot.core.common import config, LoggerFactory
from digestbot.app.dbrequest.message import (
    get_top_messages,
    get_top_messages_by_channel_id,
    get_top_messages_by_category_name,
)
from digestbot.core.db.models import Message

SYNTAX_RESPONSE = "Hello, <@{}>! I didn't understood your request, could you check your command? Thanks."


class __CommandType(Enum):
    """Parsed command type from user message"""

    TOP_REQUEST = auto()


@dataclass(frozen=True)
class __UserRequest:
    text: str  # user text
    user: str  # author's username
    channel: str  # ID of channel from Slack
    ts: str  # timestamp of the message
    is_im: bool  # is it private message to bot (or in public channel)


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
            x.text[:15],
            x.reply_count,
            x.reply_users_count,
            x.reactions_rate,
            x.link,
        )
        for i, x in enumerate(messages, start=1)
    )
    return "\n\n".join(messages)


def __parse_message_type(message: __UserRequest) -> Optional[__CommandType]:
    """
    Parse message and return type of the command from the message

    :param message: request from user
    :return: command type or None if not parsed
    """

    # 'top ...' or '<@CWEHB72K> top ...'
    if re.match(r"(<@[A-Z\d]+> )?top", message.text.strip()):
        return __CommandType.TOP_REQUEST
    else:
        return None


async def __process_top_request(
    message: __UserRequest, db_engine: PostgreSQLEngine
) -> str:
    """
    Parse TOP_REQUEST command from user message

    :param message: user message
    :param db_engine: db engine for database operations
    :return: formatted message if parsed, None otherwise
    """

    def __parse_text(_mes: __UserRequest) -> Optional[DBTopRequest]:
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
        channel_pattern = r"(?:<#)?[\d_a-zA-Z\|]+>?"  # channel or preset name
        sorting_types = " " + "| ".join(
            SORTING_TYPE_MAPPER.keys()
        )  # one of several sorting types
        command_pattern = fr"top(?P<amount> [\d]+)?(?P<channel> {channel_pattern})?(?P<sorting>{sorting_types})?"
        parse_result = re.fullmatch(command_pattern, command_text)

        if parse_result is None:
            return None
        amount = parse_result.group("amount")
        channel = parse_result.group("channel")
        sorting = parse_result.group("sorting")

        if amount is not None:
            try:
                amount = int(amount.strip())
            except TypeError as e:
                _logger.exception(e)
                amount = None

        if sorting is not None:
            try:
                sorting = SORTING_TYPE_MAPPER[sorting.strip()]
                sorting = SortingType(sorting)
            except (ValueError, KeyError) as e:
                _logger.exception(e)
                sorting = None

        is_channel = False
        if channel is not None:
            channel = channel.strip()
            if channel.startswith("<#"):
                is_channel = True
                channel = channel.strip("<>#")
                channel = channel[: channel.index("|")]  # AJLK323BKJ|general

        # TODO: IMPORTANT!! parse initial time from user request
        ts = datetime.now() - timedelta(days=1)
        ts = Decimal(time.mktime(ts.timetuple()))

        kwargs = {
            "after_ts": ts,
            "amount": amount,
            "is_channel": is_channel,
            "channel": channel,
            "sorting_type": sorting,
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        return DBTopRequest(**kwargs)

    db_request = __parse_text(_mes=message)
    if db_request is None:
        return SYNTAX_RESPONSE.format(message.user)

    pars = {
        "db_engine": db_engine,
        "sorting_type": db_request.sorting_type,
        "top_count": db_request.amount,
        "after_ts": db_request.after_ts,
    }
    if db_request.channel is None:
        req_status, messages = await get_top_messages(**pars)
    elif db_request.is_channel:
        req_status, messages = await get_top_messages_by_channel_id(
            channel_id=db_request.channel, **pars
        )
    else:
        req_status, messages = await get_top_messages_by_category_name(
            category_name=db_request.channel, **pars
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


async def process_message(
    message: __UserRequest, bot_name: str, api: Slacker, db_engine: PostgreSQLEngine
) -> None:
    """
    Parse user request and answer
    :param message: user message to be processed
    :param bot_name: current name of the bot
    :param api: api class for usage
    :param db_engine: db engine for database operations
    """

    # do not answer on own messages
    if message.user == bot_name:
        return

    # answer only on direct messages and mentions in chats
    if api.user_id not in message.text and not message.is_im:
        return

    # parse message and prepare message to answer
    mtype = __parse_message_type(message=message)
    if mtype == __CommandType.TOP_REQUEST:
        text_to_answer = await __process_top_request(
            message=message, db_engine=db_engine
        )
    else:
        text_to_answer = SYNTAX_RESPONSE.format(message.user)

    await api.post_to_channel(channel_id=message.channel, text=text_to_answer)


_logger = LoggerFactory.create_logger(__name__, config.LOG_LEVEL)
