from typing import Self

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession, create_async_engine


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class Database:
    """
    SQL Database representation.

    Used to create sessions for managing database.

    Attributes:
        engine: Database engine.
        session_maker: Session maker for creating database sessions.
    """

    engine: AsyncEngine
    """
    Database engine.
    """

    session_maker: async_sessionmaker[AsyncSession]
    """
    Session maker for creating database sessions.
    """

    @classmethod
    def from_dsn(
            cls,
            dsn: str
    ) -> Self:
        """
        Create database instance from DSN string.

        :param dsn: Database DSN string.
        :return: Database instance.
        """

        engine = create_async_engine(
            dsn,
            pool_size=10,
            max_overflow=10,
            pool_recycle=60,
            pool_timeout=10
        )

        session_maker = async_sessionmaker(
            engine,
            expire_on_commit=False,
            autocommit=False,
        )

        return cls(engine=engine, session_maker=session_maker)
