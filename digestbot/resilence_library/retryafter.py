from slack import errors
from asyncio import sleep
from typing import Callable, TypeVar, Optional

from digestbot.core.common import config
from digestbot.resilence_library.policy import Policy
from digestbot.resilence_library.exception import PolicyError
from digestbot.core.common.LoggerFactory import create_logger


T = TypeVar("T")


class RetryAfterError(PolicyError):
    pass


class RetryAfterSlack(Policy):
    def __init__(self, repeat: int):
        self.repeat = repeat
        self.logger = create_logger("RetryAfter-Policy", config.LOG_LEVEL)

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
