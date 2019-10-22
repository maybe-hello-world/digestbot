from typing import Any, Dict

from digestbot.command_parser.argument import StringArgument
from digestbot.command_parser.command import CommandBuilder

help_command = (
    CommandBuilder("help").add_argument(StringArgument("command", default=None)).build()
)


def process_help_request(args: Dict[str, Any]) -> str:
    command = args["command"]
    if command is None:
        return general_help()
    elif command == "top":
        return top_help()
    elif command == "presets":
        return presets_help()
    else:
        return "Help for this command not found. Type `help` for general help message."


def general_help() -> str:
    return (
        "Hi! I'm a bot who can send you a top messages from given channels.\n"
        "For asking help for any command type: `help command_name`\n\n"
        "Available commands:\n"
        "`top`\n"
        "`presets`"
    )


def presets_help() -> str:
    return (
        "Return all available presets with channels.\n\n"
        "Syntax: `presets`\n\n"
        "Examples:\n"
        "`presets`"
    )


def top_help() -> str:
    return (
        "Returns top messages from asked channels.\n\n"
        "Syntax: `top [N=10] [time=1d] [sorting_method=replies] [channel=#_top|preset_name]`\n\n"
        "All arguments are positional only.\n"
        "N: amount of messages, int\n"
        "time: delta between desired oldest message and now. Possible values: (int)(m|h|d|w), where m - minutes,"
        "h - hours, d - days, w - weeks\n"
        "sorting_method: messages sorting method, one of: replies, length, reactions\n"
        "channel: channel link (with #) or preset name\n\n"
        "Examples:\n"
        "`top`\n"
        "`top 12h`\n"
        "`top 10 3d #general`\n"
        "`top 3 1d reactions #general`"
    )
