from typing import List, Tuple, Any
from decimal import Decimal
import asyncpg
import enum

from digestbot.core import Message, PostgreSQLEngine


class SortingType(enum.Enum):
    REPLY_COUNT = "reply_count"
    THREAD_LENGTH = "thread_length"
    REACTIONS_RATE = "reactions_rate"


def make_insert_values_from_messages_array(messages: List[Message]) -> str:
    return ", ".join(
        [
            (
                f"('{message.username}', '{message.text}', {message.timestamp}, "
                f"{message.reply_count}, {message.reply_users_count}, "
                f"{message.reactions_rate}, {message.thread_length}, '{message.channel_id}')"
            )
            for message in messages
        ]
    )


def request_messages_to_message_class(request_messages: List[Any]) -> List[Message]:
    return [Message(**message) for message in request_messages]


async def create_messages(db_engine: PostgreSQLEngine, messages: List[Message]) -> bool:
    request = f"""
    INSERT INTO message (username, text, timestamp, reply_count, reply_users_count,
                        reactions_rate, thread_length, channel_id)
    VALUES {make_insert_values_from_messages_array(messages)};
    """
    try:
        await db_engine.make_execute(request)
        status = True
    except asyncpg.QueryCanceledError or asyncpg.ConnectionFailureError:
        db_engine.logger.warn(
            f"Messages '{str(messages)}' was not passed into database."
        )
        status = False

    return status


async def upsert_messages(db_engine: PostgreSQLEngine, messages: List[Message]) -> bool:
    request = f"""
    INSERT INTO message (username, text, timestamp, reply_count, reply_users_count,
                        reactions_rate, thread_length, channel_id)
    VALUES {make_insert_values_from_messages_array(messages)}
    ON CONFLICT (timestamp, channel_id)
    DO UPDATE SET
        reply_count = EXCLUDED.reply_count,
        reply_users_count = EXCLUDED.reply_users_count,
        reactions_rate = EXCLUDED.reactions_rate,
        thread_length = EXCLUDED.thread_length;
    """
    try:
        await db_engine.make_execute(request)
        status = True
    except asyncpg.QueryCanceledError or asyncpg.ConnectionFailureError:
        db_engine.logger.warn(
            f"Messages '{str(messages)}' was not passed into database."
        )
        status = False

    return status


async def get_messages_without_links(
    db_engine: PostgreSQLEngine
) -> Tuple[bool, List[Message]]:
    request = f"""
    SELECT * FROM message
    WHERE link IS NULL;
    """
    try:
        messages_base = await db_engine.make_fetch_rows(request)
        status = True
        messages = request_messages_to_message_class(messages_base)
    except asyncpg.QueryCanceledError or asyncpg.ConnectionFailureError:
        db_engine.logger.warn(f"Selecting messages without links was crashed")
        status = False
        messages = None

    return status, messages


async def get_top_messages(
    db_engine: PostgreSQLEngine,
    after_ts: Decimal,
    sorting_type: SortingType = SortingType.THREAD_LENGTH,
    top_count: int = 10,
) -> Tuple[bool, List[Message]]:
    request = f"""
    SELECT * FROM message
    WHERE timestamp >= {after_ts}
    ORDER BY {sorting_type.value}
    LIMIT {top_count};
    """
    try:
        messages_base = await db_engine.make_fetch_rows(request)
        status = True
        messages = request_messages_to_message_class(messages_base)
    except asyncpg.QueryCanceledError or asyncpg.ConnectionFailureError:
        db_engine.logger.warn(f"Selecting top messages was crashed")
        status = False
        messages = None

    return status, messages


async def get_top_messages_by_channel_id(
    db_engine: PostgreSQLEngine,
    channel_id: str,
    after_ts: Decimal,
    sorting_type: SortingType = SortingType.THREAD_LENGTH,
    top_count: int = 10,
) -> Tuple[bool, List[Message]]:
    request = f"""
    SELECT * FROM message
    WHERE
        channel_id='{channel_id}'
    AND
        timestamp >= {after_ts}
    ORDER BY {sorting_type.value}
    LIMIT {top_count};
    """
    try:
        messages_base = await db_engine.make_fetch_rows(request)
        status = True
        messages = request_messages_to_message_class(messages_base)
    except asyncpg.QueryCanceledError or asyncpg.ConnectionFailureError:
        db_engine.logger.warn(
            f"Selecting top messages for channel_id '{channel_id}' was crashed"
        )
        status = False
        messages = None

    return status, messages


async def get_top_messages_by_category_name(
    db_engine: PostgreSQLEngine,
    category_name: str,
    after_ts: Decimal,
    sorting_type: SortingType = SortingType.THREAD_LENGTH,
    top_count: int = 10,
) -> Tuple[bool, List[Message]]:
    request = f"""
    SELECT message.* FROM message
    JOIN category
    ON message.channel_id=ANY(category.channel_ids)

    WHERE
        category.name='{category_name}'
    AND
        message.timestamp >= {after_ts}

    ORDER BY {sorting_type.value}
    LIMIT {top_count};
    """
    try:
        messages_base = await db_engine.make_fetch_rows(request)
        status = True
        messages = request_messages_to_message_class(messages_base)
    except asyncpg.QueryCanceledError or asyncpg.ConnectionFailureError:
        db_engine.logger.warn(
            f"Selecting top messages for category '{category_name}' was crashed"
        )
        status = False
        messages = None

    return status, messages
