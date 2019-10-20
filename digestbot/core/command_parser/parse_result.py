from dataclasses import dataclass
from typing import Any


class ParseResult:
    pass


@dataclass(frozen=True)
class Parsed(ParseResult):
    value: Any


@dataclass(frozen=True)
class Default(ParseResult):
    value: Any
