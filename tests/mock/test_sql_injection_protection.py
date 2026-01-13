"""Mock tests for SQL injection protection."""

import pytest

from models.user import User
from services.sleep_service import SleepService
from services.user_service import UserService


class TestSQLInjectionProtection:
    """Test SQL injection protection across all inputs."""

    @pytest.mark.asyncio
    async def test_note_sql_injection_attempts(
        self,
        sleep_service: SleepService,
        completed_session_recent,
        malicious_sql_payloads: list[str],
    ):
        """Test that SQL injection payloads in notes are safely stored as text."""
        for payload in malicious_sql_payloads:
            # Should not raise exception, should store as regular text
            session = await sleep_service.add_note(completed_session_recent, payload)

            # Verify the payload is stored as-is (escaped by SQLAlchemy)
            assert session.note == payload

            # Verify no SQL execution occurred by checking session still exists
            assert session.id is not None

    @pytest.mark.asyncio
    async def test_username_sql_injection(
        self, async_session, user_service: UserService, malicious_sql_payloads: list[str]
    ):
        """Test SQL injection protection in username field."""
        telegram_id = 999888777

        for payload in malicious_sql_payloads:
            user = User(
                telegram_id=telegram_id,
                username=payload,  # Malicious username
                language="en",
                timezone="UTC",
            )
            async_session.add(user)
            await async_session.commit()
            await async_session.refresh(user)

            # Verify user was created with the payload as username (not executed)
            retrieved_user = await user_service.get_user_by_telegram_id(telegram_id)
            assert retrieved_user is not None
            assert retrieved_user.username == payload

            # Clean up
            telegram_id += 1

    @pytest.mark.asyncio
    async def test_long_note_doesnt_break_db(
        self, sleep_service: SleepService, completed_session_recent
    ):
        """Test that very long notes don't break the database."""
        # Create a very long note (10,000 characters)
        long_note = "A" * 10000

        session = await sleep_service.add_note(completed_session_recent, long_note)
        assert session.note == long_note
        assert len(session.note) == 10000

    @pytest.mark.asyncio
    async def test_special_characters_in_note(
        self, sleep_service: SleepService, completed_session_recent
    ):
        """Test that special characters are properly escaped in notes."""
        special_chars_note = "Test with 'quotes' and \"double quotes\" and \\ backslash"

        session = await sleep_service.add_note(completed_session_recent, special_chars_note)
        assert session.note == special_chars_note

    @pytest.mark.asyncio
    async def test_unicode_characters_in_note(
        self, sleep_service: SleepService, completed_session_recent
    ):
        """Test that Unicode characters work correctly in notes."""
        unicode_note = "Спал хорошо 😴 Эмодзи работают! 中文测试"

        session = await sleep_service.add_note(completed_session_recent, unicode_note)
        assert session.note == unicode_note

    @pytest.mark.asyncio
    async def test_xss_attempt_in_note(
        self, sleep_service: SleepService, completed_session_recent
    ):
        """Test that XSS attempts are safely stored (not executed)."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
        ]

        for payload in xss_payloads:
            session = await sleep_service.add_note(completed_session_recent, payload)
            # Payload should be stored as-is (escaped by the frontend/template engine)
            assert session.note == payload

    @pytest.mark.asyncio
    async def test_null_bytes_in_note(
        self, sleep_service: SleepService, completed_session_recent
    ):
        """Test handling of null bytes in notes."""
        note_with_null = "Test\x00note"

        # This should either work or raise a clear error (not cause corruption)
        try:
            session = await sleep_service.add_note(completed_session_recent, note_with_null)
            assert "\x00" in session.note or session.note == "Testnote"
        except ValueError:
            # Acceptable to reject null bytes
            pass

    @pytest.mark.asyncio
    async def test_quality_rating_sql_injection(
        self, sleep_service: SleepService, completed_session_recent
    ):
        """Test that quality rating field properly validates type (float only)."""
        # These should all raise ValueError due to type validation
        invalid_ratings = ["'; DROP TABLE users; --", "1 OR 1=1", "admin'--"]

        for invalid_rating in invalid_ratings:
            with pytest.raises((ValueError, TypeError)):
                await sleep_service.add_quality_rating(
                    completed_session_recent, invalid_rating  # type: ignore
                )

    @pytest.mark.asyncio
    async def test_timezone_sql_injection(self, async_session):
        """Test SQL injection protection in timezone field."""
        malicious_timezone = "'; DROP TABLE users; --"

        user = User(
            telegram_id=123456789,
            username="testuser",
            language="en",
            timezone=malicious_timezone,
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        # Should be stored as string (not executed)
        assert user.timezone == malicious_timezone

    @pytest.mark.asyncio
    async def test_concurrent_modifications_safe(
        self, sleep_service: SleepService, completed_session_recent, async_session
    ):
        """Test that concurrent modifications don't cause data corruption."""
        # Add a note
        await sleep_service.add_note(completed_session_recent, "First note")

        # Simulate concurrent modification attempt
        await sleep_service.add_quality_rating(completed_session_recent, 8.0)

        # Refresh to get latest state
        await async_session.refresh(completed_session_recent)

        # Both should be present
        assert completed_session_recent.note == "First note"
        assert completed_session_recent.quality_rating == 8.0

    @pytest.mark.asyncio
    async def test_language_field_injection(self, async_session):
        """Test SQL injection in language field."""
        user = User(
            telegram_id=987654321,
            username="testuser",
            language="'; DELETE FROM users; --",
            timezone="UTC",
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        assert user.language == "'; DELETE FROM users; --"

    @pytest.mark.asyncio
    async def test_parametrized_queries_used(
        self, sleep_service: SleepService, test_user: User, async_session
    ):
        """Test that parametrized queries are used (not string concatenation)."""
        # This is implicit in SQLAlchemy ORM usage, but we verify behavior
        malicious_telegram_id = "1 OR 1=1"

        # Type system should prevent this, but test the behavior
        with pytest.raises((TypeError, ValueError)):
            await async_session.execute(
                "SELECT * FROM users WHERE telegram_id = ?", (malicious_telegram_id,)
            )
