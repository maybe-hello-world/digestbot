from __future__ import annotations

from typing import List

from digestbot.core.command_parser.command import Command


class Parser:

    def __init__(self, commands: List[Command]):
        self.commands = commands

    async def handle(self, text: str):
        split = text.split()
        command_name = split[0]
        for c in self.commands:
            if command_name == c.name:
                return await c.handle(split[1:])
        return None


class ParserBuilder:

    def __init__(self):
        self.commands = []

    def add_command(self, command: Command) -> ParserBuilder:
        self.commands.append(command)
        return self

    def build(self) -> Parser:
        return Parser(self.commands)