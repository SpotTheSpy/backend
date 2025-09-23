from pydantic import ConfigDict
from pydantic.dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, AsyncSession, create_async_engine


@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class Database:
    engine: AsyncEngine
    session_maker: async_sessionmaker[AsyncSession]

    @classmethod
    def from_dsn(
            cls,
            dsn: str
    ) -> 'Database':
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
