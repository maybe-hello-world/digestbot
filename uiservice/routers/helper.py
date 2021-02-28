import container


def general_help() -> str:
    return (
        "Hi! I'm a bot who can send you a top messages from given channels.\n"
        "For asking help for any command type: `help command_name`\n\n"
        "Available commands:\n"
        "`top`\n"
        "`presets`\n"
        "`timers`"
    )


def unrecognized_help() -> str:
    return "Help for this command not found. Type `help` for general help message."


def presets_help() -> str:
    return (
        "Allows you to add, remove or list your own presets. "
        "Preset is a set that contains references to one or more channels. "
        "There are two types of presets: global and local:\n"
        "* global - predefined presets (by bot authors, contributions are welcome :) )\n"
        "* local - presets that you can create\n\n"
        "With help of presets you can union channels in categories that may interest you\n"
    )


def timers_help() -> str:
    return "Allows you to add, remove or list timers which send you top results on schedule."


def top_help() -> str:
    return "Returns top messages from requested channels."


async def process_message(channel_id: str, text: str):
    help_answer = unrecognized_help()
    text = text.strip()

    if text == "help":
        help_answer = general_help()
    elif text == "help presets":
        help_answer = presets_help()
    elif text == "help top":
        help_answer = top_help()
    elif text == "help timers":
        help_answer = timers_help()

    await container.slacker.post_to_channel(channel_id=channel_id, text=help_answer)
