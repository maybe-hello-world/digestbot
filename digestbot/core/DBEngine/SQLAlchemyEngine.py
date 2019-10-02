from sqlalchemy.engine import create_engine
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker
from .SQLAlchemyContext import SQLAlchemyContext


class SQLAlchemyEngine:
    def __init__(self):
        self.engine = None
        self.session = None
        self._db_uri = None

    def close(self):
        """
        Close all connection with database
        """

        self.session.flush()
        self.session.close()

    def init_app(self, db_uri: str, is_debug: bool = False):
        """
        Init database engine by uri
        :param db_uri: uri to database with login and password (if need)
        :param is_debug: need log all activities to console
        """

        self._db_uri = db_uri
        self.engine = create_engine(self._db_uri, echo=is_debug)
        sm = sessionmaker(bind=self.engine)
        self.session = scoped_session(sm)

    def get_context(self):
        """
        Create session for connection
        :return: session
        """
        return SQLAlchemyContext(self)
