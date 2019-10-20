from __future__ import annotations
from typing import List

from digestbot.core.command_parser.argument import Argument
from digestbot.core.command_parser.parse_result import Parsed, Default


class Command:

    def __init__(self, name: str, arguments: List[Argument], callback):
        self.name = name
        self.arguments = arguments
        self.callback = callback

    async def handle(self, params: List[str]):
        args = {}
        params_idx = 0
        for arg in self.arguments:
            args[arg.name] = arg.default
            if params_idx >= len(params):
                continue
            p = arg.parse(params[params_idx])
            if isinstance(p, Parsed):
                args[arg.name] = p.value
                params_idx += 1
        return await self.callback(args)


class CommandBuilder:

    def __init__(self, name):
        self.name = name
        self.arguments = []

    def add_argument(self, argument: Argument) -> CommandBuilder:
        self.arguments.append(argument)
        return self

    def build(self, callback) -> Command:
        return Command(self.name, self.arguments, callback)


