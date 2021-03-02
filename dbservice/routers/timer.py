from datetime import datetime, timedelta
from models import Timer
from typing import List, Optional

from config import TIMERS_LIMIT
from fastapi import APIRouter, HTTPException
from dbprovider.TimerDAO import timer_dao

router = APIRouter()


@router.get("/", response_model=List[Timer])
async def list_timers(username: str):
    return await timer_dao.list_timers(username)


@router.delete("/")
async def remove_timer(username: str, timer_name: str):
    return await timer_dao.remove_timer(username, timer_name)


@router.post("/", response_model=Timer)
async def insert_timer(timer: Timer):
    if isinstance(timer.delta, float) and isinstance(timer.next_start, str):
        timer = Timer(
            channel_id=timer.channel_id,
            username=timer.username,
            timer_name=timer.timer_name,
            delta=timedelta(seconds=timer.delta),
            next_start=datetime.fromisoformat(timer.next_start),
            top_command=timer.top_command
        )

    result = await timer_dao.insert_timer(timer, TIMERS_LIMIT)
    if not result:
        raise HTTPException(
            status_code=400,
            detail="Maximum number of timers for this user achieved. "
                   "Please, consider removing one of your existing timers to be allowed to add another one."
        )

    return timer


@router.get("/exists", response_model=bool)
async def check_existence(username: str, timer_name: str):
    return await timer_dao.check_timer_existence(username=username, timer_name=timer_name)


@router.get("/count", response_model=int)
async def count_timers(username: str):
    return await timer_dao.count_timers(username)


@router.patch("/next_start", response_model=Timer)
async def update_timer_next_start(timer: Timer):
    result = await timer_dao.update_timer_next_start(timer)
    if not result:
        timer_dao.engine.logger.error(f"Timer not found. Timer: {timer}")
        raise HTTPException(
            status_code=404,
            detail="Timer not found"
        )
    return timer


@router.get("/nearest", response_model=Optional[Timer])
async def get_nearest_timer(time_border: datetime):
    return await timer_dao.get_nearest_timer(time_border)


@router.get("/overdue", response_model=List[Timer])
async def get_overdue_timers(time_border: datetime):
    if isinstance(time_border, str):
        time_border = datetime.fromisoformat(time_border)
    return await timer_dao.get_overdue_timers(time_border)
