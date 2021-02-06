import asyncio
import json
from datetime import datetime, timedelta
from logging import Logger
import requests as r

from common.Slacker import Slacker
from common.models import Timer
from ui_processor.common import UserRequest
from ui_processor.request_parser import process_message
from config import OVERDUE_MINUTES


async def process_timers(slacker: Slacker, logger: Logger, db_service: str):
    base_url = f"http://{db_service}/"

    while True:
        time_border = datetime.utcnow() - timedelta(minutes=OVERDUE_MINUTES)

        # get min(next_start)
        answer = r.get(base_url + "timer/nearest", params={"time_border": time_border.isoformat()}, timeout=10)
        if answer.status_code != 200:
            logger.error(answer.text)
            await asyncio.sleep(300)
            continue

        nearest_timer = answer.json()
        if nearest_timer is None:
            await asyncio.sleep(300)
            continue

        # sleep until that time if time - current_time > 0
        run_time = nearest_timer.next_start
        now = datetime.utcnow()
        run_delta = run_time - now
        run_delta = run_delta.total_seconds()
        if run_delta > 5:
            await asyncio.sleep(
                min(run_delta - 3, 300)
            )  # if nearest in 1 year and someone will add another
            continue  # let's get timer again just in case if user deleted it already

        # run top command and return result to the user
        u_message = UserRequest(
            user=nearest_timer.username,
            text=nearest_timer.top_command,
            channel=nearest_timer.channel_id,
            is_im=True,
            ts="",
        )

        # set next_start to next_start + timedelta
        next_time = nearest_timer.next_start + nearest_timer.delta

        try:
            await process_message(
                message=u_message, bot_name="", api=slacker, db_service=db_service
            )
            await slacker.post_to_channel(
                channel_id=u_message.channel,
                text=f"Next start: {next_time.strftime('%Y-%m-%d %H:%M:%S')} UTC",
            )

        except Exception as e:
            logger.exception(e)

        new_timer = Timer(
            channel_id=nearest_timer.channel_id,
            username=nearest_timer.username,
            timer_name=nearest_timer.timer_name,
            delta=nearest_timer.delta,
            next_start=next_time,
            top_command=nearest_timer.top_command,
        )

        result = r.patch(base_url + "timer/next_start", data=json.dumps(new_timer))
        if result != 200:
            logger.error(result.text)
            break  # Exiting timers processing to avoid spamming to users...


async def update_timers_once(
        slacker: Slacker, logger: Logger, db_service: str
):
    """
    Updates timers that are older than N minutes ago and send user a message about it
    """
    base_url = f"http://{db_service}/"

    # get timers older than n_minutes
    time_border = datetime.utcnow() - timedelta(minutes=OVERDUE_MINUTES)

    answer = r.get(base_url + "timer/overdue", params={"time_border": time_border.isoformat()}, timeout=10)
    if answer.status_code != 200:
        logger.error(answer.text)
        return
    overdue_timers = answer.json()
    if not overdue_timers:
        return

    # update each timer and notify the timer creator
    now = datetime.utcnow()
    for timer in overdue_timers:
        new_start = timer.next_start

        # update time with deltas
        while new_start < now:
            new_start += timer.delta

        new_timer = Timer(
            channel_id=timer.channel_id,
            username=timer.username,
            timer_name=timer.timer_name,
            delta=timer.delta,
            next_start=new_start,
            top_command=timer.top_command,
        )

        answer = r.patch(base_url + "timer/next_start", body=json.dumps(new_timer), timeout=10)
        if answer.status_code != 200:
            logger.error(answer.text)
            continue

        await slacker.post_to_channel(
            channel_id=new_timer.channel_id,
            text=f"Due to bot being offline or other reasons timer {new_timer.timer_name} of user "
                 f"<@{new_timer.username}> missed it's tick. "
                 f"Timer's new next start is: {new_timer.next_start.strftime('%Y-%m-%d %H:%M:%S')}",
        )

    logger.debug(f"{len(overdue_timers)} overdue timers updated.")


async def update_timers(slacker: Slacker, logger: Logger, db_service: str):
    while True:
        await asyncio.sleep(OVERDUE_MINUTES * 60)

        try:
            await update_timers_once(slacker=slacker, logger=logger, db_service=db_service)
        except Exception as e:
            logger.exception(e)
