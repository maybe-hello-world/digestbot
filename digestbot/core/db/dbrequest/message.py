from typing import List, Tuple, Any, Optional
from decimal import Decimal
import asyncpg

from digestbot.core import Message, PostgreSQLEngine
from digestbot.core.common.Enums import SortingType


def make_insert_values_from_messages_array(messages: List[Message]) -> List[tuple]:
    return [
        (
            message.username,
            message.text,
            message.timestamp,
            message.reply_count,
            message.reply_users_count,
            message.reactions_rate,
            message.thread_length,
            message.channel_id,
        )
        for message in messages
    ]


def request_messages_to_message_class(request_messages: List[Any]) -> List[Message]:
    return [Message(**message) for message in request_messages]


async def create_messages(db_engine: PostgreSQLEngine, messages: List[Message]) -> bool:
    request = f"""
    INSERT INTO message (username, text, timestamp, reply_count, reply_users_count,
                        reactions_rate, thread_length, channel_id)
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8);
    """
    try:
        await db_engine.make_execute_many(
            request, make_insert_values_from_messages_array(messages)
        )
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
    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    ON CONFLICT (timestamp, channel_id)
    DO UPDATE SET
        reply_count = EXCLUDED.reply_count,
        reply_users_count = EXCLUDED.reply_users_count,
        reactions_rate = EXCLUDED.reactions_rate,
        thread_length = EXCLUDED.thread_length;
    """
    try:
        await db_engine.make_execute_many(
            request, make_insert_values_from_messages_array(messages)
        )
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


def make_link_update_values_from_messages_array(messages: List[Message]) -> List[tuple]:
    return [(x.link, x.timestamp, x.channel_id) for x in messages]


async def update_message_links(
    db_engine: PostgreSQLEngine, messages: List[Message]
) -> bool:
    request = f"""
        UPDATE message
        SET link=($1)
        WHERE timestamp=($2) AND channel_id=($3)
        """
    try:
        await db_engine.make_execute_many(
            request, make_link_update_values_from_messages_array(messages=messages)
        )
        status = True
    except (asyncpg.QueryCanceledError, asyncpg.ConnectionFailureError) as e:
        db_engine.logger.warn("Updating message permalinks crashed. Stacktrace:")
        db_engine.logger.exception(e)
        status = False
    return status


async def get_top_messages(
    db_engine: PostgreSQLEngine,
    after_ts: Decimal,
    sorting_type: SortingType = SortingType.REPLIES,
    top_count: int = 10,
) -> Tuple[bool, List[Message]]:
    request = f"""
    SELECT * FROM message
    WHERE timestamp >= {after_ts}
    ORDER BY {sorting_type.value} DESC
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
    sorting_type: SortingType = SortingType.REPLIES,
    top_count: int = 10,
) -> Tuple[bool, List[Message]]:
    request = f"""
    SELECT * FROM message
    WHERE
        channel_id=($1)
    AND
        timestamp >= {after_ts}
    ORDER BY {sorting_type.value} DESC
    LIMIT {top_count};
    """
    try:
        messages_base = await db_engine.make_fetch_rows(request, channel_id)
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
    sorting_type: SortingType = SortingType.REPLIES,
    top_count: int = 10,
    user_id: Optional[str] = None
) -> Tuple[bool, List[Message]]:
    request = f"""
    WITH categories AS (
        SELECT *
        FROM category
        WHERE name = $1
          AND (username = $2 OR username IS NULL)
        ORDER BY username NULLS LAST
        LIMIT 1
    )
    SELECT message.* FROM message
        JOIN categories category
        ON message.channel_id=ANY(category.channel_ids)
        WHERE message.timestamp >= {after_ts}
        ORDER BY {sorting_type.value} DESC
        LIMIT {top_count};
    """
    try:
        messages_base = await db_engine.make_fetch_rows(request, category_name, user_id)
        status = True
        messages = request_messages_to_message_class(messages_base)
    except asyncpg.QueryCanceledError or asyncpg.ConnectionFailureError:
        db_engine.logger.warn(
            f"Selecting top messages for category '{category_name}' was crashed"
        )
        status = False
        messages = None

    return status, messages
