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
    elif command == "timers":
        return timers_help()
    else:
        return "Help for this command not found. Type `help` for general help message."


def general_help() -> str:
    return (
        "Hi! I'm a bot who can send you a top messages from given channels.\n"
        "For asking help for any command type: `help command_name`\n\n"
        "Available commands:\n"
        "`top`\n"
        "`presets`\n"
        "`timers`"
    )


def presets_help() -> str:
    return (
        "Return all available presets with channels.\n\n"
        "Syntax: `presets`\n\n"
        "Examples:\n"
        "`presets`"
    )


def timers_help() -> str:
    return (
        "Allows you to add, remove or list timers which send you top results on schedule.\n\n"
        "*timers add* - schedule new timer with given top command and timedelta\n"
        "Syntax: `timers add [cyclicity=every] [time=1d] top <top_command_arguments>`\n"
        "All arguments are positional only.\n"
        "Arguments:\n"
        "`cyclicity`: now only `every` is available (send results every N), in future once and more flexible schedule "
        "could be added\n"
        "`time`: how often to send you top results, possible values: (int)(h|d|w), "
        "where h - hours, d - days, w - weeks\n"
        "`top`: mandatory keyword to explicitly state top command\n"
        "`<top_command_arguments>`: arguments of top command in corresponding order, see `help top` for more details\n"
        "Examples:\n\n"
        "Create timer with default time delta and default top command\n"
        "`timers add top`\n\n"
        "Create timer for every 3h with messages from kek preset\n"
        "`timers add every 3h top kek`\n"
        "\n\n"
        "*timers ls* - lists all your timers\n"
        "Syntax: `timers ls`\n"
        "Examples:\n"
        "`timers ls`\n"
        "\n\n"
        "*timers rm* - removes one of your timers\n"
        "Syntax: `timers rm <timer_name>`\n"
        "`timer_name`: name of timer (created automatically)\n"
        "Example:\n"
        "`timers rm oncx`"
    )


def top_help() -> str:
    return (
        "Returns top messages from asked channels.\n\n"
        "Syntax: `top [N=5] [time=1d] [sorting_method=replies] [channel=#_top|preset_name]`\n\n"
        "All arguments are positional only.\n"
        "`N`: amount of messages, int\n"
        "`time`: delta between desired oldest message and now. Possible values: (int)(m|h|d|w), where m - minutes,"
        "h - hours, d - days, w - weeks\n"
        "`sorting_method`: messages sorting method, one of: replies, length, reactions\n"
        "`channel`: channel link (with #) or preset name\n\n"
        "Examples:\n\n"
        "Get top messages over all channels:\n"
        "`top`\n\n"
        "Get top messages over all channels for last 12 hours:\n"
        "`top 12h`\n\n"
        "Get 10 top messages from #general for last 3 days:\n"
        "`top 10 3d #general`\n\n"
        "Get top 3 messages from #general for last 24 hours (1 day) sorted by reactions rate:\n"
        "`top 3 1d reactions #general`"
    )
