import json
from datetime import datetime, timedelta
from typing import Optional, Callable
import result
import requests as r
from sentry_sdk import capture_exception


def try_parse_int(value: str) -> Optional[int]:
    try:
        return int(value)
    except ValueError:
        return None


class TimerEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, timedelta):
            return o.total_seconds()
        return json.JSONEncoder.default(self, o)


def try_request(request: Callable, *args, **kwargs) -> result.Result[r.Response, str]:
    try:
        answer: r.Response = request(*args, **kwargs, timeout=10)
        if answer.status_code != 200:
            raise ValueError(answer.text)

        return result.Ok(answer)
    except (r.exceptions.Timeout, ValueError) as e:
        capture_exception(e)
        return result.Err(str(e))
