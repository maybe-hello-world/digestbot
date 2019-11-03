from __future__ import annotations

from typing import List, Optional, Dict

from digestbot.command_parser.command import Command
from digestbot.command_parser.parse_result import CommandParseResult


class CommandParser:
    def __init__(self, commands: List[Command],
                 name: Optional[str] = None,
                 sub_parsers: Optional[List[CommandParser]] = None):
        self.name = name
        self.commands = commands
        self.sub_parsers = sub_parsers or []

    def parse(self, text: str) -> Optional[CommandParseResult]:
        split = text.split()
        if not split:
            return None
        command_name = split[0].lower()
        for sub_parser in self.sub_parsers:
            if command_name == sub_parser.name:
                return CommandParseResult(command_name, {}, sub_parser.parse(' '.join(split[1:])))
        for c in self.commands:
            if command_name == c.name:
                return CommandParseResult(command_name, c.parse(split[1:]))
        return None
