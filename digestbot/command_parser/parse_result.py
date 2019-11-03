from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


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
    sub_parser_result: CommandParseResult = None

    def is_sub_parser(self, command_name) -> bool:
        return self.sub_parser_result is not None and self.command == command_name
