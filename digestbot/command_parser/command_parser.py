from __future__ import annotations

from typing import List, Optional

from digestbot.command_parser.command import Command
from digestbot.command_parser.parse_result import CommandParseResult


class CommandParser:
    def __init__(self, commands: List[Command]):
        self.commands = commands

    def parse(self, text: str) -> Optional[CommandParseResult]:
        split = text.split()
        if not split:
            return None
        command_name = split[0].lower()
        for c in self.commands:
            if command_name == c.name:
                return CommandParseResult(command_name, c.parse(split[1:]))
        return None
