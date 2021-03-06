from datetime import datetime, timezone
import hashlib
import hmac
from decimal import Decimal, InvalidOperation
from typing import Optional, List, Any
import requests as r

from fastapi import HTTPException, Request
from pydantic import ValidationError
from result import Result

import config
import container
from common.extras import try_request
from json_types import QnAAnswer


def check_message_callback(data: dict) -> bool:
    return data.get("type", None) == "event_callback" and data.get("event", {}).get("type", None) == "message"


async def verify_origin(request: Request) -> None:
    headers = request.headers
    body = await request.body()

    version = "v0"
    timestamp = headers.get("X-Slack-Request-Timestamp")
    if abs(datetime.now(timezone.utc).timestamp() - float(timestamp)) > 60 * 5:
        # The request timestamp is more than five minutes from local time.
        # It could be a replay attack, so let's ignore it.
        raise HTTPException(status_code=403, detail="X-Slack-Request-Timestamp is too old.")

    request_hash = f"{version}:{timestamp}:".encode("ascii") + body
    request_hash = hmac.new(key=config.SIGNING_SECRET.encode('ascii'), msg=request_hash,
                            digestmod=hashlib.sha256).hexdigest()
    request_hash = f"{version}={request_hash}"

    if not hmac.compare_digest(request_hash, headers.get('X-Slack-Signature', '')):
        raise HTTPException(status_code=403, detail="Couldn't verify the origin of the request")


def check_url_verification(data: dict) -> bool:
    return data.get("type", None) == "url_verification"


def process_url_verification(data: dict) -> dict:
    return {"challenge": data.get("challenge", None)}


def get_user_presets(user_id: str) -> Optional[List]:
    # get presets available for the user
    return try_request(
        container.logger,
        r.get,
        f"http://{config.DB_URL}/category/",
        params={'user_id': user_id, 'include_global': "true"}
    ).map(lambda x: x.json()).value


async def get_user_channels_and_presets(user_id: str) -> Optional[List]:
    presets_list = get_user_presets(user_id)
    if presets_list is None:
        return None

    sources = [(y := x.get("name", "<ERROR>"), y.lower()) for x in presets_list]

    # extend them with current existing channels
    channels = await container.slacker.get_channels_list()
    if channels:
        sources.extend((y, f"<#{x}>") for x, y in channels)
    return sources


def check_qna_answer(answer: Any) -> Result[List[QnAAnswer], str]:
    try:
        if not (isinstance(answer, list)):
            raise ValidationError("Base type is not list.")
        return Result.Ok([QnAAnswer.parse_obj(x) for x in answer])
    except ValidationError as e:
        container.logger.exception(e)
        return Result.Err(str(e))


def transform_to_permalinks_or_text(data: List[QnAAnswer]) -> List[str]:
    """
    For each message try to find permalink and return either permalink (ok) or message text (error)
    """
    transformed_data = []
    for answer in data:
        try:
            message_ts = Decimal(answer.timestamp)
            result = container.slacker.get_permalink(channel_id=answer.channel_id, message_ts=message_ts)
            if result is None:
                raise ValueError(f"Couldn't receive permalink for a message.")
        except (InvalidOperation, ValueError):
            result = answer.text
        transformed_data.append(
            '''
            {
              "type": "section",
              "text": {
                "type": "mrkdwn",
                "text": "''' + f'{result}' + '''"
              }
            }
            ''')
    return transformed_data
