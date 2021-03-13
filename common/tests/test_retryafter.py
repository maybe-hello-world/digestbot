import unittest
from unittest.mock import MagicMock
from slack.errors import SlackApiError
import asyncio
from common.resilence_library.retryafter import RetryAfterSlack, RetryAfterError


class RetryAfterTest(unittest.TestCase):
    class Response:
        status_code = 429
        headers = {"Retry-After": "1"}

    @staticmethod
    async def async_magic():
        pass

    @classmethod
    def setUpClass(cls) -> None:
        MagicMock.__await__ = lambda x: cls.async_magic().__await__()

    def test_retryafterslack_policy(self):
        mock = MagicMock(
            side_effect=SlackApiError(message="x", response=self.Response())
        )
        policy = RetryAfterSlack(3)

        loop = asyncio.new_event_loop()
        with self.assertRaises(RetryAfterError):
            loop.run_until_complete(policy.execute(lambda: mock()))
