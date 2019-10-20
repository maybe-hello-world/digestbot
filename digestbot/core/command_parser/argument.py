from abc import abstractmethod
from datetime import timedelta
from typing import List, Optional

from digestbot.core.command_parser.parse_result import ParseResult, Parsed, Default, NotParsed


class Argument:

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def parse(self, text: str) -> ParseResult:
        pass


class IntArgument(Argument):

    def __init__(self, name: str, default: int):
        super().__init__(name)
        self.default = default

    def parse(self, text: str) -> ParseResult:
        result = _int_or_default(text)
        if result:
            return Parsed(self.name, result)
        else:
            return Default(self.name, self.default)


class StringArgument(Argument):

    def __init__(self, name: str):
        super().__init__(name)

    def parse(self, text: str) -> ParseResult:
        if not text:
            return NotParsed()
        return Parsed(self.name, text)


class ChoiceArgument(Argument):

    def __init__(self, name: str, choices: List[str], default: str = None):
        super().__init__(name)
        self.choices = choices
        self.default = default

    def parse(self, text: str) -> ParseResult:
        if text in self.choices:
            return Parsed(self.name, text)
        return Default(self.name, self.default)


class DateArgument(Argument):

    def __init__(self, name: str, default: timedelta = None):
        super().__init__(name)
        self.default = default

    def parse(self, text: str) -> ParseResult:
        if not text or len(text) < 2:
            return Default(self.name, self.default)
        suffix = text[-1]
        count = _int_or_default(text[:-1])
        if not count:
            return Default(self.name, self.default)
        if suffix == 'w':
            return Parsed(self.name, timedelta(weeks=count))
        elif suffix == 'd':
            return Parsed(self.name, timedelta(days=count))
        elif suffix == 'h':
            return Parsed(self.name, timedelta(hours=count))
        else:
            return Default(self.name, self.default)


def _int_or_default(text: str, default: Optional[int] = None) -> Optional[int]:
    try:
        return int(text)
    except ValueError:
        return default