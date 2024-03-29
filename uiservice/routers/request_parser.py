from datetime import datetime

from influxdb_client import Point

import container
from config import INFLUX_API_WRITE, QNA_PRESENTED
from . import top, timer, preset, helper, qna, ignore


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

    INFLUX_API_WRITE(Point("digestbot").field("overall_requests", 1).time(datetime.utcnow()))

    if text.startswith("help"):
        await helper.process_message(channel, text)
    elif text == "top":
        await top.send_initial_message(user_id, channel)
    elif text == "timers":
        await timer.send_initial_message(user_id, channel)
    elif text == "presets":
        await preset.send_initial_message(user_id, channel)
    elif text == "ignore":
        await ignore.send_initial_message(user_id, channel)
    elif text == "qna" and QNA_PRESENTED:    # only if QnA provided
        await qna.send_initial_message(user_id, channel, message.get('trigger_id', ""))
    else:
        template = container.jinja_env.get_template("syntax_response.json")
        result = template.render(qna_presented=QNA_PRESENTED)
        await container.slacker.post_to_channel(channel_id=channel, blocks=result, ephemeral=True, user_id=user_id)
