from datetime import datetime
from typing import List, Optional

from models import Timer
from .engine import db_engine, DBEngine


class TimerDAO:
    def __init__(self, engine: DBEngine):
        self.engine = engine

    async def list_timers(self, username: str) -> List[Timer]:
        request = "SELECT * FROM timer WHERE username = ($1)"

        timers = await self.engine.make_fetch_rows(request, username)
        return [Timer(**x) for x in timers]

    async def check_timer_existence(self, timer_name: str, username: str) -> bool:
        request = "SELECT EXISTS(SELECT * FROM timer WHERE username = ($1) AND timer_name = ($2))"
        timer_count = await self.engine.make_fetch_rows(request, username, timer_name)
        return bool(timer_count[0][0])

    async def count_timers(self, username: str) -> int:
        request = """
            SELECT COUNT(*) FROM timer
            WHERE username = ($1)
        """

        timers_count = await self.engine.make_fetch_rows(request, username)
        return timers_count[0][0]

    async def remove_timer(self, username: str, timer_name: str) -> None:
        request = "DELETE FROM timer WHERE username = ($1) AND timer_name = ($2)"
        await self.engine.make_execute(request, username, timer_name)

    async def insert_timer(self, timer: Timer, max_timers_count: int) -> bool:
        request = """
            INSERT INTO timer (channel_id, username, timer_name, delta, next_start, top_command)
            (SELECT $1, $2, $3, $4, $5, $6
            WHERE (SELECT COUNT(*) FROM timer WHERE username = $2) < $7)
            RETURNING True
        """

        result = await self.engine.make_fetch_rows(
            request,
            timer.channel_id,
            timer.username,
            timer.timer_name,
            timer.delta,
            timer.next_start,
            timer.top_command,
            max_timers_count,
        )
        return len(result) > 0  # len == 1 when insertion succeeded, 0 otherwise

    async def update_timer_next_start(self, timer: Timer) -> bool:
        request = """
            UPDATE timer SET
            next_start = $3
            WHERE username = $1 AND timer_name = $2
            RETURNING True
        """

        result = await self.engine.make_fetch_rows(request, timer.username, timer.timer_name, timer.next_start)
        rows_updated = len(result)
        if rows_updated > 1:
            self.engine.logger.critical(
                f"Timers with similar names within one user are existing! "
                f"Username: {timer.username}, "
                f"timer name: {timer.timer_name}, "
                f"amount: {rows_updated}"
            )
            return True

        return rows_updated == 1

    async def get_nearest_timer(self, time_border: datetime) -> Optional[Timer]:
        request = """
            SELECT * FROM timer
            WHERE next_start = (
                SELECT MIN(next_start) FROM timer
                WHERE next_start > $1
            );
        """

        answer = await self.engine.make_fetch_rows(request, time_border)
        if not answer:
            return None
        answer = answer[0]
        answer = Timer(**answer)
        return answer

    async def get_overdue_timers(self, time_border: datetime) -> List[Timer]:
        """
        Return timers with next_start date < time_border date

        :return: None if any error, List of timers otherwise
        """
        request = """
            SELECT * FROM timer
            WHERE next_start < $1
        """

        overdue_timers = await self.engine.make_fetch_rows(request, time_border)
        result = [Timer(**x) for x in overdue_timers]
        return result


timer_dao = TimerDAO(db_engine)
