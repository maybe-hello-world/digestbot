from digestbot.command_parser.argument import StringArgument
from digestbot.command_parser.command import CommandBuilder
from digestbot.command_parser.command_parser import CommandParser
from digestbot.core.db.dbengine import PostgreSQLEngine
from digestbot.core.db.dbrequest.category import get_all_categories

presets_command = CommandBuilder("presets").build()


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

presets_add_command = CommandBuilder("add").build()
presets_rm_command = CommandBuilder("rm").build()
presets_ls_command = CommandBuilder("ls").add_argument(StringArgument("scope", "local")).build()

presets_parser = CommandParser([presets_add_command, presets_rm_command, presets_ls_command], "presets")
