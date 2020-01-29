from __future__ import annotations
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional, Dict, Any

from digestbot.command_parser.argument import (
    IntArgument,
    TimeDeltaArgument,
    ChoiceArgument,
    StringArgument,
)
from digestbot.command_parser.command import CommandBuilder
from digestbot.core.common.Enums import SortingType
from digestbot.core.ui_processor.common import parse_channel_id

top_arguments = (
    IntArgument("N", default=5),
    TimeDeltaArgument("time", default=timedelta(days=1)),
    ChoiceArgument(
        "sorting_method", ["replies", "length", "reactions"], default="replies"
    ),
    StringArgument("channel", default=None),
)
top_command = CommandBuilder("top").extend_with_arguments(top_arguments).build()


@dataclass(frozen=True)
class TopCommandArgs:
    N: int
    time: timedelta
    sorting_method: str

    channel_id: Optional[str] = None
    category_name: Optional[str] = None

    @staticmethod
    def _parse_channel(source_name: Optional[str]) -> Dict[str, str]:
        if not source_name:
            return {}

        channel_uid = parse_channel_id(channel=source_name)

        # Either ID successfully parsed...
        if channel_uid:
            return {"channel_id": channel_uid}

        # ...or it is category name. No other ways.
        return {"category_name": source_name}

    def is_all_channels_requested(self) -> bool:
        return self.category_name is None and self.channel_id is None

    def is_channel(self) -> bool:
        return self.channel_id is not None

    @staticmethod
    def from_dict(kwargs: Dict[str, Any]) -> TopCommandArgs:
        sorting_type_mapper = {
            "replies": "reply_count",
            "length": "thread_length",
            "reactions": "reactions_rate",
        }
        kwargs["sorting_method"] = SortingType(
            sorting_type_mapper[kwargs["sorting_method"]]
        )
        channel_parse = TopCommandArgs._parse_channel(kwargs["channel"])
        del kwargs["channel"]
        kwargs.update(channel_parse)
        return TopCommandArgs(**kwargs)
