import logging

import sys
from slack import errors
from asyncio import sleep
from typing import Callable, TypeVar, Optional

from digestbot.resilence_library.policy import Policy
from digestbot.resilence_library.exception import PolicyError


T = TypeVar("T")


class RetryAfterError(PolicyError):
    pass


class RetryAfterSlack(Policy):
    def __init__(self, repeat: int):
        self.repeat = repeat

        logger = logging.getLogger("RetryAfter-Policy")
        logger.setLevel("INFO")

        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%m.%d.%Y-%I:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

    @staticmethod
    def __int_or_none(val: str) -> Optional[int]:
        try:
            val = int(val)
        except ValueError:
            return None
        else:
            return val

    async def execute(self, function: Callable[[], T]) -> T:
        for i in range(self.repeat):
            try:
                result = await function()
            except errors.SlackApiError as e:
                response = e.response
                if response.status_code != 429:
                    raise
                retry_value = response.headers.get("Retry-After", "")
                self.logger.debug(
                    f"429: Retry-After received, iteration: {i}, retry timer: {retry_value}"
                )
                retry_timer = self.__int_or_none(retry_value) or 5
                await sleep(retry_timer)
            else:
                return result

        raise RetryAfterError(
            f"Retry-After policy failed after {self.repeat} iterations."
        )
