import unittest
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from digestbot.command_parser.argument import StringArgument, ChoiceArgument, TimeDeltaArgument, IntArgument
from digestbot.command_parser.command import CommandBuilder
from digestbot.command_parser.command_parser import CommandParser
from digestbot.command_parser.exception import TooManyArgumentsError


@dataclass(frozen=True)
class TopCommand:
    N: int
    time: timedelta
    sorting_method: str
    channel: Optional[str]


class TopCommandParsingTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.default = TopCommand(10, timedelta(days=1), 'replies', None)
        cls.top_command = CommandBuilder('top')\
            .add_argument(IntArgument('N', default=cls.default.N))\
            .add_argument(TimeDeltaArgument('time', default=cls.default.time))\
            .add_argument(ChoiceArgument('sorting_method', ['replies', 'length', 'reactions'],
                                         default=cls.default.sorting_method))\
            .add_argument(StringArgument('channel', default=cls.default.channel))\
            .build()
        cls.command_parser = CommandParser([cls.top_command])

    def test_full_command(self):
        result = self.command_parser.parse('top 25 3w reactions #general')
        self.assertIsNotNone(result)
        args = TopCommand(**result.args)
        self.assertEqual(25, args.N)
        self.assertEqual(timedelta(weeks=3), args.time)
        self.assertEqual('reactions', args.sorting_method)
        self.assertEqual('#general', args.channel)

    def test_no_params(self):
        result = self.command_parser.parse('top     ')
        self.assertIsNotNone(result)
        args = TopCommand(**result.args)
        self.assertEqual(self.default, args)

    def test_mixed_params(self):
        result = self.command_parser.parse('top 3w i_love_python')
        self.assertIsNotNone(result)
        args = TopCommand(**result.args)
        expected = TopCommand(self.default.N, timedelta(weeks=3), self.default.sorting_method, 'i_love_python')
        self.assertEqual(expected, args)

    def test_no_command(self):
        result = self.command_parser.parse('')
        self.assertIsNone(result)

    def test_too_many_arguments(self):
        with self.assertRaises(TooManyArgumentsError):
            self.command_parser.parse('top a a')
        with self.assertRaises(TooManyArgumentsError):
            self.command_parser.parse('top a a a a a a a a a a')


if __name__ == '__main__':
    unittest.main()
