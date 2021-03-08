import json
import uuid
from datetime import datetime, timedelta

import config
import container
import requests as r
from result import Result, Ok, Err
from sentry_sdk import capture_message

from common.models import Timer
from extras import get_user_channels_and_presets
from common.extras import try_request, TimerEncoder
from routers.top import top_parser

DATABASE_INTERACTION_ERROR = "Received error during database interaction. Please, try later."
TIMER_START_ERROR_FUTURE = "Timer should start in the future, not in the past."
TIMER_CREATED = (
    "Timer {0} successfully created. "
    "Next start time: {1} UTC"
)
TIMER_CREATION_FAILED = "Something went wrong during creation of the timer. Sorry. :("
TIMER_NAME_NOT_SPECIFIED = (
    "Timer name to delete should be explicitly specified. "
    "Please specify timer name or type `help timers` to get additional information."
)
INTERNAL_ERROR = "Internal error occurred. Sorry :("
TIMER_NOT_FOUND = (
    "Couldn't find timer with such name. "
    "If you are sure that it's a bug, please contact bot developer team. Thanks."
)
TIMER_DELETED = "Timer {0} successfully deleted."
TIMER_NOT_DELETED = (
    "Some error occurred. Timer {0} possibly is not deleted. "
    "Please, retry or contact developers team. Thanks."
)
PRESETS_NOT_RECEIVED = "Couldn't receive presets for the user. Please, contact bot developers about this situation."


async def send_initial_message(user_id: str, channel_id: str) -> None:
    base_url = f"http://{config.DB_URL}/timer/"
    answer = try_request(container.logger, r.get, base_url, params={"username": user_id})

    if answer.is_err():
        await container.slacker.post_to_channel(channel_id=channel_id, text=DATABASE_INTERACTION_ERROR)
        return
    answer = answer.unwrap()

    timers = answer.json()
    timers = [Timer(
        channel_id=x['channel_id'],
        username=x['username'],
        timer_name=x['timer_name'],
        delta=timedelta(seconds=x['delta']),
        next_start=datetime.fromisoformat(x['next_start']),
        top_command=x['top_command']
    ) for x in timers]

    template = container.jinja_env.get_template("timer_list.json")
    result = template.render(timers=timers)
    await container.slacker.post_to_channel(channel_id=channel_id, blocks=result, ephemeral=True, user_id=user_id)


async def timer_interaction_eligibility(data: dict):
    return data.get("type", "") == "block_actions" and \
           data.get("actions", [{}])[0].get("action_id", "").startswith("timer")


async def timer_interaction(data: dict):
    action_id = data.get("actions", [{}])[0].get("action_id", "")
    channel_id = data.get('channel', {}).get("id", "")
    user_id = data.get("user", {}).get("id", "")

    if action_id == "timer_new":
        await __show_timer_creation(channel_id, user_id)
    elif action_id == "timer_new_submission":
        await __process_timer_creation(data, channel_id, user_id)
    elif action_id == "timer_delete":
        await __process_timer_deletion(data, channel_id, user_id)


async def __process_timer_creation(data: dict, channel_id: str, user_id: str):
    def __parse_amount_unit(_amount: str, _unit: str) -> Result[int, str]:
        """Return seconds from parsed period"""
        multipliers = {
            "hour": 60 * 60,
            "day": 60 * 60 * 24,
            "week": 60 * 60 * 24 * 7
        }
        _amount = int(_amount)

        if _unit not in multipliers:
            capture_message(f"Received unknown unit type: {_unit}")
            return Err("Internal error.")

        return Ok(_amount * multipliers[_unit])

    values = data['state']['values']

    # parse common params
    timer_parameters = top_parser(
        amount=values['timer_message_amount']['timer_message_amount'],
        sorting_type=values['timer_sorting_selector']['timer_sorting_selector'],
        preset=values['timer_preset_selector']['timer_preset_selector'],
        user_id=user_id
    )

    if timer_parameters.is_err():
        # error returned
        await container.slacker.post_to_channel(channel_id=channel_id, text=timer_parameters.unwrap_err())
        return
    timer_parameters = timer_parameters.unwrap()

    # parse message period
    amount = values['timer_message_period_picker']['timer_period_amount']['selected_option']['value']
    unit = values['timer_message_period_picker']['timer_period_unit']['selected_option']['value']
    result = __parse_amount_unit(amount, unit)
    if result.is_err():
        await container.slacker.post_to_channel(channel_id=channel_id, text=result.unwrap_err())
        return
    timer_parameters['message_period_seconds'] = result.unwrap()

    # parse timer period
    amount = values['timer_period_picker']['timer_period_amount']['selected_option']['value']
    unit = values['timer_period_picker']['timer_period_unit']['selected_option']['value']
    result = __parse_amount_unit(amount, unit)
    if result.is_err():
        await container.slacker.post_to_channel(channel_id=channel_id, text=result.unwrap_err())
        return
    timer_delta = timedelta(seconds=result.unwrap())

    # find user's timezone
    user_info = await container.slacker.get_user_info(user_id=user_id)
    tz_offset = user_info.get('tz_offset', 0)

    # parse timer initial date
    start_time = values['timer_begin_picker']['delta_timepicker']['selected_time']
    start_date = values['timer_begin_picker']['delta_datepicker']['selected_date']
    selected_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    selected_datetime -= timedelta(seconds=tz_offset)
    if selected_datetime < datetime.utcnow():
        await container.slacker.post_to_channel(channel_id=channel_id, text=TIMER_START_ERROR_FUTURE)
        return

    new_timer = Timer(
        channel_id=channel_id,
        username=user_id,
        timer_name=str(uuid.uuid4()),
        delta=timer_delta,
        next_start=selected_datetime,
        top_command=json.dumps(timer_parameters)
    )

    data = json.dumps(new_timer.dict(), cls=TimerEncoder)
    answer = try_request(container.logger, r.post, f"http://{config.DB_URL}/timer/", data=data)
    if answer.is_err():
        await container.slacker.post_to_channel(channel_id=channel_id, text=TIMER_CREATION_FAILED)
        return

    await container.slacker.post_to_channel(
        channel_id=channel_id,
        text=TIMER_CREATED.format(new_timer.timer_name, new_timer.next_start.isoformat())
    )
    return


async def __process_timer_deletion(data: dict, channel_id: str, user_id: str):
    timer_name = data['actions'][0]['value']
    base_url = f"http://{config.DB_URL}/timer/"

    if not timer_name:
        await container.slacker.post_to_channel(channel_id=channel_id, text=TIMER_NAME_NOT_SPECIFIED)
        return

    answer = try_request(container.logger, r.get, base_url + "exists",
                         params={'timer_name': timer_name, 'username': user_id})

    if answer.is_err():
        await container.slacker.post_to_channel(channel_id=channel_id, text=INTERNAL_ERROR)
        return

    if not answer.unwrap().json():
        await container.slacker.post_to_channel(channel_id=channel_id, text=TIMER_NOT_FOUND)
        return

    answer = try_request(container.logger, r.delete, base_url, params={'timer_name': timer_name, 'username': user_id})
    if answer.is_ok():
        text = TIMER_DELETED
    else:
        text = TIMER_NOT_DELETED

    await container.slacker.post_to_channel(channel_id=channel_id, text=text.format(timer_name))


async def __show_timer_creation(channel_id: str, user_id: str):
    sources = await get_user_channels_and_presets(user_id)
    if sources is None:
        await container.slacker.post_to_channel(channel_id=channel_id, text=PRESETS_NOT_RECEIVED)
        return

    sources = [('all', 'all')] + sources

    template = container.jinja_env.get_template("timer_new.json")
    result = template.render(sources=sources, today=datetime.today().strftime("%Y-%m-%d"))
    await container.slacker.post_to_channel(channel_id=channel_id, blocks=result, ephemeral=True, user_id=user_id)
