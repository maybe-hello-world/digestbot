from digestbot.core.command_parser.command_parser import CommandParser
from digestbot.core.common import config, LoggerFactory
from digestbot.core.db.dbengine import PostgreSQLEngine
from digestbot.core.slack_api.Slacker import Slacker
from digestbot.core.ui_processor.common import UserRequest
from digestbot.core.ui_processor.top_processor import (
    top_command,
    TopCommandArgs,
    process_top_request,
)

SYNTAX_RESPONSE = "Hello, <@{}>! I didn't understood your request, could you check your command? Thanks."

_logger = LoggerFactory.create_logger(__name__, config.LOG_LEVEL)


parser = CommandParser([top_command])


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
    parse_result = parser.parse(message.text)
    if parse_result.command == top_command.name:
        top_command_args = TopCommandArgs.from_dict(parse_result.args)
        text_to_answer = await process_top_request(top_command_args, db_engine)
        await api.post_to_channel(channel_id=message.channel, text=text_to_answer)
    else:
        await api.post_to_channel(
            channel_id=message.channel, text=SYNTAX_RESPONSE.format(message.user)
        )
