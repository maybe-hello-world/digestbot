import re
from enum import Enum, auto
from typing import Optional

from digestbot.core.slack_api.Slacker import Slacker
from digestbot.core.db.dbengine import PostgreSQLEngine
from digestbot.core.common import config, LoggerFactory
from digestbot.core.ui_processor.common import UserRequest
from digestbot.core.ui_processor.top_processor import __process_top_request

SYNTAX_RESPONSE = "Hello, <@{}>! I didn't understood your request, could you check your command? Thanks."

_logger = LoggerFactory.create_logger(__name__, config.LOG_LEVEL)


class __CommandType(Enum):
    """Parsed command type from user message"""

    TOP_REQUEST = auto()


def __parse_message_type(message: UserRequest) -> Optional[__CommandType]:
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


async def process_message(
    message: UserRequest, bot_name: str, api: Slacker, db_engine: PostgreSQLEngine
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
        if text_to_answer is not None:
            await api.post_to_channel(channel_id=message.channel, text=text_to_answer)

    await api.post_to_channel(
        channel_id=message.channel, text=SYNTAX_RESPONSE.format(message.user)
    )
