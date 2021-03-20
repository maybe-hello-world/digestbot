from typing import List, Any, Optional

from models import Preset
from .engine import db_engine, DBEngine


class PresetDAO:
    def __init__(self, engine: DBEngine):
        self.engine = engine

    @staticmethod
    def __request_presets_to_preset_class(request_presets: List[Any]) -> List[Preset]:
        return [Preset(**p) for p in request_presets]

    async def get_all_presets(self) -> List[Preset]:
        request = f"SELECT * FROM preset;"
        presets = await self.engine.make_fetch_rows(request)
        presets = self.__request_presets_to_preset_class(presets)
        return presets

    async def get_preset_by_name(self, name) -> List[Preset]:
        request = f"SELECT * FROM preset WHERE name='{name}';"

        presets_base = await self.engine.make_fetch_rows(request)
        return self.__request_presets_to_preset_class(presets_base)

    async def get_presets(self, user_id: Optional[str], include_global: bool = True) -> List[Preset]:
        user_query = "SELECT * FROM preset WHERE username = $1"
        global_query = "SELECT * FROM preset WHERE username IS NULL"
        union_query = f"{user_query} UNION ALL {global_query}"

        if user_id is None:
            result = await self.engine.make_fetch_rows(global_query)
        elif user_id is not None and include_global:
            result = await self.engine.make_fetch_rows(union_query, user_id)
        else:
            result = await self.engine.make_fetch_rows(user_query, user_id)

        return self.__request_presets_to_preset_class(result)

    async def add_or_update_preset(
            self,
            user_id: str,
            name: str,
            channels: List[str],
            max_user_presets_count: int
    ) -> Optional[Preset]:
        query = """INSERT INTO preset (username, name, channel_ids) 
                    (SELECT $1, $2, $3 WHERE (SELECT COUNT(*) FROM preset WHERE username = $1) < $4)
                    ON CONFLICT (username, name)
                    DO UPDATE SET 
                        username = excluded.username, 
                        name = excluded.name, 
                        channel_ids = excluded.channel_ids
                    RETURNING *"""

        result = await self.engine.make_fetch_rows(query, user_id, name, channels, max_user_presets_count)
        result = self.__request_presets_to_preset_class(result)
        return result[0] if result else None

    async def remove_preset(self, user_id: str, name: str) -> Optional[Preset]:
        query = "DELETE FROM preset WHERE username = $1 AND name = $2 RETURNING *"

        result = await self.engine.make_fetch_rows(query, user_id, name)
        result = self.__request_presets_to_preset_class(result)
        return result[0] if result else None

    async def get_custom_preset_count(self) -> int:
        query = "SELECT COUNT(*) FROM Preset WHERE username IS NOT NULL"
        return await self.engine.make_fetchval(query)


preset_dao = PresetDAO(db_engine)
