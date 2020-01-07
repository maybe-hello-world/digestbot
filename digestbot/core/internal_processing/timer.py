import asyncio
from datetime import datetime
from logging import Logger

from digestbot.core.db.models import Timer
from digestbot.core.db.dbengine.PostgreSQLEngine import PostgreSQLEngine
from digestbot.core.db.dbrequest.timer import get_nearest_timer, upsert_timer
from digestbot.core.slack_api import Slacker
from digestbot.core.ui_processor.common import UserRequest
from digestbot.core.ui_processor.request_parser import process_message


async def timer_processor(
    slacker: Slacker, logger: Logger, db_engine: PostgreSQLEngine
):
    while True:
        # get min(next_start)
        nearest_timer = await get_nearest_timer(db_engine=db_engine)
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

        try:
            await process_message(
                message=u_message, bot_name="", api=slacker, db_engine=db_engine
            )
        except Exception as e:
            logger.exception(e)

        # set next_start to next_start + timedelta
        next_time = datetime.utcnow() + nearest_timer.delta
        new_timer = Timer(
            channel_id=nearest_timer.channel_id,
            username=nearest_timer.username,
            timer_name=nearest_timer.timer_name,
            delta=nearest_timer.delta,
            next_start=next_time,
            top_command=nearest_timer.top_command,
        )
        await upsert_timer(db_engine=db_engine, timer=new_timer)
