from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Disable SQL query logging (too verbose)
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session.

    Yields:
        AsyncSession: Database session

    Example:
        >>> async for session in get_session():
        ...     result = await session.execute(select(User))
        ...     break  # Important: must break or return before end of block
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error("database_session_error", error=str(e))
            raise
        finally:
            await session.close()


async def get_db_session() -> AsyncSession:
    """Get database session for use in middleware and handlers that need early return.

    Returns:
        AsyncSession: Database session that must be manually closed

    Example:
        >>> session = await get_db_session()
        >>> try:
        ...     result = await session.execute(select(User))
        ...     await session.commit()
        ... except Exception:
        ...     await session.rollback()
        ...     raise
        ... finally:
        ...     await session.close()
    """
    return async_session_maker()


async def init_database() -> None:
    """Initialize database tables (for testing purposes only).

    In production, use Alembic migrations instead.
    """
    from models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("database_initialized", message="All tables created")


async def close_database() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("database_closed", message="Database connections closed")
