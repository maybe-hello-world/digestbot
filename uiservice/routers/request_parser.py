import container
from . import top, timer, preset, helper

SYNTAX_RESPONSE = (
    "Oops! <@{}>, I didn't understood your request, could you check your command? "
    "Or ask for `help` if you don't know what to do. Thanks."
)


async def process_message(message: dict) -> None:
    """
    Parse user request and answer
    :param message: user message to be processed
    """

    # start with simple parser
    text = message.get("text", "").lower().strip()
    user_id = message.get("user", "")
    channel = message.get("channel", "")
    if text.startswith("help"):
        await helper.process_message(channel, text)
    elif text == "top":
        await top.send_initial_message(user_id, channel)
    elif text == "timers":
        await timer.send_initial_message(user_id, channel)
    elif text == "presets":
        await preset.send_initial_message(user_id, channel)
    else:
        await container.slacker.post_to_channel(channel_id=channel, text=SYNTAX_RESPONSE.format(user_id))
