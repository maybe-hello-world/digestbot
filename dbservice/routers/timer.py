from datetime import datetime
from models import Timer
from typing import List

from fastapi import APIRouter

router = APIRouter()


@router.get("/", response_model=List[Timer])
async def list_timers(username: str):
    raise NotImplementedError


@router.delete("/", response_model=Timer)
async def remove_timer(username: str, timer_name: str):
    raise NotImplementedError


@router.post("/", response_model=Timer)
async def insert_timer(timer: Timer):
    raise NotImplementedError


# TODO: 200 or 404?
@router.get("/exists", response_model=Timer)
async def check_existence(username: str, timer_name: str):
    raise NotImplementedError


@router.get("/count", response_model=int)
async def count_timers(username: str):
    raise NotImplementedError


@router.patch("/next_start", response_model=Timer)
async def update_timer_next_start(timer: Timer):
    raise NotImplementedError


@router.get("/nearest", response_model=Timer)
async def get_nearest_timer(time_border: datetime):
    raise NotImplementedError


@router.get("/overdue", response_model=List[Timer])
async def get_overdue_timers(time_border: datetime):
    raise NotImplementedError
