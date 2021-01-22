from datetime import timedelta

from common.command_parser.argument import (
    ChoiceArgument,
    TimeDeltaArgument,
    ExactArgument,
    StringArgument,
)
from common.command_parser.command import CommandBuilder
from common.command_parser.command_parser import CommandParser
from ..top.top_command import top_arguments

timers_add_arguments = (
    ChoiceArgument(
        name="cyclicity", choices=["every"], default="every"  # schedule once?
    ),
    TimeDeltaArgument(name="timer_freq", default=timedelta(days=1)),
)
timers_add_command = (
    CommandBuilder("add")
    .extend_with_arguments(timers_add_arguments)
    .add_argument(ExactArgument(name="top_placeholder", value="top"))
    .extend_with_arguments(top_arguments)
    .build()
)
timers_ls_command = CommandBuilder("ls").build()
timers_rm_command = (
    CommandBuilder("rm").add_argument(StringArgument("timer_name", None)).build()
)
timers_parser = CommandParser(
    [timers_add_command, timers_ls_command, timers_rm_command], "timers"
)
