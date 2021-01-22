from typing import List, Tuple, Any, Optional
import asyncpg

from ..dbengine.PostgreSQLEngine import PostgreSQLEngine
from ..models import Category


def array_channel_ids_to_sql_insert_request(channel_ids: List[str]) -> str:
    return ", ".join([f'"{channel}"' for channel in channel_ids])


def make_insert_values_from_messages_array(categories: List[Category]) -> str:
    return ", ".join(
        [
            f"('{category.name}', '{{{array_channel_ids_to_sql_insert_request(category.channel_ids)}}}')"
            for category in categories
        ]
    )


def request_categories_to_category_class(
    request_categories: List[Any]
) -> List[Category]:
    return [Category(**category) for category in request_categories]


async def get_category_by_name(
    db_engine: PostgreSQLEngine, name: str
) -> Tuple[bool, Category]:
    request = f"""
    SELECT * FROM category
    WHERE name='{name}';
    """
    try:
        categories_base = await db_engine.make_fetch_rows(request)
        status = True
        category = request_categories_to_category_class(categories_base)

        if len(category) == 0:
            category = None
        else:
            category = category[0]

    except asyncpg.QueryCanceledError or asyncpg.ConnectionFailureError:
        db_engine.logger.warn(f"Select Category with name '{name}' was crashed")
        status = False
        category = None

    return status, category


async def get_categories(db_engine: PostgreSQLEngine, user_id: Optional[str], include_global: bool = True) -> List[Category]:
    user_query = """SELECT * FROM category WHERE username = $1"""
    global_query = """SELECT * FROM category WHERE username IS NULL"""

    union_query = f"""{user_query} UNION ALL {global_query}"""

    if user_id is None:
        return request_categories_to_category_class(await db_engine.make_fetch_rows(global_query))
    else:
        if include_global:
            return request_categories_to_category_class(await db_engine.make_fetch_rows(union_query, user_id))
        else:
            return request_categories_to_category_class(await db_engine.make_fetch_rows(user_query, user_id))


async def add_or_update_category(
        db_engine: PostgreSQLEngine,
        user_id: Optional[str],
        name: str, channels: List[str],
        max_user_categories_count: int) -> Optional[Category]:
    query = """INSERT INTO category (username, name, channel_ids) 
                (SELECT $1, $2, $3 WHERE (SELECT COUNT(*) FROM category WHERE username = $1) < $4)
                ON CONFLICT (username, name)
                DO UPDATE SET 
                    username = excluded.username, 
                    name = excluded.name, 
                    channel_ids = excluded.channel_ids
                RETURNING *"""

    result = await db_engine.make_fetch_rows(query, user_id, name, channels, max_user_categories_count)
    result_categories = request_categories_to_category_class(result)
    if result_categories:
        return result_categories[0]
    return None


async def remove_category(db_engine: PostgreSQLEngine, user_id: str, name: str) -> Optional[Category]:
    query = """DELETE FROM category WHERE username = $1 AND name = $2 RETURNING *"""

    result = await db_engine.make_fetch_rows(query, user_id, name)

    if not result:
        return None
    return request_categories_to_category_class(result)[0]


async def get_all_categories(
    db_engine: PostgreSQLEngine
) -> Tuple[bool, List[Category]]:
    request = f"""
    SELECT * FROM category;
    """
    try:
        categories_base = await db_engine.make_fetch_rows(request)
        status = True
        categories = request_categories_to_category_class(categories_base)
    except asyncpg.QueryCanceledError or asyncpg.ConnectionFailureError:
        db_engine.logger.warn(f"Select all categories was crashed")
        status = False
        categories = None

    return status, categories
