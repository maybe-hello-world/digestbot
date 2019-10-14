import logging
import asyncpg
import sys

from digestbot.core.DBEngine.utils.createdb import (
    create_database,
    check_exist_tables,
    create_tables,
)


class PostgreSQLEngine:
    def __init__(self):
        self.logger: logging.Logger
        self.engine: asyncpg.Connection

        self.__setting_logger()

    def __setting_logger(self):
        """
        Setting handlers and level of logging for self.logger
        """

        self.logger = logging.getLogger("DBEngine")
        self.logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)  # TODO: change after dockerization
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%m.%d.%Y-%I:%M:%S",
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    async def connect_to_database(
        self, user: str, password: str, database_name: str, port: int = None
    ) -> bool:
        """
        Create connection to database

        :param user: user name
        :param password: password for username
        :param database_name: database name
        :param port: port for database server
        :return: status execution: 0 - Fail, 1 - Success
        """
        self.logger.info(f"Try to connect to '{database_name}' database")
        try:
            self.engine = await asyncpg.create_pool(
                user=user, password=password, database=database_name, port=port
            )
            status = 2
        except asyncpg.InvalidCatalogNameError:
            self.logger.info(
                f"Database '{database_name}' does not exist. It Will be created for user '{user}'"
            )
            status = await create_database(
                user=user,
                password=password,
                database_name=database_name,
                logger=self.logger,
                port=port,
            )
        except asyncpg.InvalidPasswordError:
            status = 0
            self.logger.error(f"Invalid password for user '{user}'")
        except asyncpg.UndefinedObjectError:
            status = 0
            self.logger.error(f"User '{user}' does not exist")

        if status == 1:
            status = await self.connect_to_database(user, password, database_name, port)

        if status == 2:
            async with self.engine.acquire() as connection:
                exist_tables = await check_exist_tables(connection)

            if not exist_tables:
                async with self.engine.acquire() as connection:
                    status = await create_tables(
                        connection=connection, logger=self.logger
                    )

        return status

    async def make_execute(self, request_string: str):
        """
        Execute request
        :param request_string: request string
        """
        async with self.engine.acquire() as connection:
            return await connection.execute(request_string)

    async def make_fetch_rows(self, request_string: str):
        """
        Fetch request
        :param request_string: request string
        """

        async with self.engine.acquire() as connection:
            return await connection.fetch(request_string)

    async def close(self):
        """
        Close all connection with database
        """
        await self.engine.close()
