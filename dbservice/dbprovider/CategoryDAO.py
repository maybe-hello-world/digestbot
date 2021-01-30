from typing import List, Any, Optional

from models import Category
from .engine import db_engine, DBEngine


class CategoryDAO:
    def __init__(self, engine: DBEngine):
        self.engine = engine

    @staticmethod
    def __request_categories_to_category_class(request_categories: List[Any]) -> List[Category]:
        return [Category(**category) for category in request_categories]

    async def get_all_categories(self) -> List[Category]:
        request = f"SELECT * FROM category;"
        categories = await self.engine.make_fetch_rows(request)
        categories = self.__request_categories_to_category_class(categories)
        return categories

    async def get_category_by_name(self, name) -> List[Category]:
        request = f"SELECT * FROM category WHERE name='{name}';"

        categories_base = await self.engine.make_fetch_rows(request)
        return self.__request_categories_to_category_class(categories_base)

    async def get_categories(self, user_id: Optional[str], include_global: bool = True) -> List[Category]:
        user_query = "SELECT * FROM category WHERE username = $1"
        global_query = "SELECT * FROM category WHERE username IS NULL"
        union_query = f"{user_query} UNION ALL {global_query}"

        if user_id is None:
            result = await self.engine.make_fetch_rows(global_query)
        elif user_id is not None and include_global:
            result = await self.engine.make_fetch_rows(union_query, user_id)
        else:
            result = await self.engine.make_fetch_rows(user_query, user_id)

        return self.__request_categories_to_category_class(result)

    async def add_or_update_category(
            self,
            user_id: str,
            name: str,
            channels: List[str],
            max_user_categories_count: int
    ) -> Optional[Category]:
        query = """INSERT INTO category (username, name, channel_ids) 
                    (SELECT $1, $2, $3 WHERE (SELECT COUNT(*) FROM category WHERE username = $1) < $4)
                    ON CONFLICT (username, name)
                    DO UPDATE SET 
                        username = excluded.username, 
                        name = excluded.name, 
                        channel_ids = excluded.channel_ids
                    RETURNING *"""

        result = await self.engine.make_fetch_rows(query, user_id, name, channels, max_user_categories_count)
        result = self.__request_categories_to_category_class(result)
        return result[0] if result else None

    async def remove_category(self, user_id: str, name: str) -> Optional[Category]:
        query = "DELETE FROM category WHERE username = $1 AND name = $2 RETURNING *"

        result = await self.engine.make_fetch_rows(query, user_id, name)
        result = self.__request_categories_to_category_class(result)
        return result[0] if result else None


category_dao = CategoryDAO(db_engine)
