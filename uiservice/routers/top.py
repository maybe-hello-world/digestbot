import time
from datetime import datetime, timedelta
from typing import List, Generator, Any

import requests as r
from influxdb_client import Point
from result import Result, Ok, Err

import config
from common.extras import try_parse_int, try_request
from extras import get_user_channels_and_presets
import container

PRESETS_NOT_RECEIVED = "Couldn't receive presets for the user. Please, contact bot developers about this situation."
TOP_FUTURE_ERROR = "Please, select the date from the past. We cannot process future messages. Yet. :)"
MESSAGE_HANDLING_ERROR = (
    "Sorry, some error occurred during message handling. "
    "Please, contact bot developers. Thanks."
)
NO_MESSAGES_TO_PRINT = (
    "No messages to print. Either preset/channel/messages not found "
    "or something went wrong."
)


def __pretty_top_format(messages: List[dict]) -> Generator[str, Any, None]:
    template = (
        "{}. <@{}> | <#{}>\n"
        "{}...\n"
        "Replies: {} from {} users. Reactions rate: {}.\n"
        "Link: {}"
    )
    messages = (
        template.format(
            i,
            x['username'],
            x['channel_id'],
            x['text'][:200],
            x['reply_count'],
            x['reply_users_count'],
            round(x['reactions_rate'], 2),
            x['link'],
        )
        for i, x in enumerate(messages, start=1)
    )
    return messages


async def send_initial_message(user_id: str, channel_id: str) -> None:
    # get current date
    today = datetime.today().strftime("%Y-%m-%d")

    # create answer for top command from the template
    template = container.jinja_env.get_template("top.json")
    render_result = template.render(today=today)
    await container.slacker.post_to_channel(channel_id=channel_id, blocks=render_result, ephemeral=True,
                                            user_id=user_id)


async def send_options(user_id: str, value: str) -> dict:
    sources = await get_user_channels_and_presets(user_id)
    if sources is None:
        return {"options": [{"text": {"type": "plain_text", "text": "Internal digestbot problems :("}, "value": "all"}]}

    # only channels and presets where 'value' presented if value is not empty string
    if value:
        sources = [(x, y) for x, y in sources if value in x]
    sources = [('all', 'all')] + sources
    if len(sources) > 99:
        sources = sources[:99]  # Slack constraints

    result = {"options": [{"text": {"type": "plain_text", "text": x}, "value": y} for x, y in sources]}
    return result


async def top_interaction_eligibility(data: dict):
    return data.get("type", "") == "block_actions" and data.get("actions", [{}])[0].get("action_id",
                                                                                        "") == "top_submission"


def top_parser(amount: dict, sorting_type: dict, preset: dict, user_id: str) -> Result[dict, str]:
    answer = {}

    # amount parsing
    amount_str = amount['selected_option']['value']
    amount = try_parse_int(amount_str)
    if amount is None:
        return Err(f"Erroneous number: {amount_str}")
    if amount <= 0:
        return Err(f"Number of messages should be positive, provided value: {amount}")
    answer['top_count'] = amount

    # sorting_type parsing
    sorting_type = sorting_type['selected_option']['value']
    if sorting_type not in {"reply_count", "thread_length", "reactions_rate"}:
        return Err(f"Unknown sorting type: {sorting_type}")
    answer['sorting_type'] = sorting_type

    answer['user_id'] = user_id

    # preset parsing
    preset = preset['selected_option']['value']
    if preset == "all":
        pass
    elif preset.startswith("<#") and preset.endswith(">"):
        answer['channel_id'] = preset[2:-1]
    else:
        answer['preset_name'] = preset

    return Ok(answer)


async def top_interaction(data: dict):
    user = data['user']['id']
    channel = data['channel']['id']
    values = data['state']['values']

    # parse top parameters
    request_parameters = top_parser(
        amount=values['top_amount_selector']['top_amount_selector'],
        sorting_type=values['top_sorting_selector']['top_sorting_selector'],
        preset=values['top_preset_selector']['top_preset_selector'],
        user_id=user
    )

    if request_parameters.is_err():
        # error returned
        await container.slacker.post_to_channel(channel_id=channel, text=request_parameters.unwrap_err())
        return
    request_parameters = request_parameters.unwrap()

    # find user's timezone
    user_info = await container.slacker.get_user_info(user_id=user)
    tz_offset = user_info.get('tz_offset', 0)

    # parse time
    date_value = values['top_datetime_selector']['delta_datepicker']['selected_date']
    time_value = values['top_datetime_selector']['delta_timepicker']['selected_time']
    selected_datetime = datetime.strptime(f"{date_value} {time_value}", "%Y-%m-%d %H:%M")
    selected_datetime -= timedelta(seconds=tz_offset)
    if selected_datetime > datetime.utcnow():
        await container.slacker.post_to_channel(channel_id=channel, text=TOP_FUTURE_ERROR)
        return

    request_parameters['after_ts'] = str(time.mktime(selected_datetime.timetuple()))

    await post_top_message(channel_id=channel, request_parameters=request_parameters)


async def post_top_message(channel_id: str, request_parameters: dict):
    base_url = f"http://{config.DB_URL}/message/top"
    answer = try_request(container.logger, r.get, base_url, params=request_parameters)

    if answer.is_err():
        answer = [MESSAGE_HANDLING_ERROR]
    elif not (y := answer.unwrap().json()):
        answer = [NO_MESSAGES_TO_PRINT]
    else:
        config.INFLUX_API_WRITE(Point("digestbot").field("top_answers_returned", len(y)).time(datetime.utcnow()))
        answer = __pretty_top_format(y)

    config.INFLUX_API_WRITE(Point("digestbot").field("top_requests", 1).time(datetime.utcnow()))
    for message in answer:
        await container.slacker.post_to_channel(channel_id=channel_id, text=message)
