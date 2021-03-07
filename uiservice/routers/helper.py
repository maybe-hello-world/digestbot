import container


def general_help() -> str:
    template = container.jinja_env.get_template("help_response.json")
    return template.render()


def unrecognized_help() -> str:
    return "Help for this command not found. Type `help` for general help message."


def presets_help() -> str:
    return (
        "Allows you to add, remove or list your own presets. "
        "Preset is a set that contains references to one or more channels. "
        "There are two types of presets: global and local:\n"
        "* global - predefined presets (by bot authors, contributions are welcome :) )\n"
        "* local - presets that you can create\n\n"
        "With help of presets you can union channels in presets that may interest you and then specify preset "
        "instead of subset of channels for simplicity."
    )


def timers_help() -> str:
    return (
        "Allows you to add, remove or list timers.\n"
        "These timers could be created for providing you top messages on schedule, like every day or week.\n"
        "You can configure different settings and specify channels or presets from which to provide messages.\n"
        "It's not so hard, so we encourage you to try :)"
    )


def top_help() -> str:
    return (
        "Returns top messages from requested channels. \n"
        "Top is defined by selecting messages with given criteria and sorting them by one of the available methods.\n"
        "Just ask `top` and try it by yourself :)."
    )


def qna_help() -> str:
    return (
        "Q&A ODS.ai team provides an API for intellectual search over ODS.ai Slack workspace messages. \n"
        "Via this bot you can use this API and benefit from modern NLP approaches working just for you ^^. \n"
        "You can contact the Q&A ODS.ai team via @submaps in Slack."
    )


async def process_message(channel_id: str, text: str):
    help_answer = {"text": unrecognized_help()}
    text = text.strip().replace("+", " ")

    if text == "help":
        help_answer = {"blocks": general_help()}
    elif text == "help presets":
        help_answer = {"text": presets_help()}
    elif text == "help top":
        help_answer = {"text": top_help()}
    elif text == "help timers":
        help_answer = {"text": timers_help()}
    elif text == "help qna":
        help_answer = {"text": qna_help()}

    await container.slacker.post_to_channel(channel_id=channel_id, **help_answer)
