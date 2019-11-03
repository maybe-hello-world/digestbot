from digestbot.command_parser.argument import StringArgument, MultiArgument, StringMultiArgument
from digestbot.command_parser.command import CommandBuilder
from digestbot.command_parser.command_parser import CommandParser
from digestbot.command_parser.parse_result import CommandParseResult
from digestbot.core.db.dbengine import PostgreSQLEngine
from digestbot.core.db.dbrequest.category import get_all_categories, get_categories, add_or_update_category, \
    remove_category
from digestbot.core.ui_processor.common import parse_channel_id

presets_command = CommandBuilder("presets").build()


NO_NAME_PASSED_MESSAGE = "You have not specify preset name"
NO_CHANNELS_PASSED_MESSAGE = "You have not specify channels name for preset. Please specify them"
PRESET_OVERRIDE_WARNING_MESSAGE = "Your preset name is the same as global preset. It will override global preset"
BAD_CHANNEL_PASSED_MESSAGE = "You have passed incorrect channel name. This channel does not exist"


async def process_presets_request(db_engine: PostgreSQLEngine) -> str:
    status, presets_list = await get_all_categories(db_engine)

    if not status:
        return "Oops, database is unavailable now. Please, try later or notify bot creators."
    if not presets_list:
        return "No available presets for now :("

    answer = "Available presets:\n\n"
    answer += "\n".join(
        f"`{x.name}`: " f"{', '.join(f'<#{c}>' for c in x.channel_ids)}"
        for x in presets_list
    )
    return answer

presets_add_command = (
    CommandBuilder("add")
        .add_argument(StringArgument("name"))
        .add_argument(StringMultiArgument("channels"))
        .build()
)
presets_rm_command = (
    CommandBuilder("rm")
        .add_argument(StringArgument("name"))
        .build()
)
presets_ls_command = (
    CommandBuilder("ls")
        .add_argument(StringArgument("scope", "global"))
        .build()
)

presets_parser = CommandParser([presets_add_command, presets_rm_command, presets_ls_command], "presets")


async def process_presets(presets_command_args: CommandParseResult, user_id: str, db_engine: PostgreSQLEngine) -> str:
    if presets_command_args.command == presets_add_command.name:
        return await process_presets_add(presets_command_args, user_id, db_engine)
    elif presets_command_args.command == presets_ls_command.name:
        return await process_presets_ls(presets_command_args, user_id, db_engine)
    elif presets_command_args.command == presets_rm_command.name:
        return await process_presets_rm(presets_command_args, user_id, db_engine)


async def process_presets_add(presets_command_args: CommandParseResult, user_id: str, db_engine: PostgreSQLEngine):
    channels = set([parse_channel_id(channel) for channel in presets_command_args.args["channels"]])
    name = presets_command_args.args["name"]
    if not name:
        return NO_NAME_PASSED_MESSAGE
    if not channels:
        return NO_CHANNELS_PASSED_MESSAGE
    if None in channels:
        return BAD_CHANNEL_PASSED_MESSAGE

    global_presets = await get_categories(db_engine, None)

    result_message = ""

    if name in [preset.name for preset in global_presets]:
        result_message += PRESET_OVERRIDE_WARNING_MESSAGE

    category = await add_or_update_category(db_engine, user_id, name, list(channels))
    category = category

    result_message += f"\n\nSuccessfully added preset `{category.name}`"
    return result_message


async def process_presets_ls(presets_command_args: CommandParseResult, user_id: str, db_engine: PostgreSQLEngine):
    include_global = presets_command_args.args["scope"] != "local"
    presets_list = await get_categories(db_engine, user_id, include_global)

    if not presets_list:
        return "No available presets for now. You can create your own preset with `presets add` command"

    answer = "Available presets:\n\n"
    answer += "\n".join(
        f"`{x.name}`{' (global)' if x.username is None else ''}: " f"{', '.join(f'<#{c}>' for c in x.channel_ids)}"
        for x in presets_list
    )
    return answer


async def process_presets_rm(presets_command_args: CommandParseResult, user_id: str, db_engine: PostgreSQLEngine):
    name = presets_command_args.args["name"]
    if not name:
        return NO_NAME_PASSED_MESSAGE

    category = await remove_category(db_engine, user_id, name)

    if not category:
        return "Preset with specified name is not found. You can find list of your presets with `presets ls` command"

    return f"Successfully removed preset `{category.name}`"
