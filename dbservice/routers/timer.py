from datetime import datetime
from models import Timer
from typing import List

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/", response_model=List[Timer])
async def list_timers(username: str):
    raise HTTPException(status_code=500, detail="Method not implemented")


@router.delete("/", response_model=Timer)
async def remove_timer(username: str, timer_name: str):
    raise HTTPException(status_code=500, detail="Method not implemented")


@router.post("/", response_model=Timer)
async def insert_timer(timer: Timer):
    raise HTTPException(status_code=500, detail="Method not implemented")


# TODO: 200 or 404?
@router.get("/exists", response_model=Timer)
async def check_existence(username: str, timer_name: str):
    raise HTTPException(status_code=500, detail="Method not implemented")


@router.get("/count", response_model=int)
async def count_timers(username: str):
    raise HTTPException(status_code=500, detail="Method not implemented")


@router.patch("/next_start", response_model=Timer)
async def update_timer_next_start(timer: Timer):
    raise HTTPException(status_code=500, detail="Method not implemented")


@router.get("/nearest", response_model=Timer)
async def get_nearest_timer(time_border: datetime):
    raise HTTPException(status_code=500, detail="Method not implemented")


@router.get("/overdue", response_model=List[Timer])
async def get_overdue_timers(time_border: datetime):
    raise HTTPException(status_code=500, detail="Method not implemented")
