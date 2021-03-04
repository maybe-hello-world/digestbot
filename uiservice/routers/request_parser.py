import container
from . import top, timer, preset, helper, qna


async def request_picker_eligibility(data: dict):
    return data.get("type", "") == "block_actions" and data.get("actions", [{}])[0].get("block_id",
                                                                                        "") == "command_picker"


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
    elif text == "qna":
        await qna.send_initial_message(user_id, channel, message.get('trigger_id', ""))
    else:
        template = container.jinja_env.get_template("syntax_response.json")
        result = template.render()
        await container.slacker.post_to_channel(channel_id=channel, blocks=result, ephemeral=True, user_id=user_id)
