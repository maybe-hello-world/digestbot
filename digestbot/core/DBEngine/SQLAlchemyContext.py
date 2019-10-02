from sqlalchemy.orm.session import Session


class SQLAlchemyContext(object):
    def __init__(self, engine):
        """
        Create session
        :param engine: wrapper for sqlalchemy SQLAlchemyEngine
        """

        self._db = engine.session()

    @property
    def db(self) -> Session:
        return self._db

    def commit(self, exception: bool = False):
        """
        Commit all changes to database if no any exceptions
        :param exception: did any exceptions or not
        """

        if exception:
            self.db.rollback()
            return

        self.db.commit()
