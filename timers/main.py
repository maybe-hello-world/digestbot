import asyncio
import json
from datetime import datetime, timedelta
import time
from logging import Logger
import requests as r
from influxdb_client import Point

from common.models import Timer

from config import OVERDUE_MINUTES, LOG_LEVEL
from common.LoggerFactory import create_logger
from common.extras import TimerEncoder, try_request
from config import INFLUX_API_WRITE


async def update_timers_once(
        logger: Logger, ui_service: str, db_service: str
):
    """
    Updates timers that are older than N minutes ago and send user a message about it
    """
    db_base_url = f"http://{db_service}/timer/"
    ui_base_url = f"http://{ui_service}/internal/"

    # get timers older than n_minutes
    time_border = (datetime.utcnow() - timedelta(minutes=OVERDUE_MINUTES)).isoformat()

    overdue_timers = (try_request(logger, r.get, db_base_url + "overdue", params={"time_border": time_border})
                      .map_or([], lambda x: x.json()))
    INFLUX_API_WRITE(Point("digestbot").field("overdue_timers", len(overdue_timers)).time(datetime.utcnow()))

    # update each timer and notify the timer creator
    now = datetime.utcnow()
    for timer in overdue_timers:
        new_start = datetime.fromisoformat(timer['next_start'])
        delta = timedelta(seconds=timer['delta'])

        # update time with deltas
        while new_start < now:
            new_start += delta

        new_timer = Timer(
            channel_id=timer['channel_id'],
            username=timer['username'],
            timer_name=timer['timer_name'],
            delta=delta,
            next_start=new_start,
            top_command=timer['top_command'],
        )

        # update timer in DB and notify the user
        try_request(
            logger, r.patch, db_base_url + "next_start",
            data=json.dumps(new_timer.dict(), cls=TimerEncoder),
            headers={'Content-Type': 'application/json'}
        )

        text = f"""Due to bot being offline or other reasons timer {new_timer.timer_name} 
        of user <@{new_timer.username}> missed it's tick. 
        Timer's new next start is: {new_timer.next_start.strftime('%Y-%m-%d %H:%M:%S')}."""
        try_request(
            logger, r.post, ui_base_url + "message",
            data=json.dumps({"channel_id": new_timer.channel_id, "text": text}),
            headers={'Content-Type': 'application/json'}
        )

    logger.debug(f"{len(overdue_timers)} overdue timers updated.")


async def report_statistics(logger: Logger, db_service: str):
    db_base_url = f"http://{db_service}/timer/count"
    timers_total = try_request(logger, r.get, db_base_url).map(lambda x: x.json())
    if timers_total.is_ok():
        INFLUX_API_WRITE(Point("digestbot").field("timers_total", timers_total.unwrap()).time(datetime.utcnow()))


async def update_timers(logger: Logger, ui_service: str, db_service: str):
    while True:
        await update_timers_once(logger=logger, ui_service=ui_service, db_service=db_service)
        await report_statistics(logger=logger, db_service=db_service)
        await asyncio.sleep(OVERDUE_MINUTES * 60)


async def process_timers(logger: Logger, ui_service: str, db_service: str):
    db_base_url = f"http://{db_service}/timer/"
    ui_base_url = f"http://{ui_service}/internal/"

    while True:
        time_border = (datetime.utcnow() - timedelta(minutes=OVERDUE_MINUTES)).isoformat()

        # get nearest timer to execute
        answer = try_request(logger, r.get, db_base_url + "nearest", params={"time_border": time_border}).map(
            lambda x: x.json())
        if answer.is_err() or answer.value is None:
            await asyncio.sleep(300)
            continue
        nearest_timer: dict = answer.value

        # sleep until that time if time - current_time > 0

        run_time = datetime.fromisoformat(nearest_timer['next_start'])
        now = datetime.utcnow()
        run_delta = run_time - now
        run_delta = run_delta.total_seconds()
        if run_delta > 5:
            await asyncio.sleep(
                min(run_delta - 3, 300)
            )  # if nearest in 1 year and someone will add another
            continue  # let's get timer again just in case if user deleted it already

        # run top command and return result to the user
        request_parameters = json.loads(nearest_timer['top_command'])
        message_period = timedelta(seconds=request_parameters['message_period_seconds'])
        after_ts = str(time.mktime((datetime.utcnow() - message_period).timetuple()))
        request_parameters['after_ts'] = after_ts

        next_time = datetime.fromisoformat(nearest_timer['next_start']) + timedelta(seconds=nearest_timer['delta'])
        request_parameters['next_time'] = next_time
        request_parameters['user_id'] = nearest_timer['username']

        # post top request
        try_request(
            logger, r.post, ui_base_url + "top",
            data=json.dumps({"channel_id": nearest_timer['channel_id'], "request_parameters": request_parameters},
                            cls=TimerEncoder),
            headers={'Content-Type': 'application/json'}
        )

        new_timer = Timer(
            channel_id=nearest_timer['channel_id'],
            username=nearest_timer['username'],
            timer_name=nearest_timer['timer_name'],
            delta=nearest_timer['delta'],
            next_start=next_time,
            top_command=nearest_timer['top_command'],
        )

        try_request(
            logger, r.patch, db_base_url + "next_start",
            data=json.dumps(new_timer.dict(), cls=TimerEncoder),
            headers={'Content-Type': 'application/json'}
        )
        INFLUX_API_WRITE(Point("digestbot").field("timers_processed", 1).time(datetime.utcnow()))


if __name__ == '__main__':
    UI_SERVICE = "uiservice:80"
    DB_SERVICE = "dbservice:80"

    _logger = create_logger(__name__, LOG_LEVEL)

    loop = asyncio.get_event_loop()
    process_timers_task = loop.create_task(process_timers(_logger, UI_SERVICE, DB_SERVICE))
    update_timers_task = loop.create_task(update_timers(_logger, UI_SERVICE, DB_SERVICE))

    _logger.info("Wait for 15 seconds to allow DB services to start...")
    time.sleep(15)
    _logger.info("Starting timer processor...")
    loop.run_until_complete(asyncio.gather(process_timers_task, update_timers_task))
