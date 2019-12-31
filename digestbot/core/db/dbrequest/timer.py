from typing import List, Tuple, Optional
import asyncpg

from digestbot.core.db.models import Timer
from digestbot.core.db.dbengine.PostgreSQLEngine import PostgreSQLEngine


async def list_timers(
    db_engine: PostgreSQLEngine, username: str
) -> Tuple[bool, Optional[List[Timer]]]:
    request = """
        SELECT * FROM timer
        WHERE username = ($1)
    """
    try:
        timers = await db_engine.make_fetch_rows(request, username)
        result = [Timer(**x) for x in timers]
        return True, result
    except (asyncpg.QueryCanceledError, asyncpg.ConnectionFailureError) as e:
        db_engine.logger.exception(e)
        return False, None


async def check_timer_existence(
    db_engine: PostgreSQLEngine, timer_name: str, username: str
) -> Tuple[bool, Optional[bool]]:
    request = """
                SELECT COUNT(*) FROM timer
                WHERE username = ($1) AND timer_name = ($2)
            """
    try:
        timers_count = await db_engine.make_fetch_rows(request, username, timer_name)
        return True, timers_count[0]["count"] > 0
    except (asyncpg.QueryCanceledError, asyncpg.ConnectionFailureError) as e:
        db_engine.logger.exception(e)
        return False, None


async def count_timers(
    db_engine: PostgreSQLEngine, username: str
) -> Tuple[bool, Optional[int]]:
    request = """
        SELECT COUNT(*) FROM timer
        WHERE username = ($1)
    """
    try:
        timers_count = await db_engine.make_fetch_rows(request, username)
        return True, timers_count[0]["count"]
    except (asyncpg.QueryCanceledError, asyncpg.ConnectionFailureError) as e:
        db_engine.logger.exception(e)
        return False, None


async def remove_timer(
    db_engine: PostgreSQLEngine, username: str, timer_name: str
) -> bool:
    request = """
        DELETE FROM timer
        WHERE username = ($1) AND timer_name = ($2)
    """
    try:
        await db_engine.make_execute(request, username, timer_name)
        return True
    except (asyncpg.QueryCanceledError, asyncpg.ConnectionFailureError) as e:
        db_engine.logger.exception(e)
        return False


async def upsert_timer(db_engine: PostgreSQLEngine, timer: Timer) -> bool:
    request = """
        INSERT INTO timer (channel_id, username, timer_name, delta, next_start, top_command)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (username, timer_name)
        DO UPDATE SET
            delta = EXCLUDED.delta,
            next_start = EXCLUDED.next_start,
            top_command = EXCLUDED.top_command;
    """
    try:
        await db_engine.make_execute(
            request,
            timer.channel_id,
            timer.username,
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
        if not answer:
            return None
        answer = answer[0]
        answer = Timer(**answer)
        return answer
    except (asyncpg.QueryCanceledError, asyncpg.ConnectionFailureError) as e:
        db_engine.logger.exception(e)
        return None
    except Exception as e:
        db_engine.logger.error("Error! Unhandled exception!")
        db_engine.logger.exception(e)
        return None
