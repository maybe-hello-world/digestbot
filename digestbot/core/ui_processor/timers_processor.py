from datetime import timedelta

from digestbot.core import Timer
from digestbot.command_parser.argument import (
    StringArgument,
    ChoiceArgument,
    TimeDeltaArgument,
    IntArgument,
    ExactArgument,
)
from digestbot.command_parser.command import CommandBuilder
from digestbot.core.ui_processor.top_processor import top_arguments

timers_arguments = (
    ChoiceArgument(
        name="cyclicity", choices=["every"], default="every"  # schedule once?
    ),
    TimeDeltaArgument(name="time", default=timedelta(days=1)),
)

timers_command = (
    CommandBuilder("schedule")
    .extend_with_arguments(timers_arguments)
    .add_argument(ExactArgument(name="top", value="top"))
    .extend_with_arguments(top_arguments)
    .build()
)
