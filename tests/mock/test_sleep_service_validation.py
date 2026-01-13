"""Mock tests for sleep service validation logic with time windows."""

from datetime import datetime, timedelta

import pytest
import pytz

from models.sleep_session import SleepSession
from models.user import User
from services.sleep_service import SessionUpdateValidation, SleepService


class TestSleepServiceValidation:
    """Test sleep service validation methods."""

    @pytest.mark.asyncio
    async def test_validate_session_update_allow_first_rating(
        self, sleep_service: SleepService, completed_session_recent: SleepSession
    ):
        """Test that first rating on fresh session is allowed without confirmation."""
        validation, hours_since_wake = sleep_service.validate_session_update(
            completed_session_recent, "quality", has_existing_data=False
        )

        assert validation == SessionUpdateValidation.ALLOW
        assert hours_since_wake < 24

    @pytest.mark.asyncio
    async def test_validate_session_update_allow_first_note(
        self, sleep_service: SleepService, completed_session_recent: SleepSession
    ):
        """Test that first note on fresh session is allowed without confirmation."""
        validation, hours_since_wake = sleep_service.validate_session_update(
            completed_session_recent, "note", has_existing_data=False
        )

        assert validation == SessionUpdateValidation.ALLOW
        assert hours_since_wake < 24

    @pytest.mark.asyncio
    async def test_validate_session_update_ask_confirmation_fresh_with_rating(
        self, sleep_service: SleepService, completed_session_with_rating: SleepSession
    ):
        """Test that updating rating on fresh session asks for confirmation."""
        validation, hours_since_wake = sleep_service.validate_session_update(
            completed_session_with_rating, "quality", has_existing_data=True
        )

        assert validation == SessionUpdateValidation.ASK_CONFIRMATION
        assert hours_since_wake < 24

    @pytest.mark.asyncio
    async def test_validate_session_update_ask_confirmation_fresh_with_note(
        self, sleep_service: SleepService, completed_session_with_note: SleepSession
    ):
        """Test that updating note on fresh session asks for confirmation."""
        validation, hours_since_wake = sleep_service.validate_session_update(
            completed_session_with_note, "note", has_existing_data=True
        )

        assert validation == SessionUpdateValidation.ASK_CONFIRMATION
        assert hours_since_wake < 24

    @pytest.mark.asyncio
    async def test_validate_session_update_show_warning_old_session(
        self, sleep_service: SleepService, completed_session_old: SleepSession
    ):
        """Test that old session (>= 24h) shows warning regardless of existing data."""
        # Test with no existing data
        validation, hours_since_wake = sleep_service.validate_session_update(
            completed_session_old, "quality", has_existing_data=False
        )

        assert validation == SessionUpdateValidation.SHOW_WARNING
        assert hours_since_wake >= 24

    @pytest.mark.asyncio
    async def test_validate_session_update_show_warning_old_session_with_data(
        self, sleep_service: SleepService, completed_session_old: SleepSession
    ):
        """Test that old session shows warning even with existing data."""
        validation, hours_since_wake = sleep_service.validate_session_update(
            completed_session_old, "quality", has_existing_data=True
        )

        assert validation == SessionUpdateValidation.SHOW_WARNING
        assert hours_since_wake >= 24

    @pytest.mark.asyncio
    async def test_add_quality_rating_valid_range(
        self, sleep_service: SleepService, completed_session_recent: SleepSession
    ):
        """Test adding valid quality rating (1.0-10.0)."""
        for rating in [1.0, 5.5, 10.0]:
            session = await sleep_service.add_quality_rating(completed_session_recent, rating)
            assert session.quality_rating == rating

    @pytest.mark.asyncio
    async def test_add_quality_rating_invalid_range_low(
        self, sleep_service: SleepService, completed_session_recent: SleepSession
    ):
        """Test that rating below 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="Quality rating must be between 1.0 and 10.0"):
            await sleep_service.add_quality_rating(completed_session_recent, 0.5)

    @pytest.mark.asyncio
    async def test_add_quality_rating_invalid_range_high(
        self, sleep_service: SleepService, completed_session_recent: SleepSession
    ):
        """Test that rating above 10.0 raises ValueError."""
        with pytest.raises(ValueError, match="Quality rating must be between 1.0 and 10.0"):
            await sleep_service.add_quality_rating(completed_session_recent, 10.5)

    @pytest.mark.asyncio
    async def test_add_quality_rating_to_active_session(
        self, sleep_service: SleepService, async_session, test_user: User
    ):
        """Test that adding rating to active session raises ValueError."""
        now = datetime.now(pytz.UTC)
        active_session = SleepSession(
            user_id=test_user.id,
            sleep_start=now - timedelta(hours=1),
            sleep_end=None,
            duration_hours=None,
        )
        async_session.add(active_session)
        await async_session.commit()
        await async_session.refresh(active_session)

        with pytest.raises(ValueError, match="Cannot rate an active sleep session"):
            await sleep_service.add_quality_rating(active_session, 8.0)

    @pytest.mark.asyncio
    async def test_add_note_valid(
        self, sleep_service: SleepService, completed_session_recent: SleepSession
    ):
        """Test adding valid note."""
        note_text = "Had a great sleep!"
        session = await sleep_service.add_note(completed_session_recent, note_text)
        assert session.note == note_text

    @pytest.mark.asyncio
    async def test_add_note_empty_raises_error(
        self, sleep_service: SleepService, completed_session_recent: SleepSession
    ):
        """Test that empty note raises ValueError."""
        with pytest.raises(ValueError, match="Note cannot be empty"):
            await sleep_service.add_note(completed_session_recent, "")

    @pytest.mark.asyncio
    async def test_add_note_whitespace_only_raises_error(
        self, sleep_service: SleepService, completed_session_recent: SleepSession
    ):
        """Test that whitespace-only note raises ValueError."""
        with pytest.raises(ValueError, match="Note cannot be empty"):
            await sleep_service.add_note(completed_session_recent, "   ")

    @pytest.mark.asyncio
    async def test_add_note_to_active_session(
        self, sleep_service: SleepService, async_session, test_user: User
    ):
        """Test that adding note to active session raises ValueError."""
        now = datetime.now(pytz.UTC)
        active_session = SleepSession(
            user_id=test_user.id,
            sleep_start=now - timedelta(hours=1),
            sleep_end=None,
            duration_hours=None,
        )
        async_session.add(active_session)
        await async_session.commit()
        await async_session.refresh(active_session)

        with pytest.raises(ValueError, match="Cannot add note to an active sleep session"):
            await sleep_service.add_note(active_session, "Test note")

    @pytest.mark.asyncio
    async def test_format_time_ago_minutes(self, sleep_service: SleepService):
        """Test formatting time ago for minutes."""
        hours = 0.5  # 30 minutes
        result = sleep_service.format_time_ago(hours)
        assert "30 minutes ago" in result

    @pytest.mark.asyncio
    async def test_format_time_ago_hours(self, sleep_service: SleepService):
        """Test formatting time ago for hours."""
        hours = 5.7
        result = sleep_service.format_time_ago(hours)
        assert "5 hours ago" in result

    @pytest.mark.asyncio
    async def test_format_time_ago_days(self, sleep_service: SleepService):
        """Test formatting time ago for days."""
        hours = 48.5  # 2 days
        result = sleep_service.format_time_ago(hours)
        assert "2 days ago" in result

    @pytest.mark.asyncio
    async def test_get_last_completed_session_returns_most_recent(
        self, sleep_service: SleepService, test_user_with_sessions: User, async_session
    ):
        """Test that get_last_completed_session returns the most recent completed session."""
        last_session = await sleep_service.get_last_completed_session(test_user_with_sessions)

        assert last_session is not None
        assert last_session.sleep_end is not None

        # Verify it's the most recent completed session (not the active one)
        all_sessions = await async_session.execute(
            "SELECT * FROM sleep_sessions WHERE user_id = ? AND sleep_end IS NOT NULL ORDER BY sleep_end DESC",
            (test_user_with_sessions.id,),
        )
        # The returned session should be the most recent completed one

    @pytest.mark.asyncio
    async def test_get_last_completed_session_no_sessions(
        self, sleep_service: SleepService, test_user: User
    ):
        """Test that get_last_completed_session returns None when user has no sessions."""
        last_session = await sleep_service.get_last_completed_session(test_user)
        assert last_session is None

    @pytest.mark.asyncio
    async def test_note_trimming(
        self, sleep_service: SleepService, completed_session_recent: SleepSession
    ):
        """Test that notes are trimmed of leading/trailing whitespace."""
        note_with_whitespace = "  Test note with spaces  "
        session = await sleep_service.add_note(completed_session_recent, note_with_whitespace)
        assert session.note == "Test note with spaces"

    @pytest.mark.asyncio
    async def test_overwrite_existing_rating(
        self, sleep_service: SleepService, completed_session_with_rating: SleepSession
    ):
        """Test that existing rating can be overwritten."""
        original_rating = completed_session_with_rating.quality_rating
        assert original_rating == 7.5

        new_rating = 9.0
        session = await sleep_service.add_quality_rating(completed_session_with_rating, new_rating)
        assert session.quality_rating == new_rating
        assert session.quality_rating != original_rating

    @pytest.mark.asyncio
    async def test_overwrite_existing_note(
        self, sleep_service: SleepService, completed_session_with_note: SleepSession
    ):
        """Test that existing note can be overwritten."""
        original_note = completed_session_with_note.note
        assert original_note == "Existing test note"

        new_note = "Updated test note"
        session = await sleep_service.add_note(completed_session_with_note, new_note)
        assert session.note == new_note
        assert session.note != original_note
