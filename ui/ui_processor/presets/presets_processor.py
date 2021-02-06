import json

import requests as r

from common.LoggerFactory import create_logger
from config import LOG_LEVEL
from .presets_command import presets_add_command, presets_ls_command, presets_rm_command
from ..common import parse_channel_id
from common.command_parser.parse_result import CommandParseResult

NO_NAME_PASSED_MESSAGE = "You have not specify preset name"
NO_CHANNELS_PASSED_MESSAGE = "You have not specify channels name for preset. Please specify them"
PRESET_OVERRIDE_WARNING_MESSAGE = "Your preset name is the same as global preset. It will override global preset"
BAD_CHANNEL_PASSED_MESSAGE = "You have passed incorrect channel name. This channel does not exist"

_logger = create_logger(__name__, LOG_LEVEL)


def log_erroneous_answer(answer: r.Response) -> None:
    if answer.status_code >= 500:
        _logger.warning(answer.text)


async def process_presets(presets_command_args: CommandParseResult, user_id: str, db_service: str) -> str:
    if presets_command_args.command == presets_add_command.name:
        return await process_presets_add(presets_command_args, user_id, db_service)
    elif presets_command_args.command == presets_ls_command.name:
        return await process_presets_ls(presets_command_args, user_id, db_service)
    elif presets_command_args.command == presets_rm_command.name:
        return await process_presets_rm(presets_command_args, user_id, db_service)


async def process_presets_add(presets_command_args: CommandParseResult, user_id: str, db_service: str):
    base_url = f"http://{db_service}/category/"

    channels = set([parse_channel_id(channel) for channel in presets_command_args.args["channels"]])
    name = presets_command_args.args["name"]
    if not name:
        return NO_NAME_PASSED_MESSAGE
    if not channels:
        return NO_CHANNELS_PASSED_MESSAGE
    if None in channels:
        return BAD_CHANNEL_PASSED_MESSAGE

    # get global categories
    answer = r.get(base_url, timeout=10)
    if answer.status_code != 200:
        log_erroneous_answer(answer)
        return "Could not receive global categories. Possibly database connection problems."
    global_presets = answer.json()

    answer = r.put(base_url, params={'user_id': user_id, 'name': name}, data=json.dumps(list(channels)), timeout=10)
    if answer.status_code != 200:
        log_erroneous_answer(answer)
        return answer.text

    result_message = ""

    if name in [preset.name for preset in global_presets]:
        result_message = PRESET_OVERRIDE_WARNING_MESSAGE

    result_message += f"\n\nSuccessfully added preset `{name}`"
    return result_message


async def process_presets_ls(presets_command_args: CommandParseResult, user_id: str, db_service: str):
    base_url = f"http://{db_service}/category/"

    include_global = presets_command_args.args["scope"] != "local"

    answer = r.get(base_url, params={'user_id': user_id, 'include_global': include_global}, timeout=10)
    if answer.status_code != 200:
        log_erroneous_answer(answer)
        return answer.text
    presets_list = answer.json()

    if not presets_list:
        return "No available presets for now. You can create your own preset with `presets add` command"

    answer = "Available presets:\n\n"
    answer += "\n".join(
        f"`{x.name}`{' (global)' if x.username is None else ''}: " f"{', '.join(f'<#{c}>' for c in x.channel_ids)}"
        for x in presets_list
    )
    return answer


async def process_presets_rm(presets_command_args: CommandParseResult, user_id: str, db_service: str):
    base_url = f"http://{db_service}/category/"

    name = presets_command_args.args["name"]
    if not name:
        return NO_NAME_PASSED_MESSAGE

    answer = r.delete(base_url, params={'user_id': user_id, 'name': name}, timeout=10)
    if answer.status_code != 200:
        log_erroneous_answer(answer)
        return answer.text
    category = answer.json()

    if not category:
        return "Preset with specified name is not found. You can find list of your presets with `presets ls` command"

    return f"Successfully removed preset `{category.name}`"
