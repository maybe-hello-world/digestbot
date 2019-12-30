from abc import abstractmethod
from datetime import timedelta
from typing import List, Optional, Any

from digestbot.command_parser.parse_result import ParseResult, Parsed, NotParsed


class Argument:
    def __init__(self, name: str, default: Optional[Any]):
        self.name = name
        self.default = default

    @abstractmethod
    def parse(self, text: str) -> ParseResult:
        pass


class IntArgument(Argument):
    def __init__(self, name: str, default: Optional[int] = None):
        super().__init__(name, default)

    def parse(self, text: str) -> ParseResult:
        result = _int_or_default(text)
        if result:
            return Parsed(result)
        else:
            return NotParsed(self.default)


class StringArgument(Argument):
    def __init__(self, name: str, default: Optional[str] = None):
        super().__init__(name, default)

    def parse(self, text: str) -> ParseResult:
        return Parsed(text)


class ChoiceArgument(Argument):
    def __init__(self, name: str, choices: List[str], default: Optional[str] = None):
        super().__init__(name, default)
        self.choices = choices

    def parse(self, text: str) -> ParseResult:
        if text in self.choices:
            return Parsed(text)
        return NotParsed(self.default)


class TimeDeltaArgument(Argument):
    def __init__(self, name: str, default: Optional[timedelta] = None):
        super().__init__(name, default)

    def parse(self, text: str) -> ParseResult:
        if not text or len(text) < 2:
            return NotParsed(self.default)
        suffix = text[-1]
        count = _int_or_default(text[:-1])
        if not count:
            return NotParsed(self.default)
        if suffix == "w":
            return Parsed(timedelta(weeks=count))
        elif suffix == "d":
            return Parsed(timedelta(days=count))
        elif suffix == "h":
            return Parsed(timedelta(hours=count))
        elif suffix == "m":
            return Parsed(timedelta(minutes=count))
        else:
            return NotParsed(self.default)


class ExactArgument(Argument):
    def __init__(self, name: str, value: str):
        super().__init__(name, value)
        self.value = value

    def parse(self, text: str) -> ParseResult:
        if text == self.value:
            return Parsed(self.value)
        else:
            return NotParsed(self.value)


def _int_or_default(text: str, default: Optional[int] = None) -> Optional[int]:
    try:
        return int(text)
    except ValueError:
        return default
