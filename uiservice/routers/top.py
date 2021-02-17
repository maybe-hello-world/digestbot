import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

import requests as r

import config
from common.models import Message
from extras import try_parse_int, log_erroneous_answer
import container


def __pretty_top_format(messages: List[Message]) -> str:
    """
    Create pretty formatted output of top slack messages.

    :param messages: list of slack messages from DB
    :return: string to be send to the channel
    """
    template = (
        "{}. <@{}> | <#{}>\n"
        "{}...\n"
        "Replies: {} from {} users. Reactions rate: {}.\n"
        "Link: {}"
    )
    messages = (
        template.format(
            i,
            x.username,
            x.channel_id,
            x.text[:200],
            x.reply_count,
            x.reply_users_count,
            round(x.reactions_rate, 2),
            x.link,
        )
        for i, x in enumerate(messages, start=1)
    )
    return "\n\n\n".join(messages)


async def send_initial_message(user_id: str, channel_id: str) -> None:
    # get current date
    today = datetime.today().strftime("%Y-%m-%d")

    # get presets available for the user
    answer = r.get(
        f"http://{config.DB_URL}/category/",
        params={'user_id': user_id, 'include_global': "true"},
        timeout=10
    )
    if answer.status_code != 200:
        log_erroneous_answer(answer)
        await container.slacker.post_to_channel(
            channel_id=channel_id,
            text="Couldn't receive presets for the user. "
                 "Please, contact bot developers about this situation."
        )
        return

    presets_list = answer.json()
    sources = [('all', 'all')]
    sources.extend((y := x.get("name", "<ERROR>"), y.lower()) for x in presets_list)

    # extend them with current existing channels
    channels = await container.slacker.get_channels_list()
    sources.extend((y, f"<#{x}>") for x, y in channels)

    # create answer for top command from the template
    template = container.jinja_env.get_template("top.json.j2")
    result = template.render(today=today, sources=sources).replace("\n", "")
    await container.slacker.post_blocks_to_channel(channel_id=channel_id, blocks=result)


async def top_interaction_eligibility(data: dict):
    return data.get("type", "") == "block_actions" and data.get("actions", [{}])[0].get("action_id",
                                                                                        "") == "top_submission"


async def top_interaction(data: dict):
    request_parameters = {}

    user = data['user']['id']
    channel = data['channel']['id']

    # parse values
    values = data['state']['values']

    # parse amount
    amount_str = values['top_amount_selector']['top_amount_selector']['selected_option']['value']
    amount = try_parse_int(amount_str)
    if amount is None:
        await container.slacker.post_to_channel(channel_id=channel, text=f"Erroneous number: {amount_str}")
        return

    if amount <= 0:
        await container.slacker.post_to_channel(channel_id=channel, text=f"Number of messages should be positive, "
                                                                         f"provided value: {amount}")
        return
    request_parameters['top_count'] = amount

    sorting_type = values['top_sorting_selector']['top_sorting_selector']['selected_option']['value']
    if sorting_type not in {"reply_count", "thread_length", "reactions_rate"}:
        await container.slacker.post_to_channel(channel_id=channel, text=f"Unknown sorting type: {sorting_type}")
        return
    request_parameters['sorting_type'] = sorting_type

    preset: str = values['top_preset_selector']['top_preset_selector']['selected_option']['value']

    if preset == "all":
        pass
    elif preset.startswith("<#") and preset.endswith(">"):
        request_parameters['channel_id'] = preset[2:-1]
    else:
        request_parameters['category_name'] = preset
        request_parameters['user_id'] = user

    # find user's timezone
    user_info = await container.slacker.get_user_info(user_id=user)
    tz_offset = user_info.get('tz_offset', 0)

    date_value = values['top_datetime_selector']['delta_datepicker']['selected_date']
    time_value = values['top_datetime_selector']['delta_timepicker']['selected_time']
    selected_datetime = datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %H:%M")
    selected_datetime -= timedelta(seconds=tz_offset)
    request_parameters['after_ts'] = Decimal(time.mktime(selected_datetime.timetuple()))

    base_url = f"http://{config.DB_URL}/message/top"
    answer = r.get(base_url, params=request_parameters, timeout=10)
    if answer.status_code != 200:
        result = (
            "Sorry, some error occurred during message handling. "
            "Please, contact bot developers. Thanks."
        )
    elif not (y := answer.json()):
        result = (
            "No messages to print. Either category/channel/messages not found "
            "or something went wrong."
        )
    else:
        result = __pretty_top_format(y)

    await container.slacker.post_to_channel(channel_id=channel, text=result)
