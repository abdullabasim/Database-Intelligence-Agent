from typing import AsyncGenerator, Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models in the application.
    All models should inherit from this class to be included in migrations.
    """
    pass


# Primary asynchronous engine for the main admin database
async_engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

# Factory for creating new asynchronous sessions
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Internal cache for sync engine used by inspection tools
_sync_engine: Engine | None = None


def get_sync_engine() -> Engine:
    """
    Lazily initializes and returns the synchronous engine for the main database.
    Useful for schema inspection and management tasks.
    """
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(
            settings.sync_database_url,
            echo=False,
            pool_size=5,
        )
    return _sync_engine

# Caches for tenant-specific database connections to optimize resource usage
_dynamic_async_engines: dict[str, Any] = {}
_dynamic_sync_engines: dict[str, Any] = {}


def get_dynamic_async_engine(db_url: str):
    """
    Provides a cached asynchronous engine for a specific tenant database URL.
    This allows the agent to query external data sources efficiently.
    """
    if db_url not in _dynamic_async_engines:
        _dynamic_async_engines[db_url] = create_async_engine(
            db_url, echo=False, pool_size=5, max_overflow=10
        )
    return _dynamic_async_engines[db_url]


def get_dynamic_sync_engine(db_url: str):
    """
    Provides a cached synchronous engine for schema introspection of a tenant database.
    Used during the MDL generation process to read table structures.
    """
    if db_url not in _dynamic_sync_engines:
        _dynamic_sync_engines[db_url] = create_engine(
            db_url, echo=False, pool_size=2
        )
    return _dynamic_sync_engines[db_url]


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    A dependency function used in FastAPI routes to provide a scoped database session.
    Ensures that the session is properly closed after each request.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
