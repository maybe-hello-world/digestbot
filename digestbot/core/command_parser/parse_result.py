from dataclasses import dataclass


class ParseResult:
    pass


@dataclass(frozen=True)
class Parsed(ParseResult):
    name: str
    value: object


@dataclass(frozen=True)
class Default(ParseResult):
    name: str
    value: object


@dataclass(frozen=True)
class NotParsed(ParseResult):
    pass