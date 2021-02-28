import json
from datetime import datetime, timedelta
from typing import Optional


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
