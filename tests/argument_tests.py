import unittest
from datetime import timedelta

from digestbot.core.command_parser.argument import TimeDeltaArgument


class TimeDeltaArgumentArgumentTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.argument = TimeDeltaArgument('date', default=None)

    def test_minutes(self):
        expected = timedelta(minutes=3)
        actual = self.argument.parse('3m').value
        self.assertEqual(expected, actual)

    def test_hours(self):
        expected = timedelta(hours=3)
        actual = self.argument.parse('3h').value
        self.assertEqual(expected, actual)

    def test_days(self):
        expected = timedelta(days=3)
        actual = self.argument.parse('3d').value
        self.assertEqual(expected, actual)

    def test_weeks(self):
        expected = timedelta(weeks=3)
        actual = self.argument.parse('3w').value
        self.assertEqual(expected, actual)

        expected = timedelta(weeks=-3)
        actual = self.argument.parse('-3w').value
        self.assertEqual(expected, actual)

    def test_other(self):
        expected = None
        actual = self.argument.parse('3p').value
        self.assertEqual(expected, actual)

if __name__ == '__main__':
    unittest.main()
