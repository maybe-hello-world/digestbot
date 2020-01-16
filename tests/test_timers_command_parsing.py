import datetime
import unittest

from digestbot.command_parser.command_parser import CommandParser
from digestbot.command_parser.exception import TooManyArgumentsError

from digestbot.core.ui_processor.timers.timers_command import timers_parser


class TimersCommandsParsingTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.command_parser = CommandParser(sub_parsers=[timers_parser], commands=[])
        cls.default_add = {
            "cyclicity": "every",
            "timer_freq": datetime.timedelta(days=1),
            "top_placeholder": "top",
            "N": 5,
            "time": datetime.timedelta(days=1),
            "sorting_method": "replies",
            "channel": None,
        }

    def test_ls(self):
        result = self.command_parser.parse("timers ls")
        self.assertEqual(result.command, "timers")
        self.assertIsNotNone(result.sub_parser_result)
        self.assertEqual(result.sub_parser_result.command, "ls")

    def test_rm_positive(self):
        result = self.command_parser.parse("timers rm valid_t")
        self.assertEqual(result.command, "timers")
        self.assertIsNotNone(result.sub_parser_result)
        self.assertEqual(result.sub_parser_result.command, "rm")
        self.assertEqual(result.sub_parser_result.args, {"timer_name": "valid_t"})

    def test_rm_negative(self):
        result = self.command_parser.parse("timers rm")
        self.assertEqual(result.command, "timers")
        self.assertIsNotNone(result.sub_parser_result)
        self.assertEqual(result.sub_parser_result.command, "rm")
        self.assertEqual(result.sub_parser_result.args, {"timer_name": None})

        with self.assertRaises(TooManyArgumentsError):
            self.command_parser.parse("timers rm a b")

    def test_add_positive(self):
        result = self.command_parser.parse("timers add top")
        self.assertDictEqual(result.sub_parser_result.args, self.default_add)

        valid_result = self.default_add.copy()
        valid_result.update({"timer_freq": datetime.timedelta(hours=3)})
        result = self.command_parser.parse("timers add every 3h top")
        self.assertDictEqual(result.sub_parser_result.args, valid_result)

    def test_add_negative(self):
        result = self.command_parser.parse("timers add")
        self.assertIsNone(result.sub_parser_result.args["top_placeholder"])

        with self.assertRaises(TooManyArgumentsError):
            self.command_parser.parse("timers add top X X")


if __name__ == "__main__":
    unittest.main()
