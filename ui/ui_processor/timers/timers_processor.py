import random
import string
from datetime import datetime
from typing import Any, Dict, List

from common.LoggerFactory import create_logger
from common.db.models import Timer
from common.db.dbengine.PostgreSQLEngine import PostgreSQLEngine
from common.command_parser.parse_result import CommandParseResult
from config import TIMERS_LIMIT, LOG_LEVEL

from .timers_command import (
    timers_add_command,
    timers_ls_command,
    timers_rm_command,
)
from common.db.dbrequest.timer import (
    check_timer_existence,
    remove_timer,
    list_timers,
    insert_timer,
)

_logger = create_logger(__name__, LOG_LEVEL)


async def ls_timers(username: str, db_engine: PostgreSQLEngine):
    """
    List user's timers
    :param username: username of the requester
    :param db_engine: db engine for work
    :return: formatted string with timers listing
    """

    def _pretty_format(timers_list: List[Timer]):
        template = (
            "{}. Timer name: {}, top command: {}\n" "Delta: {}, next start: {} UTC"
        )

        messages = (
            template.format(
                i,
                x.timer_name,
                x.top_command,
                x.delta,
                x.next_start.strftime("%Y-%m-%d %H:%M:%S"),
            )
            for i, x in enumerate(timers_list, start=1)
        )
        return "\n\n".join(messages)

    result, timers = await list_timers(db_engine=db_engine, username=username)
    if not result:
        _logger.warning(
            "Couldn't list timers from the database, possible DB connection problems."
        )
        return (
            "Couldn't get list of timers from the database. Possible connection problems. "
            "Please, try later or contact bot developer team."
        )
    if not timers:
        return "No timers to list. Let's create one!"
    return _pretty_format(timers)


async def add_timer(
    channel_id: str,
    username: str,
    args: Dict[str, Any],
    original_text: str,
    db_engine: PostgreSQLEngine,
) -> str:
    """
    Create (or not if any errors) timer for user and notify about the result (success or failure)

    :param channel_id: channel from which request comes
    :param username: username of user who requested to create a timer
    :param args: parsed args from command parser
    :param original_text: original message text from what top command is obtained
    :param db_engine: db engine to work with
    :return: formatted message to answer the user
    """
    if args["top_placeholder"] is None:
        return (
            "Top command should be explicitly presented. "
            "Please, see `help timers` for syntax and arguments."
        )

    timer_delta = args["timer_freq"]
    if timer_delta.total_seconds() < 3600:
        return (
            "Timers with frequencies less than 1 hour are not allowed. "
            "Please, specify timer with greater frequency."
        )

    timer_exist, timer_name = True, ""
    while timer_exist:  # TODO: remove while and take out to separate module
        timer_name = f"{''.join(random.choices(string.ascii_lowercase, k=4))}"
        timer_check_success, timer_exist = await check_timer_existence(
            db_engine=db_engine, timer_name=timer_name, username=username
        )
        if not timer_check_success:
            _logger.warning("Couldn't check timer existence in database.")

    # TODO: now it's just hack, should be replaced somehow
    #  maybe return from commandparser original information?
    str_top_command = original_text[original_text.index("top") :]

    next_start = datetime.utcnow() + timer_delta
    timer = Timer(
        channel_id=channel_id,
        username=username,
        timer_name=timer_name,
        delta=timer_delta,
        next_start=next_start,
        top_command=str_top_command,
    )

    result = await insert_timer(
        db_engine=db_engine, timer=timer, max_timers_count=TIMERS_LIMIT
    )
    if result is None:
        _logger.warning(f"Unsuccessful database timer insert, timer: {timer}")
        return (
            "Some error occurred during timer creation. "
            "Please, try later or notify developer team about this situation. Thanks."
        )
    elif result:
        return (
            f"Timer {timer.timer_name} successfully created. "
            f"Next start time: {timer.next_start.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
    else:
        return (
            "Maximum number of timers for this user achieved. "
            "Please, consider removing one of your existing timers to be available to add another one. "
            f"Current limit: {TIMERS_LIMIT} timers."
        )


async def rm_timer(username: str, args: Dict[str, Any], db_engine: PostgreSQLEngine):
    """
    Try to remove timer specified by the user
    :param username: username of the requester
    :param args: parsed arguments
    :param db_engine: db engine to work with
    :return: formatted string with operation status
    """
    timer_name = args["timer_name"]
    if timer_name is None:
        return (
            "Timer name to delete should be explicitly specified. "
            "Please specify timer name or type `help timers` to get additional information."
        )

    check_status, timer_exists = await check_timer_existence(
        db_engine=db_engine, timer_name=timer_name, username=username
    )
    if check_status and not timer_exists:
        return (
            "Couldn't find timer with such name. "
            "If you are sure that it's a bug, please contact bot developer team. Thanks."
        )
    if not check_status:
        _logger.warning("Couldn't check timer existence in the database.")

    result = await remove_timer(
        db_engine=db_engine, timer_name=timer_name, username=username
    )
    if result:
        return f"Timer {timer_name} successfully deleted."
    else:
        return (
            f"Some error occurred. Timer {timer_name} possibly is not deleted. "
            f"Please, check with `timers ls` and contact developers team. Thanks."
        )


async def process_timers_request(
    channel_id: str,
    username: str,
    result: CommandParseResult,
    original_text: str,
    db_engine: PostgreSQLEngine,
) -> str:
    """
    Dispatches timer requests to corresponding methods

    :param channel_id: channel from which request comes
    :param username: username of user who requested to create a timer
    :param result: parsed result of the command
    :param original_text: original message text from what top command is obtained
    :param db_engine: db engine to work with
    :return: formatted message to answer the user
    """

    if result.sub_parser_result is None:
        return (
            "Couldn't parse the request."
            " Please, check the syntax and type `help timers` for additional information."
        )
    command_name = result.sub_parser_result.command
    if command_name == timers_add_command.name:
        return await add_timer(
            channel_id=channel_id,
            username=username,
            args=result.sub_parser_result.args,
            original_text=original_text,
            db_engine=db_engine,
        )
    elif command_name == timers_ls_command.name:
        return await ls_timers(username=username, db_engine=db_engine)
    elif command_name == timers_rm_command.name:
        return await rm_timer(
            username=username, args=result.sub_parser_result.args, db_engine=db_engine
        )
    else:
        return "Sub-command not found. Please check syntax or read `help timers` and try again."
