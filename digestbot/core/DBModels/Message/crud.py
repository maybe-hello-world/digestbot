from typing import List

from .Message import Message
import asyncpg
from digestbot.core.DBEngine.PostgreSQLEngine import PostgreSQLEngine


def make_insert_values_from_messages_array(messages: List[Message]) -> str:
    return ", ".join(
        [
            (
                f"('{message.username}', '{message.text}', {message.date}, "
                f"{message.reply_count}, {message.reply_users_count}, "
                f"{message.reactions_rate}, {message.thread_length}, '{message.channel_id}')"
            )
            for message in messages
        ]
    )


async def create_messages(db_engine: PostgreSQLEngine, messages: List[Message]) -> bool:
    request = f"""
    INSERT INTO Message (username, text, date, reply_count, reply_users_count,
                        reactions_rate, thread_length, channel_id)
    VALUES {make_insert_values_from_messages_array(messages)}
    """
    try:
        async with db_engine.engine.acquire() as connection:
            await connection.execute(request)
        status = True
    except asyncpg.QueryCanceledError or asyncpg.ConnectionFailureError:
        db_engine.logger.warn(
            f"Messages '{str(messages)}' was not passed into database."
        )
        status = False

    return status
