from common.Enums import SortingType
from models import Message
from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException

from dbprovider.MessageDAO import message_dao

router = APIRouter()


@router.post("/")
async def insert_messages(messages: List[Message]):
    return await message_dao.create_messages(messages)


@router.put("/")
async def upsert_messages(messages: List[Message]):
    return await message_dao.upsert_messages(messages)


@router.get("/linkless", response_model=List[Message])
async def get_linkless_messages():
    return await message_dao.get_messages_without_links()


@router.patch("/links")
async def update_message_links(messages: List[Message]):
    return await message_dao.update_message_links(messages)


@router.get("/top", response_model=List[Message])
async def get_top_messages(
        after_ts: str,
        channel_id: Optional[str] = None,
        preset_name: Optional[str] = None,
        user_id: Optional[str] = None,
        sorting_type: SortingType = SortingType.REPLIES,
        top_count: int = Query(default=10, ge=1),
):
    if channel_id is None and preset_name is None and user_id is None:
        return await message_dao.get_top_messages(after_ts=after_ts, sorting_type=sorting_type, top_count=top_count)

    if channel_id is not None and preset_name is None and user_id is None:
        return await message_dao.get_top_messages_by_channel_id(
            channel_id=channel_id,
            after_ts=after_ts,
            sorting_type=sorting_type,
            top_count=top_count
        )

    if channel_id is None and preset_name is not None:
        return await message_dao.get_top_messages_by_preset_name(
            preset_name=preset_name,
            after_ts=after_ts,
            sorting_type=sorting_type,
            top_count=top_count,
            user_id=user_id,
        )

    raise HTTPException(status_code=400, detail="This combination of parameters is not allowed!")
