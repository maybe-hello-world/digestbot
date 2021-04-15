from datetime import datetime
from influxdb_client import Point
import requests as r

import config
import container

from common.extras import try_request
from config import INFLUX_API_WRITE


async def send_initial_message(user_id: str, channel_id: str) -> None:
    base_url = f"http://{config.DB_URL}/ignore/"
    answer = try_request(container.logger, r.get, base_url, params={"author_id": user_id})
    if answer.is_err():
        await container.slacker.post_to_channel(channel_id=channel_id, text=answer.unwrap_err())
        return
    answer = answer.unwrap()

    ignore_list = answer.json()
    template = container.jinja_env.get_template("ignore.json")
    result = template.render(ignore_list=ignore_list)
    await container.slacker.post_to_channel(channel_id=channel_id, blocks=result, ephemeral=True, user_id=user_id)


async def ignore_interaction_eligibility(data: dict):
    return (data.get("type", "") == "block_actions" and
            data.get("actions", [{}])[0].get("action_id", "").startswith("ignore"))


async def ignore_interaction(data: dict):
    action_id = data.get("actions", [{}])[0].get("action_id", "")
    channel_id = data.get('channel', {}).get("id", "")
    user_id = data.get("user", {}).get("id", "")
    base_url = f"http://{config.DB_URL}/ignore/"

    if action_id == "ignore_user_add":
        field = "selected_user"
        op = r.put
        message = "User <@{0}> successfully added to the ignore list."
    elif action_id == "ignore_user_remove":
        field = "value"
        op = r.delete
        message = "User <@{0}> successfully removed from the ignore list."
    else:
        container.logger.warning(f"Unknown preset interaction message: {data}")
        return

    ignore_user = data.get("actions", [{}])[0].get(field, "")
    answer = try_request(
        container.logger, op, base_url, params={'author_id': user_id, 'ignore_id': ignore_user}
    )
    answer = answer.map(lambda *x: message.format(ignore_user)).value
    await container.slacker.post_to_channel(channel_id=channel_id, text=answer)

    ignored_count = try_request(container.logger, r.get, f"http://{config.DB_URL}/ignore/count").map(lambda x: x.json())
    if ignored_count.is_ok():
        INFLUX_API_WRITE(Point("digestbot").field("ignored_total", ignored_count.unwrap()).time(datetime.utcnow()))
