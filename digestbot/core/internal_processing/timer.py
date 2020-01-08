import asyncio
from datetime import datetime, timedelta
from logging import Logger

from digestbot.core.db.models import Timer
from digestbot.core.db.dbengine.PostgreSQLEngine import PostgreSQLEngine
from digestbot.core.db.dbrequest.timer import (
    get_nearest_timer,
    update_timer_next_start,
    get_overdue_timers,
)
from digestbot.core.slack_api import Slacker
from digestbot.core.ui_processor.common import UserRequest
from digestbot.core.ui_processor.request_parser import process_message
from digestbot.core.common.config import OVERDUE_MINUTES


async def timer_processor(
    slacker: Slacker, logger: Logger, db_engine: PostgreSQLEngine
):
    while True:
        time_border = datetime.utcnow() - timedelta(minutes=OVERDUE_MINUTES)

        # get min(next_start)
        nearest_timer = await get_nearest_timer(
            db_engine=db_engine, time_border=time_border
        )
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
        next_time = datetime.utcnow() + nearest_timer.delta

        try:
            await process_message(
                message=u_message, bot_name="", api=slacker, db_engine=db_engine
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
        result = await update_timer_next_start(db_engine=db_engine, timer=new_timer)
        if result is None:
            logger.critical(
                "Timer wasn't updated due to DB problems! "
                "Exiting timers processing to avoid spamming to users..."
            )
            break


async def timers_update_once(
    slacker: Slacker, logger: Logger, db_engine: PostgreSQLEngine
):
    """
    Updates timers that are older than N minutes ago and send user a message about it
    """

    # get timers older than n_minutes
    time_border = datetime.utcnow() - timedelta(minutes=OVERDUE_MINUTES)
    overdue_timers = await get_overdue_timers(
        db_engine=db_engine, time_border=time_border
    )
    if overdue_timers is None:
        logger.warning("Database problems occurred while timers updating. Exiting...")
        return
    elif not overdue_timers:
        logger.debug("No overdue timers exist.")
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

        result = await update_timer_next_start(db_engine=db_engine, timer=new_timer)
        if not result:
            logger.error(
                "Couldn't update timer with new next_start timer in timer_update_once procedure, "
                f"timer: {new_timer}"
            )
            continue

        await slacker.post_to_channel(
            channel_id=new_timer.channel_id,
            text=f"Due to bot being offline or other reasons timer {new_timer.timer_name} of user "
            f"<@{new_timer.username}> missed it's tick. "
            f"Timer's new next start is: {new_timer.next_start.strftime('%Y-%m-%d %H:%M:%S')}",
        )

    logger.debug(f"{len(overdue_timers)} overdue timers updated.")


async def timers_updater(slacker: Slacker, logger: Logger, db_engine: PostgreSQLEngine):
    while True:
        await asyncio.sleep(300)

        await timers_update_once(slacker=slacker, logger=logger, db_engine=db_engine)
