from dataclasses import dataclass
from typing import Any, Dict


class ParseResult:
    pass


@dataclass(frozen=True)
class Parsed(ParseResult):
    value: Any


@dataclass(frozen=True)
class Default(ParseResult):
    value: Any


@dataclass(frozen=True)
class CommandParseResult:
    command: str
    args: Dict[str, Any]
