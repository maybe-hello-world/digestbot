import unittest
import os
import importlib
from logging import DEBUG, INFO, WARNING, ERROR


class ConfigParserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["SLACK_USER_TOKEN"] = "test_token"
        os.environ["SLACK_BOT_TOKEN"] = "another_test_token"
        os.environ["CRAWL_INTERVAL"] = "300"
        os.environ["BOT_NAME"] = "test-bot-name"

        os.environ["DB_USER"] = "postgres"
        os.environ["DB_PASS"] = "postgres"
        os.environ["DB_NAME"] = "postgres"
        os.environ["DB_HOST"] = "postgres"
        os.environ["DB_PORT"] = "3456"

        os.environ["LOG_LEVEL"] = "debug"
        os.environ["PM_ONLY"] = "True"

        from digestbot.core.common import config

        cls.config = config

    def setUp(self) -> None:
        os.environ["SLACK_USER_TOKEN"] = "test_token"
        os.environ["SLACK_BOT_TOKEN"] = "another_test_token"

    def test_slack_user_token_positive(self):
        token = "something"
        os.environ["SLACK_USER_TOKEN"] = token

        importlib.reload(self.config)
        self.assertEqual(token, self.config.SLACK_USER_TOKEN)

    def test_slack_user_token_negative(self):
        del os.environ["SLACK_USER_TOKEN"]

        with self.assertRaises(Exception):
            importlib.reload(self.config)

    def test_slack_bot_token_positive(self):
        token = "something_bottable"
        os.environ["SLACK_BOT_TOKEN"] = token

        importlib.reload(self.config)
        self.assertEqual(token, self.config.SLACK_BOT_TOKEN)

    def test_slack_bot_token_negative(self):
        del os.environ["SLACK_BOT_TOKEN"]

        with self.assertRaises(Exception):
            importlib.reload(self.config)

    def test_crawl_interval_positive(self):
        os.environ["CRAWL_INTERVAL"] = "300"

        importlib.reload(self.config)
        self.assertEqual(300, self.config.CRAWL_INTERVAL)

    def test_crawl_interval_negative(self):
        os.environ["CRAWL_INTERVAL"] = "abc"

        importlib.reload(self.config)
        self.assertEqual(
            900,
            self.config.CRAWL_INTERVAL,
            msg="Default value should be correctly parsed.",
        )

    def test_bot_name_positive(self):
        os.environ["BOT_NAME"] = "test"

        importlib.reload(self.config)
        self.assertEqual("test", self.config.BOT_NAME)

    def test_bot_name_negative(self):
        del os.environ["BOT_NAME"]

        importlib.reload(self.config)
        self.assertEqual("digest-bot", self.config.BOT_NAME)

    def test_db_user_positive(self):
        os.environ["DB_USER"] = "testvalue"

        importlib.reload(self.config)
        self.assertEqual("testvalue", self.config.DB_USER)

    def test_db_user_negative(self):
        del os.environ["DB_USER"]

        importlib.reload(self.config)
        self.assertEqual("postgres", self.config.DB_USER)

    def test_db_pass_positive(self):
        os.environ["DB_PASS"] = "testvalue"

        importlib.reload(self.config)
        self.assertEqual("testvalue", self.config.DB_PASS)

    def test_db_pass_negative(self):
        del os.environ["DB_PASS"]

        importlib.reload(self.config)
        self.assertEqual("postgres", self.config.DB_PASS)

    def test_db_name_positive(self):
        os.environ["DB_NAME"] = "testvalue"

        importlib.reload(self.config)
        self.assertEqual("testvalue", self.config.DB_NAME)

    def test_db_name_negative(self):
        del os.environ["DB_NAME"]

        importlib.reload(self.config)
        self.assertEqual("postgres", self.config.DB_NAME)

    def test_db_host_positive(self):
        os.environ["DB_HOST"] = "testvalue"

        importlib.reload(self.config)
        self.assertEqual("testvalue", self.config.DB_HOST)

    def test_db_host_negative(self):
        del os.environ["DB_HOST"]

        importlib.reload(self.config)
        self.assertEqual("postgres", self.config.DB_HOST)

    def test_db_port_positive(self):
        os.environ["DB_PORT"] = "5566"

        importlib.reload(self.config)
        self.assertEqual(5566, self.config.DB_PORT)

    def test_db_port_negative(self):
        del os.environ["DB_PORT"]

        importlib.reload(self.config)
        self.assertEqual(5432, self.config.DB_PORT)

        os.environ["DB_PORT"] = "hello"
        importlib.reload(self.config)
        self.assertEqual(5432, self.config.DB_PORT)

    def test_log_level_positive(self):
        def intra_test(pred, true):
            os.environ["LOG_LEVEL"] = pred
            importlib.reload(self.config)
            self.assertEqual(true, self.config.LOG_LEVEL)

        intra_test("dEbUG", DEBUG)
        intra_test("INFo", INFO)
        intra_test("warn", WARNING)
        intra_test("warning", WARNING)
        intra_test("ERROR", ERROR)

    def test_log_level_negative(self):
        os.environ["LOG_LEVEL"] = "something_strange"

        importlib.reload(self.config)
        self.assertEqual(INFO, self.config.LOG_LEVEL)

    def test_pm_only_positive(self):
        os.environ["PM_ONLY"] = "True"
        importlib.reload(self.config)
        self.assertEqual(True, self.config.PM_ONLY)

    def test_pm_only_negative(self):
        del os.environ["PM_ONLY"]
        importlib.reload(self.config)
        self.assertEqual(False, self.config.PM_ONLY)


if __name__ == "__main__":
    unittest.main()
