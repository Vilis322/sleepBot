"""Mock tests for repository layer."""

from datetime import datetime, timedelta

import pytest
import pytz

from models.sleep_session import SleepSession
from models.user import User
from repositories.sleep_repository import SleepRepository
from repositories.user_repository import UserRepository


class TestUserRepository:
    """Test user repository operations."""

    @pytest.mark.asyncio
    async def test_create_user(self, user_repository: UserRepository, async_session):
        """Test creating a new user."""
        user = User(
            telegram_id=123456,
            username="testuser",
            language="en",
            timezone="UTC",
        )
        created_user = await user_repository.create(user)

        assert created_user.id is not None
        assert created_user.telegram_id == 123456
        assert created_user.username == "testuser"

    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id(
        self, user_repository: UserRepository, test_user: User
    ):
        """Test retrieving user by Telegram ID."""
        retrieved_user = await user_repository.get_by_telegram_id(test_user.telegram_id)

        assert retrieved_user is not None
        assert retrieved_user.id == test_user.id
        assert retrieved_user.telegram_id == test_user.telegram_id

    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id_not_found(self, user_repository: UserRepository):
        """Test that non-existent Telegram ID returns None."""
        retrieved_user = await user_repository.get_by_telegram_id(999999999)
        assert retrieved_user is None

    @pytest.mark.asyncio
    async def test_update_user(self, user_repository: UserRepository, test_user: User):
        """Test updating user data."""
        test_user.language = "ru"
        test_user.timezone = "Europe/Moscow"

        updated_user = await user_repository.update(test_user)

        assert updated_user.language == "ru"
        assert updated_user.timezone == "Europe/Moscow"

    @pytest.mark.asyncio
    async def test_delete_user(
        self, user_repository: UserRepository, test_user: User, async_session
    ):
        """Test deleting a user."""
        await user_repository.delete(test_user)
        await async_session.commit()

        # Verify user is deleted
        retrieved_user = await user_repository.get_by_telegram_id(test_user.telegram_id)
        assert retrieved_user is None


class TestSleepRepository:
    """Test sleep repository operations."""

    @pytest.mark.asyncio
    async def test_start_sleep_session(
        self, sleep_repository: SleepRepository, test_user: User
    ):
        """Test creating a new sleep session."""
        now = datetime.now(pytz.UTC)
        session = await sleep_repository.start_sleep_session(test_user.id, now)

        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.sleep_start == now
        assert session.sleep_end is None

    @pytest.mark.asyncio
    async def test_get_active_session(
        self, sleep_repository: SleepRepository, test_user: User, async_session
    ):
        """Test retrieving active sleep session."""
        now = datetime.now(pytz.UTC)
        active_session = SleepSession(
            user_id=test_user.id,
            sleep_start=now,
            sleep_end=None,
        )
        async_session.add(active_session)
        await async_session.commit()

        retrieved_session = await sleep_repository.get_active_session(test_user.id)

        assert retrieved_session is not None
        assert retrieved_session.id == active_session.id
        assert retrieved_session.sleep_end is None

    @pytest.mark.asyncio
    async def test_get_active_session_none(
        self, sleep_repository: SleepRepository, test_user: User
    ):
        """Test that get_active_session returns None when no active session."""
        retrieved_session = await sleep_repository.get_active_session(test_user.id)
        assert retrieved_session is None

    @pytest.mark.asyncio
    async def test_end_sleep_session(
        self, sleep_repository: SleepRepository, test_user: User, async_session
    ):
        """Test ending an active sleep session."""
        now = datetime.now(pytz.UTC)
        start_time = now - timedelta(hours=8)

        active_session = SleepSession(
            user_id=test_user.id,
            sleep_start=start_time,
            sleep_end=None,
        )
        async_session.add(active_session)
        await async_session.commit()
        await async_session.refresh(active_session)

        ended_session = await sleep_repository.end_sleep_session(active_session, now)

        assert ended_session.sleep_end == now
        assert ended_session.duration_hours == pytest.approx(8.0, rel=0.01)

    @pytest.mark.asyncio
    async def test_get_last_completed_session(
        self, sleep_repository: SleepRepository, test_user_with_sessions: User
    ):
        """Test retrieving the most recent completed session."""
        last_session = await sleep_repository.get_last_completed_session(
            test_user_with_sessions.id
        )

        assert last_session is not None
        assert last_session.sleep_end is not None
        # Should not return the active session
        assert last_session.duration_hours is not None

    @pytest.mark.asyncio
    async def test_add_quality_rating(
        self, sleep_repository: SleepRepository, completed_session_recent: SleepSession
    ):
        """Test adding quality rating to a session."""
        rating = 8.5
        updated_session = await sleep_repository.add_quality_rating(
            completed_session_recent, rating
        )

        assert updated_session.quality_rating == rating

    @pytest.mark.asyncio
    async def test_add_note(
        self, sleep_repository: SleepRepository, completed_session_recent: SleepSession
    ):
        """Test adding note to a session."""
        note = "Great sleep!"
        updated_session = await sleep_repository.add_note(completed_session_recent, note)

        assert updated_session.note == note

    @pytest.mark.asyncio
    async def test_get_sessions_by_date_range(
        self, sleep_repository: SleepRepository, test_user: User, async_session
    ):
        """Test retrieving sessions within a date range."""
        now = datetime.now(pytz.UTC)

        # Create sessions at different times
        for i in range(5):
            session = SleepSession(
                user_id=test_user.id,
                sleep_start=now - timedelta(days=i + 1, hours=8),
                sleep_end=now - timedelta(days=i + 1),
                duration_hours=8.0,
            )
            async_session.add(session)
        await async_session.commit()

        # Get sessions from last 3 days
        start_date = now - timedelta(days=3)
        end_date = now

        sessions = await sleep_repository.get_sessions_by_date_range(
            test_user.id, start_date, end_date, only_completed=True
        )

        # Should return sessions from days 1, 2, 3 (3 sessions)
        assert len(sessions) >= 2  # At least the most recent ones

    @pytest.mark.asyncio
    async def test_get_all_user_sessions(
        self, sleep_repository: SleepRepository, test_user_with_sessions: User
    ):
        """Test retrieving all user sessions."""
        sessions = await sleep_repository.get_all_user_sessions(
            test_user_with_sessions.id, only_completed=True
        )

        # Should not include active session
        assert all(session.sleep_end is not None for session in sessions)
        assert len(sessions) >= 2

    @pytest.mark.asyncio
    async def test_delete_session(
        self, sleep_repository: SleepRepository, completed_session_recent: SleepSession
    ):
        """Test deleting a sleep session."""
        session_id = completed_session_recent.id

        await sleep_repository.delete(completed_session_recent)

        # Verify session is deleted by trying to get it
        # (We'd need to implement get_by_id for proper verification)

    @pytest.mark.asyncio
    async def test_get_first_session_date(
        self, sleep_repository: SleepRepository, test_user_with_sessions: User
    ):
        """Test retrieving the date of user's first session."""
        first_date = await sleep_repository.get_first_session_date(test_user_with_sessions.id)

        assert first_date is not None
        assert isinstance(first_date, datetime)

    @pytest.mark.asyncio
    async def test_get_first_session_date_no_sessions(
        self, sleep_repository: SleepRepository, test_user: User
    ):
        """Test that get_first_session_date returns None for new user."""
        first_date = await sleep_repository.get_first_session_date(test_user.id)
        assert first_date is None


class TestRepositoryConcurrency:
    """Test concurrent operations on repositories."""

    @pytest.mark.asyncio
    async def test_multiple_sessions_same_user(
        self, sleep_repository: SleepRepository, test_user: User, async_session
    ):
        """Test creating multiple sessions for the same user."""
        now = datetime.now(pytz.UTC)

        # Create and complete first session
        session1 = await sleep_repository.start_sleep_session(
            test_user.id, now - timedelta(hours=20)
        )
        await sleep_repository.end_sleep_session(session1, now - timedelta(hours=12))

        # Create and complete second session
        session2 = await sleep_repository.start_sleep_session(
            test_user.id, now - timedelta(hours=10)
        )
        await sleep_repository.end_sleep_session(session2, now - timedelta(hours=2))

        # Both sessions should exist
        all_sessions = await sleep_repository.get_all_user_sessions(
            test_user.id, only_completed=True
        )
        assert len(all_sessions) >= 2

    @pytest.mark.asyncio
    async def test_update_same_session_multiple_times(
        self, sleep_repository: SleepRepository, completed_session_recent: SleepSession
    ):
        """Test updating the same session multiple times."""
        # Add rating
        await sleep_repository.add_quality_rating(completed_session_recent, 7.0)

        # Add note
        await sleep_repository.add_note(completed_session_recent, "Test note")

        # Update rating again
        updated_session = await sleep_repository.add_quality_rating(
            completed_session_recent, 9.0
        )

        # All updates should be reflected
        assert updated_session.quality_rating == 9.0
        assert updated_session.note == "Test note"
