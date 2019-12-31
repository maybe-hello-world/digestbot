import unittest

from digestbot.command_parser.command_parser import CommandParser
from digestbot.core.ui_processor.presets.presets_command import presets_parser


class PresetsCommandParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.presets_parser = CommandParser(commands=[], sub_parsers=[presets_parser])

    def test_sub_parser(self):
        parse_result = self.presets_parser.parse("presets ls global")
        self.assertEqual("presets", parse_result.command)
        self.assertTrue(parse_result.is_sub_parser("presets"))

        sub_parse_result = parse_result.sub_parser_result
        self.assertEqual("ls", sub_parse_result.command)
        self.assertEqual("global", sub_parse_result.args["scope"])


if __name__ == "__main__":
    unittest.main()
