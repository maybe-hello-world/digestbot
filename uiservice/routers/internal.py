from fastapi import APIRouter
from pydantic import BaseModel

import container
from routers.top import post_top_message

router = APIRouter()


class MessagePostData(BaseModel):
    channel_id: str
    text: str


class TopData(BaseModel):
    channel_id: str
    request_parameters: dict


@router.post("message")
async def post_message(data: MessagePostData):
    """
    Post message to slack channel
    """

    if data.channel_id and data.text:
        await container.slacker.post_to_channel(channel_id=data.channel_id, text=data.text)


@router.post("top")
async def process_top(data: TopData):
    if data.channel_id and data.request_parameters:
        await post_top_message(channel_id=data.channel_id, request_parameters=data.request_parameters)
