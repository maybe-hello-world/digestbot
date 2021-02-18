import json
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Union

import config
import container
import requests as r

from common.models import Timer
from extras import get_user_channels_and_presets, log_erroneous_answer, TimerEncoder
from routers.top import top_parser


async def send_initial_message(user_id: str, channel_id: str) -> None:
    base_url = f"http://{config.DB_URL}/timer/"
    try:
        answer = r.get(base_url, params={"username": user_id}, timeout=10)
    except r.Timeout:
        await container.slacker.post_to_channel(
            channel_id=channel_id,
            text="Received timeout during database interaction. Please, try later."
        )
        return

    timers = answer.json()
    timers = [Timer(
        x['channel_id'],
        x['username'],
        x['timer_name'],
        timedelta(seconds=x['delta']),
        datetime.fromisoformat(x['next_start']),
        x['top_command']
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
    else:
        container.logger.warning(f"Unknown timer interaction message: {data}")


async def __process_timer_creation(data: dict, channel_id: str, user_id: str):
    def __parse_amount_unit(_amount: str, _unit: str) -> Union[int, str]:
        """Return seconds from parsed period"""
        multipliers = {
            "hour": 60 * 60,
            "day": 60 * 60 * 24,
            "week": 60 * 60 * 24 * 7
        }
        _amount = int(_amount)

        if _unit not in multipliers:
            container.logger.error(f"Received unknown unit type: {_unit}")
            return "Internal error."

        return _amount * multipliers[_unit]

    values = data['state']['values']

    # parse common params
    timer_parameters = top_parser(
        amount=values['timer_message_amount']['timer_message_amount'],
        sorting_type=values['timer_sorting_selector']['timer_sorting_selector'],
        preset=values['timer_preset_selector']['timer_preset_selector'],
        user_id=user_id
    )

    if isinstance(timer_parameters, str):
        # error returned
        await container.slacker.post_to_channel(channel_id=channel_id, text=timer_parameters)
        return

    # parse message period
    amount = values['timer_message_period_picker']['timer_period_amount']['selected_option']['value']
    unit = values['timer_message_period_picker']['timer_period_unit']['selected_option']['value']
    result = __parse_amount_unit(amount, unit)
    if isinstance(result, str):
        await container.slacker.post_to_channel(channel_id=channel_id, text=result)
        return
    timer_parameters['message_period_seconds'] = result

    # parse timer period
    amount = values['timer_period_picker']['timer_period_amount']['selected_option']['value']
    unit = values['timer_period_picker']['timer_period_unit']['selected_option']['value']
    result = __parse_amount_unit(amount, unit)
    if isinstance(result, str):
        await container.slacker.post_to_channel(channel_id=channel_id, text=result)
        return
    timer_delta = timedelta(seconds=result)

    # find user's timezone
    user_info = await container.slacker.get_user_info(user_id=user_id)
    tz_offset = user_info.get('tz_offset', 0)

    # parse timer initial date
    start_time = values['timer_begin_picker']['delta_timepicker']['selected_time']
    start_date = values['timer_begin_picker']['delta_datepicker']['selected_date']
    selected_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    selected_datetime -= timedelta(seconds=tz_offset)
    if selected_datetime < datetime.utcnow():
        await container.slacker.post_to_channel(
            channel_id=channel_id,
            text="Timer should start in the future, not in the past."
        )
        return

    new_timer = Timer(
        channel_id=channel_id,
        username=user_id,
        timer_name=str(uuid.uuid4()),
        delta=timer_delta,
        next_start=selected_datetime,
        top_command=json.dumps(timer_parameters)
    )

    data = json.dumps(asdict(new_timer), cls=TimerEncoder)
    answer = r.post(f"http://{config.DB_URL}/timer/", data=data, timeout=10)
    if answer.status_code != 200:
        log_erroneous_answer(answer)
        await container.slacker.post_to_channel(channel_id=channel_id, text=answer.text)
        return

    await container.slacker.post_to_channel(channel_id=channel_id, text=(
        f"Timer {new_timer.timer_name} successfully created. "
        f"Next start time: {new_timer.next_start.strftime('%Y-%m-%d %H:%M:%S')} UTC"
    ))
    return


async def __process_timer_deletion(data: dict, channel_id: str, user_id: str):
    timer_name = data['actions'][0]['value']
    base_url = f"http://{config.DB_URL}/timer/"

    if timer_name is None:
        await container.slacker.post_to_channel(channel_id=channel_id, text=(
            "Timer name to delete should be explicitly specified. "
            "Please specify timer name or type `help timers` to get additional information."
        ))
        return

    answer = r.get(base_url + "exists", params={'timer_name': timer_name, 'username': user_id}, timeout=10)
    if answer.status_code == 404:
        await container.slacker.post_to_channel(channel_id=channel_id, text=(
            "Couldn't find timer with such name. "
            "If you are sure that it's a bug, please contact bot developer team. Thanks."
        ))
        return

    answer = r.delete(base_url, params={'timer_name': timer_name, 'username': user_id}, timeout=10)
    if answer.status_code == 200:
        await container.slacker.post_to_channel(channel_id=channel_id, text=f"Timer {timer_name} successfully deleted.")
    else:
        container.logger.error(answer.text)
        await container.slacker.post_to_channel(channel_id=channel_id, text=(
            f"Some error occurred. Timer {timer_name} possibly is not deleted. "
            f"Please, check with `timers ls` and contact developers team. Thanks."
        ))


async def __show_timer_creation(channel_id: str, user_id: str):
    sources = await get_user_channels_and_presets(user_id)
    if sources is None:
        await container.slacker.post_to_channel(
            channel_id=channel_id,
            text="Couldn't receive presets for the user. "
                 "Please, contact bot developers about this situation."
        )
        return

    sources = [('all', 'all')] + sources

    template = container.jinja_env.get_template("timer_new.json")
    result = template.render(sources=sources, today=datetime.today().strftime("%Y-%m-%d"))
    await container.slacker.post_to_channel(channel_id=channel_id, blocks=result, ephemeral=True, user_id=user_id)
