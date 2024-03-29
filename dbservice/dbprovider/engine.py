import asyncpg

import config
from common.LoggerFactory import create_logger


class DBEngine:
    def __init__(self):
        self.logger = create_logger("dbengine", config.LOG_LEVEL)
        self.pool = None

    async def ainit(self):
        self.pool = await asyncpg.create_pool(
            user=config.DB_USER,
            password=config.DB_PASS,
            database=config.DB_NAME,
            host=config.DB_HOST,
            port=config.DB_PORT
        )

    @staticmethod
    async def check_or_create_database():
        sys_conn = await asyncpg.connect(
            database="template1", host=config.DB_HOST, port=config.DB_PORT, user=config.DB_USER, password=config.DB_PASS
        )

        # check db existence
        result = await sys_conn.execute(f"SELECT 1 FROM pg_database WHERE datname='{config.DB_NAME}'")
        if not result:  # create DB
            await sys_conn.execute(
                f"CREATE DATABASE {config.DB_NAME} WITH "
                f'OWNER = "{config.DB_USER}" '
                f"ENCODING = 'UTF-8'"
            )

        await sys_conn.close()

    async def check_or_create_tables(self):
        tables = [
            """CREATE TABLE IF NOT EXISTS Timer (
                    channel_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    timer_name TEXT NOT NULL,
                    delta INTERVAL NOT NULL,
                    next_start TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                    top_command TEXT NOT NULL,
                    PRIMARY KEY(username, timer_name)
                );
            """,
            """CREATE TABLE IF NOT EXISTS Preset (
                    id BIGSERIAL NOT NULL PRIMARY KEY, 
                    username TEXT,  -- username is null if preset is created by developers
                    name TEXT NOT NULL,
                    channel_ids TEXT[],
                    UNIQUE (username, name)
                );
    
                CREATE INDEX IF NOT EXISTS preset_name_idx ON preset (name);
            """,
            """CREATE TABLE IF NOT EXISTS Message (
                    username TEXT NOT NULL,
                    timestamp DECIMAL NOT NULL,
                    reply_count INTEGER NOT NULL,
                    reply_users_count INTEGER NOT NULL,
                    reactions_rate FLOAT,
                    thread_length INTEGER NOT NULL,
                    channel_id TEXT,
                    link TEXT NULL,
                    PRIMARY KEY(channel_id, timestamp)
                );
            """,
            """CREATE TABLE IF NOT EXISTS IgnoreList ( 
                    author_username TEXT NOT NULL,
                    ignore_username TEXT NOT NULL,
                    UNIQUE (author_username, ignore_username)
                );
    
                CREATE INDEX IF NOT EXISTS author_name_idx ON IgnoreList (author_username);
            """
        ]

        big_query = "\n".join(tables)

        async with self.pool.acquire() as connection:
            await connection.execute(big_query)

    async def make_execute(self, request_string: str, *args):
        """
        Execute request
        :param request_string: request string
        """
        async with self.pool.acquire() as connection:
            return await connection.execute(request_string, *args)

    async def make_execute_many(self, request_string: str, sequence: list):
        """
        Execute request for each element in sequence
        :param request_string: request string
        :param sequence: list with data
        """
        async with self.pool.acquire() as connection:
            return await connection.executemany(request_string, sequence)

    async def make_fetch_rows(self, request_string: str, *args):
        """
        Fetch request
        :param request_string: request string
        """

        async with self.pool.acquire() as connection:
            return await connection.fetch(request_string, *args)

    async def make_fetchval(self, request_string: str, *args):
        """
        Fetch first value from first row returned
        :param request_string: request string
        :param args: args for SQL request
        :return: Value from 1st column of 1st row returned
        """

        async with self.pool.acquire() as connection:
            return await connection.fetchval(request_string, *args)

    async def close(self):
        """
        Close all connection with database
        """
        await self.pool.close()


db_engine = DBEngine()
