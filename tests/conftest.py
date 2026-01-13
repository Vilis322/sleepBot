"""Shared test fixtures for all test types."""

from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
import pytz
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from models import Base
from localization import LocalizationService
from models.sleep_session import SleepSession
from models.user import User
from repositories.sleep_repository import SleepRepository
from repositories.user_repository import UserRepository
from services.sleep_service import SleepService
from services.user_service import UserService

# Initialize faker for generating test data
fake = Faker()


@pytest.fixture
async def async_engine():
    """Create an async SQLite in-memory database engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def async_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an async database session for testing."""
    async_session_maker = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def user_repository(async_session: AsyncSession) -> UserRepository:
    """Create a user repository instance."""
    return UserRepository(async_session)


@pytest.fixture
async def sleep_repository(async_session: AsyncSession) -> SleepRepository:
    """Create a sleep repository instance."""
    return SleepRepository(async_session)


@pytest.fixture
async def user_service(async_session: AsyncSession) -> UserService:
    """Create a user service instance."""
    return UserService(async_session)


@pytest.fixture
async def sleep_service(async_session: AsyncSession) -> SleepService:
    """Create a sleep service instance."""
    return SleepService(async_session)


@pytest.fixture
async def test_user(async_session: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        telegram_id=fake.random_int(min=100000, max=999999),
        username=fake.user_name(),
        language="en",
        timezone="UTC",
        target_sleep_hours=8.0,
        target_bedtime=datetime.now().replace(hour=22, minute=0, second=0, microsecond=0).time(),
        target_wake_time=datetime.now().replace(hour=6, minute=0, second=0, microsecond=0).time(),
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture
async def test_user_with_sessions(async_session: AsyncSession, test_user: User) -> User:
    """Create a test user with multiple sleep sessions."""
    now = datetime.now(pytz.UTC)

    # Session 1: Old completed session (30 hours ago)
    old_session = SleepSession(
        user_id=test_user.id,
        sleep_start=now - timedelta(hours=38),
        sleep_end=now - timedelta(hours=30),
        duration_hours=8.0,
        quality_rating=7.5,
        note="Old session note",
    )
    async_session.add(old_session)

    # Session 2: Recent completed session (2 hours ago)
    recent_session = SleepSession(
        user_id=test_user.id,
        sleep_start=now - timedelta(hours=10),
        sleep_end=now - timedelta(hours=2),
        duration_hours=8.0,
        quality_rating=None,
        note=None,
    )
    async_session.add(recent_session)

    # Session 3: Active session (no sleep_end)
    active_session = SleepSession(
        user_id=test_user.id,
        sleep_start=now - timedelta(hours=1),
        sleep_end=None,
        duration_hours=None,
    )
    async_session.add(active_session)

    await async_session.commit()
    await async_session.refresh(test_user)
    return test_user


@pytest.fixture
async def completed_session_old(async_session: AsyncSession, test_user: User) -> SleepSession:
    """Create a completed session older than 24 hours."""
    now = datetime.now(pytz.UTC)
    session = SleepSession(
        user_id=test_user.id,
        sleep_start=now - timedelta(hours=32),
        sleep_end=now - timedelta(hours=25),
        duration_hours=7.0,
        quality_rating=8.0,
        note="Test note",
    )
    async_session.add(session)
    await async_session.commit()
    await async_session.refresh(session)
    return session


@pytest.fixture
async def completed_session_recent(async_session: AsyncSession, test_user: User) -> SleepSession:
    """Create a recently completed session (< 24 hours)."""
    now = datetime.now(pytz.UTC)
    session = SleepSession(
        user_id=test_user.id,
        sleep_start=now - timedelta(hours=10),
        sleep_end=now - timedelta(hours=2),
        duration_hours=8.0,
        quality_rating=None,
        note=None,
    )
    async_session.add(session)
    await async_session.commit()
    await async_session.refresh(session)
    return session


@pytest.fixture
async def completed_session_with_rating(
    async_session: AsyncSession, test_user: User
) -> SleepSession:
    """Create a completed session with existing quality rating."""
    now = datetime.now(pytz.UTC)
    session = SleepSession(
        user_id=test_user.id,
        sleep_start=now - timedelta(hours=10),
        sleep_end=now - timedelta(hours=2),
        duration_hours=8.0,
        quality_rating=7.5,
        note=None,
    )
    async_session.add(session)
    await async_session.commit()
    await async_session.refresh(session)
    return session


@pytest.fixture
async def completed_session_with_note(
    async_session: AsyncSession, test_user: User
) -> SleepSession:
    """Create a completed session with existing note."""
    now = datetime.now(pytz.UTC)
    session = SleepSession(
        user_id=test_user.id,
        sleep_start=now - timedelta(hours=10),
        sleep_end=now - timedelta(hours=2),
        duration_hours=8.0,
        quality_rating=None,
        note="Existing test note",
    )
    async_session.add(session)
    await async_session.commit()
    await async_session.refresh(session)
    return session


@pytest.fixture
def localization_service() -> LocalizationService:
    """Create a localization service instance."""
    return LocalizationService()


@pytest.fixture
def malicious_sql_payloads() -> list[str]:
    """Common SQL injection attack payloads for testing."""
    return [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "' OR 1=1--",
        "' UNION SELECT NULL, NULL, NULL--",
        "1; DELETE FROM sleep_sessions WHERE 1=1--",
        "' OR 'x'='x",
        "1' AND '1'='1",
        "<script>alert('XSS')</script>",
        "'; EXEC xp_cmdshell('dir'); --",
    ]
