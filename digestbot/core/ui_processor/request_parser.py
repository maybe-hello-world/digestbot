from digestbot.command_parser.command_parser import CommandParser
from digestbot.command_parser.exception import TooManyArgumentsError
from digestbot.core.common import config, LoggerFactory
from digestbot.core.db.dbengine.PostgreSQLEngine import PostgreSQLEngine
from digestbot.core.slack_api.Slacker import Slacker
from digestbot.core.ui_processor.common import UserRequest
from digestbot.core.ui_processor.top.top_processor import process_top_request
from digestbot.core.ui_processor.top.top_command import top_command, TopCommandArgs
from digestbot.core.ui_processor.help_processor import (
    help_command,
    process_help_request,
)
from digestbot.core.ui_processor.presets.presets_processor import (
    process_presets_request,
)
from digestbot.core.ui_processor.presets.presets_command import (
    presets_command,
    presets_parser,
    process_presets)

SYNTAX_RESPONSE = (
    "Oops! <@{}>, I didn't understood your request, could you check your command? "
    "Or ask for `help` if you don't know what to do. Thanks."
)

_logger = LoggerFactory.create_logger(__name__, config.LOG_LEVEL)


parser = CommandParser(
    [top_command, help_command, presets_command],
    sub_parsers=[presets_parser, timers_parser],
)


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
    try:
        parse_result = parser.parse(message.text)

        if not parse_result:
            text_to_answer = SYNTAX_RESPONSE.format(message.user)
        elif parse_result.command == top_command.name:
            top_command_args = TopCommandArgs.from_dict(parse_result.args)
            text_to_answer = await process_top_request(top_command_args, db_engine, message.user)
        elif parse_result.command == help_command.name:
            text_to_answer = process_help_request(parse_result.args)
        elif parse_result.is_sub_parser(presets_parser.name):
            text_to_answer = await process_presets(parse_result.sub_parser_result, message.user, db_engine)
        elif parse_result.command == presets_command.name:
            text_to_answer = await process_presets_request(db_engine)
        elif parse_result.command == timers_parser.name:
            text_to_answer = await process_timers_request(
                channel_id=message.channel,
                username=message.user,
                original_text=message.text,
                result=parse_result,
                db_engine=db_engine,
            )
        else:
            text_to_answer = SYNTAX_RESPONSE.format(message.user)
        await api.post_to_channel(channel_id=message.channel, text=text_to_answer)
    except TooManyArgumentsError as exception:
        await api.post_to_channel(channel_id=message.channel, text=str(exception))
    except PostgresError as exception:
        _logger.exception(exception)
        await api.post_to_channel(channel_id=message.channel,
                                  text="Sorry. We have problems with database! Please contact developers")
