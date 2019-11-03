from typing import List, Tuple, Optional
import asyncpg

from digestbot.core import PostgreSQLEngine, Timer


async def list_timers(
    db_engine: PostgreSQLEngine, channel_id: str
) -> Tuple[bool, Optional[List[Timer]]]:
    request = """
        SELECT * FROM timer
        WHERE channel_id == ($1)
    """
    try:
        timers = await db_engine.make_fetch_rows(request, channel_id)
        result = [Timer(**x) for x in timers]
        return True, result
    except (asyncpg.QueryCanceledError, asyncpg.ConnectionFailureError) as e:
        db_engine.logger.exception(e)
        return False, None


async def remove_timer(
    db_engine: PostgreSQLEngine, channel_id: str, timer_name: str
) -> bool:
    request = """
        DELETE FROM timer
        WHERE channel_id == ($1) AND timer_name == ($2)
    """
    try:
        await db_engine.make_execute(request, channel_id, timer_name)
        return True
    except (asyncpg.QueryCanceledError, asyncpg.ConnectionFailureError) as e:
        db_engine.logger.exception(e)
        return False


async def upsert_timer(db_engine: PostgreSQLEngine, timer: Timer) -> bool:
    request = """
        INSERT INTO timer (channel_id, timer_name, delta, next_start, top_command)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (channel_id, timer_name)
        DO UPDATE SET
            delta = EXCLUDED.delta,
            next_start = EXCLUDED.next_start,
            top_command = EXCLUDED.top_command;
    """
    try:
        await db_engine.make_execute(
            request,
            timer.channel_id,
            timer.timer_name,
            timer.delta,
            timer.next_start,
            timer.top_command,
        )
        return True
    except (asyncpg.QueryCanceledError, asyncpg.ConnectionFailureError) as e:
        db_engine.logger.exception(e)
        return False


async def get_nearest_timer(db_engine: PostgreSQLEngine) -> Optional[Timer]:
    request = """
        SELECT * FROM timer
        WHERE next_start = (
            SELECT MIN(next_start) FROM timer
        );
    """
    try:
        answer = await db_engine.make_fetch_rows(request)
        answer = Timer(**answer)
        return answer
    except (asyncpg.QueryCanceledError, asyncpg.ConnectionFailureError) as e:
        db_engine.logger.exception(e)
        return None
