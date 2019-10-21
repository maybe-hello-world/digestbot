from dataclasses import dataclass
from typing import Any, Dict


class ParseResult:
    value: Any


@dataclass(frozen=True)
class Parsed(ParseResult):
    value: Any


@dataclass(frozen=True)
class NotParsed(ParseResult):
    value: Any


@dataclass(frozen=True)
class CommandParseResult:
    command: str
    args: Dict[str, Any]
