import re
import logging
import sys
from dataclasses import dataclass
from enum import Enum, auto

from digestbot.core.SlackAPI.Slacker import Slacker
from typing import Optional

from digestbot.core.common.DataClasses import DBTopRequest
from digestbot.core.common.Enums import SortingType

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


async def __process_top_request(message: __UserRequest) -> str:
    """
    Parse TOP_REQUEST command from user message

    :param message: user message
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
        channel_pattern = r"#?[\d_a-zA-Z]+"  # channel or preset name
        sorting_types = " " + "| ".join(
            [x.value for x in SortingType]
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
                sorting = SortingType(sorting.strip())
            except ValueError as e:
                _logger.exception(e)
                sorting = None

        if channel is not None:
            channel = channel.strip()

        kwargs = {"amount": amount, "channel": channel, "sorting_type": sorting}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        return DBTopRequest(**kwargs)

    db_request = __parse_text(_mes=message)
    if db_request is None:
        return SYNTAX_RESPONSE.format(message.user)

    # TODO: call DB request and get answer
    formatted_message = (
        "Current top is in progress. Stay tuned. Technical info: " + repr(db_request)
    )

    return formatted_message


async def process_message(message: __UserRequest, bot_name: str, api: Slacker) -> None:
    """
    Parse user request and answer
    :param message: user message to be processed
    :param bot_name: current name of the bot
    :param api: api class for usage
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
        text_to_answer = await __process_top_request(message=message)
    else:
        text_to_answer = SYNTAX_RESPONSE.format(message.user)

    await api.post_to_channel(channel_id=message.channel, text=text_to_answer)


_logger = logging.getLogger("UserRequestParser")
_logger.setLevel(logging.INFO)
__handler = logging.StreamHandler(sys.stdout)
__formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%m.%d.%Y-%I:%M:%S"
)
__handler.setFormatter(__formatter)
_logger.addHandler(__handler)
