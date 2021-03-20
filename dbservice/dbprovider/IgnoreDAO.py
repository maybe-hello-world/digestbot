from typing import List

from .engine import db_engine, DBEngine


class IgnoreDAO:
    def __init__(self, engine: DBEngine):
        self.engine = engine

    async def get_ignore_list(self, author_id: str) -> List[str]:
        request = "SELECT ignore_username FROM IgnoreList WHERE author_username = $1"
        return await self.engine.make_fetch_rows(request, author_id)

    async def get_ignore_list_length(self, author_id: str) -> int:
        request = "SELECT COUNT(*) FROM IgnoreList WHERE author_username = $1"
        return await self.engine.make_fetchval(request, author_id)

    async def insert_into_ignore_list(self, author_id: str, ignore_id: str) -> bool:
        request = "INSERT INTO IgnoreList (author_username, ignore_username) VALUES ($1, $2) ON CONFLICT DO NOTHING"
        result = await self.engine.make_execute(request, author_id, ignore_id)
        return bool(result)  # 0 (false) if conflict occurred and name is already presented, 1 (true) otherwise

    async def delete_from_ignore_list(self, author_id, ignore_id) -> bool:
        request = "DELETE FROM IgnoreList WHERE author_username = $1 AND ignore_username = $2"
        result = await self.engine.make_execute(request, author_id, ignore_id)
        return bool(result)  # 0 (false) if nothing deleted, 1 (true) otherwise


ignore_dao = IgnoreDAO(db_engine)
