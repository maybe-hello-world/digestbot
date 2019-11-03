import unittest

from digestbot.core.ui_processor.request_parser import parser


class MyTestCase(unittest.TestCase):

    def test_sub_parser(self):
        parse_result = parser.parse('presets ls global')
        self.assertEqual('presets', parse_result.command)
        self.assertTrue(parse_result.is_sub_parser('presets'))

        sub_parse_result = parse_result.sub_parser_result
        self.assertEqual('ls', sub_parse_result.command)
        self.assertEqual('global', sub_parse_result.args['scope'])


if __name__ == '__main__':
    unittest.main()
