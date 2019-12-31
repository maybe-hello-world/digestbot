from digestbot.command_parser.argument import StringArgument
from digestbot.command_parser.command import CommandBuilder
from digestbot.command_parser.command_parser import CommandParser

presets_command = CommandBuilder("presets").build()
presets_add_command = CommandBuilder("add").build()
presets_rm_command = CommandBuilder("rm").build()
presets_ls_command = (
    CommandBuilder("ls").add_argument(StringArgument("scope", "local")).build()
)
presets_parser = CommandParser(
    [presets_add_command, presets_rm_command, presets_ls_command], "presets"
)
