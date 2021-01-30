from decimal import Decimal
from typing import List, Any, Optional

from common.Enums import SortingType
from models import Message
from .engine import db_engine, DBEngine


class MessageDAO:
    def __init__(self, engine: DBEngine):
        self.engine = engine

    @staticmethod
    def __make_insert_values_from_messages_array(messages: List[Message]) -> List[tuple]:
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

    @staticmethod
    def __request_messages_to_message_class(request_messages: List[Any]) -> List[Message]:
        return [Message(**message) for message in request_messages]

    @staticmethod
    def __make_link_update_values_from_messages_array(messages: List[Message]) -> List[tuple]:
        return [(x.link, x.timestamp, x.channel_id) for x in messages]

    async def create_messages(self, messages: List[Message]) -> None:
        request = f"""
        INSERT INTO message (username, text, timestamp, reply_count, reply_users_count,
                            reactions_rate, thread_length, channel_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8);
        """

        sequence = self.__make_insert_values_from_messages_array(messages)
        await self.engine.make_execute_many(request, sequence)

    async def upsert_messages(self, messages: List[Message]) -> None:
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
        sequence = self.__make_insert_values_from_messages_array(messages)
        await self.engine.make_execute_many(request, sequence)

    async def get_messages_without_links(self) -> List[Message]:
        request = f"SELECT * FROM message WHERE link IS NULL;"

        messages = await self.engine.make_fetch_rows(request)
        return self.__request_messages_to_message_class(messages)

    async def update_message_links(self, messages: List[Message]) -> None:
        request = f" UPDATE message SET link=($1) WHERE timestamp=($2) AND channel_id=($3)"

        sequence = self.__make_link_update_values_from_messages_array(messages)
        await self.engine.make_execute_many(request, sequence)

    async def get_top_messages(
            self,
            after_ts: Decimal,
            sorting_type: SortingType = SortingType.REPLIES,
            top_count: int = 10
    ) -> List[Message]:
        request = f"""
            SELECT * FROM message
            WHERE timestamp >= {after_ts}
            ORDER BY {sorting_type.value} DESC
            LIMIT {top_count};
        """

        messages = await self.engine.make_fetch_rows(request)
        return self.__request_messages_to_message_class(messages)

    async def get_top_messages_by_channel_id(
            self,
            channel_id: str,
            after_ts: Decimal,
            sorting_type: SortingType = SortingType.REPLIES,
            top_count: int = 10,
    ) -> List[Message]:
        request = f"""
            SELECT * FROM message
            WHERE
                channel_id=($1)
            AND
                timestamp >= {after_ts}
            ORDER BY {sorting_type.value} DESC
            LIMIT {top_count};
        """

        messages = await self.engine.make_fetch_rows(request, channel_id)
        return self.__request_messages_to_message_class(messages)

    async def get_top_messages_by_category_name(
            self,
            category_name: str,
            after_ts: Decimal,
            sorting_type: SortingType = SortingType.REPLIES,
            top_count: int = 10,
            user_id: Optional[str] = None
    ) -> List[Message]:
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
        
        messages = await self.engine.make_fetch_rows(request, category_name, user_id)
        return self.__request_messages_to_message_class(messages)


message_dao = MessageDAO(db_engine)
