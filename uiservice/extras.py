from datetime import datetime, timezone
import hashlib
import hmac
from typing import Mapping, Optional
import requests as r

from fastapi import HTTPException, Request

from config import SIGNING_SECRET
import container


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
    request_hash = hmac.new(key=SIGNING_SECRET.encode('ascii'), msg=request_hash, digestmod=hashlib.sha256).hexdigest()
    request_hash = f"{version}={request_hash}"

    if not hmac.compare_digest(request_hash, headers.get('X-Slack-Signature', '')):
        raise HTTPException(status_code=403, detail="Couldn't verify the origin of the request")


def check_url_verification(data: dict) -> bool:
    return data.get("type", None) == "url_verification"


def process_url_verification(data: dict) -> dict:
    return {"challenge": data.get("challenge", None)}


def log_erroneous_answer(answer: r.Response) -> None:
    if answer.status_code >= 500:
        container.logger.warning(answer.text)


def try_parse_int(value: str) -> Optional[int]:
    try:
        return int(value)
    except ValueError:
        return None
