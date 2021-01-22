from __future__ import annotations

from typing import List, Dict, Any, Union, Iterable

from .argument import Argument, MultiArgument
from .exception import TooManyArgumentsError
from .parse_result import Parsed


class Command:
    def __init__(self, name: str, arguments: List[Union[MultiArgument, Argument]]):
        self.name = name
        self.arguments = arguments

    def parse(self, params: List[str]) -> Dict[str, Any]:
        args = {}
        params_idx = 0
        for arg in self.arguments:
            args[arg.name] = arg.default
            if params_idx >= len(params):
                continue
            if isinstance(arg, MultiArgument):
                p = arg.parse(params[params_idx:])
                args[arg.name] = p.value
                return args
            else:
                p = arg.parse(params[params_idx])
            if isinstance(p, Parsed):
                args[arg.name] = p.value
                params_idx += 1
        if params_idx < len(params):
            raise TooManyArgumentsError(
                f"Too many arguments provided for command `{self.name}`"
            )
        return args


class CommandBuilder:
    def __init__(self, name):
        self.name = name
        self.arguments = []

    def add_argument(self, argument: Union[MultiArgument, Argument]) -> CommandBuilder:
        self.arguments.append(argument)
        return self

    def extend_with_arguments(self, arguments: Iterable[Argument]):
        self.arguments.extend(arguments)
        return self

    def build(self) -> Command:
        return Command(self.name, self.arguments)
