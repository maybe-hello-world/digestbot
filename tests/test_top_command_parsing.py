import unittest
from datetime import timedelta

from digestbot.command_parser.command_parser import CommandParser
from digestbot.command_parser.exception import TooManyArgumentsError

from digestbot.core.common.Enums import SortingType
from digestbot.core.ui_processor.top.top_command import top_command, TopCommandArgs


class TopCommandParsingTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.default = TopCommandArgs.from_dict(
            {  # update if defaults changes
                "N": 5,
                "time": timedelta(days=1),
                "sorting_method": "replies",
                "channel": None,
            }
        )
        cls.top_command = top_command
        cls.command_parser = CommandParser([cls.top_command])

    def test_full_command(self):
        result = self.command_parser.parse("top 25 3w reactions general")
        self.assertIsNotNone(result)
        args = TopCommandArgs.from_dict(result.args)
        self.assertEqual(25, args.N)
        self.assertEqual(timedelta(weeks=3), args.time)
        self.assertEqual(SortingType.REACTIONS, args.sorting_method)
        self.assertEqual(
            "general", args.category_name
        )  # can't test channel without connection to slack

    def test_no_params(self):
        result = self.command_parser.parse("top     ")
        self.assertIsNotNone(result)
        args = TopCommandArgs.from_dict(result.args)
        self.assertEqual(self.default, args)

    def test_mixed_params(self):
        result = self.command_parser.parse("top 3w i_love_python")
        self.assertIsNotNone(result)
        args = TopCommandArgs.from_dict(result.args)
        expected = TopCommandArgs(
            N=self.default.N,
            time=timedelta(weeks=3),
            sorting_method=self.default.sorting_method,
            category_name="i_love_python",
        )
        self.assertEqual(expected, args)

    def test_no_command(self):
        result = self.command_parser.parse("")
        self.assertIsNone(result)

    def test_too_many_arguments(self):
        with self.assertRaises(TooManyArgumentsError):
            self.command_parser.parse("top a a")
        with self.assertRaises(TooManyArgumentsError):
            self.command_parser.parse("top a a a a a a a a a a")


if __name__ == "__main__":
    unittest.main()
