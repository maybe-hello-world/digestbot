from digestbot.command_parser.argument import StringArgument, StringMultiArgument
from digestbot.command_parser.command import CommandBuilder
from digestbot.command_parser.command_parser import CommandParser

presets_command = CommandBuilder("presets").build()

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
