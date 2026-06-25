from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import func

from app.config import settings

_engine_kwargs = {"echo": False}
if settings.database_url.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
    _is_sqlite = True
else:
    _engine_kwargs["connect_args"] = {"charset": "utf8mb4"}
    _is_sqlite = False

engine = create_async_engine(settings.database_url, **_engine_kwargs)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


def random_func():
    """Return the database-appropriate random() function."""
    return func.random() if _is_sqlite else func.rand()

