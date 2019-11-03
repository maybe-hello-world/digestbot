import asyncpg
from logging import Logger


def create_category_table() -> str:
    return """
        CREATE TABLE Category (
            id BIGSERIAL NOT NULL PRIMARY KEY, 
            username TEXT,  -- username is null if category created by developers
            name TEXT NOT NULL,
            channel_ids TEXT[],

            UNIQUE (username, name)
        );

        CREATE INDEX category_name_idx ON category (name);
    """


def create_message_table() -> str:
    return """
        CREATE TABLE Message (
            username TEXT NOT NULL,
            text TEXT NOT NULL,
            timestamp DECIMAL NOT NULL,
            reply_count INTEGER NOT NULL,
            reply_users_count INTEGER NOT NULL,
            reactions_rate FLOAT,
            thread_length INTEGER NOT NULL,
            channel_id TEXT,
            link TEXT NULL,
            PRIMARY KEY(channel_id, timestamp)
        );
    """


async def create_database(
    user: str,
    password: str,
    host: str,
    database_name: str,
    logger: Logger,
    port: int = None,
) -> bool:
    """
    Create database

    :param user: username
    :param password: password for user
    :param host: database server
    :param database_name: database name
    :param logger: logger for logging
    :param port: port for database server
    :return: status execution: 0 - Fail, 1 - Success
    """
    logger.info(f"Try to connect to database 'template1' with user '{user}'")
    try:
        sys_conn = await asyncpg.connect(
            database="template1", host=host, port=port, user=user, password=password
        )

        await sys_conn.execute(
            f"CREATE DATABASE {database_name} WITH "
            f'OWNER = "{user}" '
            f"ENCODING = 'UTF-8'"
        )

        await sys_conn.close()
        status = True
        logger.info(f"Database '{database_name}' was created")
    except (asyncpg.UndefinedObjectError, asyncpg.InvalidCatalogNameError):
        logger.error(
            f"User '{user}' or database 'template1' does not exist. "
            f"Or user '{user}' does not have enough permissions"
        )
        status = False
    except asyncpg.InvalidPasswordError:
        logger.error(f"User password incorrect")
        status = False

    return status


async def check_exist_tables(connection: asyncpg.Connection) -> bool:
    """
    Check exist table 'message' - default table
    :param connection: connection to database
    """
    return await connection.fetchval(
        """
        SELECT EXISTS (
            SELECT 1
            FROM   information_schema.tables
            WHERE  table_schema = 'public'
            AND    table_name = 'message'
        );
    """
    )


async def create_tables(connection: asyncpg.Connection, logger: Logger) -> bool:
    """
    Create tables for current connection
    :param connection: connection to database
    :param logger: logger for logging
    :return: status execution: 0 - Fail, 1 - Success
    """
    tables = {"Category": create_category_table(), "Message": create_message_table()}

    big_query = "\n".join(tables.values())
    logger.info(f"Will be created new tables: {', '.join(tables.keys())}")

    try:
        await connection.execute(big_query)
        status = True
        logger.info("Tables were created")
    except asyncpg.QueryCanceledError:
        logger.error(f"Tables were not created")
        status = False

    return status
