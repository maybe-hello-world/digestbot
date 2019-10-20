import asyncio
import unittest
from datetime import timedelta

from digestbot.core.command_parser.argument import StringArgument, ChoiceArgument, DateArgument, IntArgument
from digestbot.core.command_parser.command import CommandBuilder
from digestbot.core.command_parser.parser import Parser


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

    def tearDown(self):
        self.loop.close()

    def test_something(self):

        async def test_func(args):
            self.assertEqual(10, args['N'])
            self.assertEqual('#general', args['channel'])
            self.assertEqual(timedelta(days=2), args['time'])
            self.assertEqual('replies', args['sorting_method'])

        top_command = CommandBuilder('top')\
            .add_argument(IntArgument('N', 10))\
            .add_argument(DateArgument('time', timedelta(days=1)))\
            .add_argument(ChoiceArgument('sorting_method', ['replies', 'length', 'reactions'], default='replies'))\
            .add_argument(StringArgument('channel'))\
            .build(test_func)

        parser = Parser([top_command])

        async def func():
            await parser.handle('top 2d #general')

        self.loop.run_until_complete(func())


if __name__ == '__main__':
    unittest.main()
