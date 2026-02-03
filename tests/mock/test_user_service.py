"""Mock tests for user service."""

from datetime import time

import pytest

from models.user import User
from services.user_service import UserService


class TestUserService:
    """Test user service operations."""

    @pytest.mark.asyncio
    async def test_get_or_create_user_creates_new(self, user_service: UserService):
        """Test creating a new user when user doesn't exist."""
        user, is_created = await user_service.get_or_create_user(
            telegram_id=12345,
            language_code="en",
            username="newuser",
            first_name="John",
            last_name="Doe",
            timezone="UTC",
        )

        assert is_created is True
        assert user.telegram_id == 12345
        assert user.username == "newuser"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.language_code == "en"
        assert user.timezone == "UTC"

    @pytest.mark.asyncio
    async def test_get_or_create_user_returns_existing(
        self, user_service: UserService, test_user: User
    ):
        """Test getting existing user."""
        user, is_created = await user_service.get_or_create_user(
            telegram_id=test_user.telegram_id,
            language_code="en",
            username="different_username",
        )

        assert is_created is False
        assert user.id == test_user.id
        assert user.telegram_id == test_user.telegram_id

    @pytest.mark.asyncio
    async def test_get_or_create_user_language_fallback(self, user_service: UserService):
        """Test language fallback to 'en' for unsupported languages."""
        user, is_created = await user_service.get_or_create_user(
            telegram_id=99999,
            language_code="fr",  # Unsupported language
            username="frenchuser",
        )

        assert is_created is True
        assert user.language_code == "en"  # Should fallback to 'en'

    @pytest.mark.asyncio
    async def test_get_or_create_user_supported_languages(self, user_service: UserService):
        """Test that supported languages are preserved."""
        lang_ids = {"en": 10001, "ru": 10002, "et": 10003}
        for lang in ["en", "ru", "et"]:
            user, is_created = await user_service.get_or_create_user(
                telegram_id=lang_ids[lang],
                language_code=lang,
                username=f"user_{lang}",
            )
            assert user.language_code == lang

    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id_found(
        self, user_service: UserService, test_user: User
    ):
        """Test retrieving user by telegram_id."""
        user = await user_service.get_user_by_telegram_id(test_user.telegram_id)

        assert user is not None
        assert user.id == test_user.id
        assert user.telegram_id == test_user.telegram_id

    @pytest.mark.asyncio
    async def test_get_user_by_telegram_id_not_found(self, user_service: UserService):
        """Test that non-existent user returns None."""
        user = await user_service.get_user_by_telegram_id(999999999)
        assert user is None

    @pytest.mark.asyncio
    async def test_update_language_valid(self, user_service: UserService, test_user: User):
        """Test updating user language with valid code."""
        updated_user = await user_service.update_language(test_user, "ru")

        assert updated_user.language_code == "ru"
        assert updated_user.id == test_user.id

    @pytest.mark.asyncio
    async def test_update_language_invalid(self, user_service: UserService, test_user: User):
        """Test that invalid language code raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported language: fr"):
            await user_service.update_language(test_user, "fr")

    @pytest.mark.asyncio
    async def test_update_timezone(self, user_service: UserService, test_user: User):
        """Test updating user timezone."""
        updated_user = await user_service.update_timezone(test_user, "Europe/Tallinn")

        assert updated_user.timezone == "Europe/Tallinn"
        assert updated_user.id == test_user.id

    @pytest.mark.asyncio
    async def test_complete_onboarding_without_goals(
        self, user_service: UserService, test_user: User
    ):
        """Test completing onboarding without sleep goals."""
        updated_user = await user_service.complete_onboarding(test_user)

        assert updated_user.is_onboarded is True

    @pytest.mark.asyncio
    async def test_complete_onboarding_with_goals(
        self, user_service: UserService, test_user: User
    ):
        """Test completing onboarding with sleep goals."""
        bedtime = time(22, 0)
        wake_time = time(6, 0)
        sleep_hours = 8

        updated_user = await user_service.complete_onboarding(
            test_user,
            target_bedtime=bedtime,
            target_wake_time=wake_time,
            target_sleep_hours=sleep_hours,
        )

        assert updated_user.is_onboarded is True
        assert updated_user.target_bedtime == bedtime
        assert updated_user.target_wake_time == wake_time
        assert updated_user.target_sleep_hours == sleep_hours

    @pytest.mark.asyncio
    async def test_complete_onboarding_invalid_sleep_hours_low(
        self, user_service: UserService, test_user: User
    ):
        """Test that sleep hours < 1 raises ValueError."""
        with pytest.raises(ValueError, match="Target sleep hours must be between 1 and 24"):
            await user_service.complete_onboarding(test_user, target_sleep_hours=0)

    @pytest.mark.asyncio
    async def test_complete_onboarding_invalid_sleep_hours_high(
        self, user_service: UserService, test_user: User
    ):
        """Test that sleep hours > 24 raises ValueError."""
        with pytest.raises(ValueError, match="Target sleep hours must be between 1 and 24"):
            await user_service.complete_onboarding(test_user, target_sleep_hours=25)

    @pytest.mark.asyncio
    async def test_update_sleep_goals(self, user_service: UserService, test_user: User):
        """Test updating sleep goals."""
        new_bedtime = time(23, 30)
        new_wake_time = time(7, 30)
        new_hours = 7

        updated_user = await user_service.update_sleep_goals(
            test_user,
            target_bedtime=new_bedtime,
            target_wake_time=new_wake_time,
            target_sleep_hours=new_hours,
        )

        assert updated_user.target_bedtime == new_bedtime
        assert updated_user.target_wake_time == new_wake_time
        assert updated_user.target_sleep_hours == new_hours

    @pytest.mark.asyncio
    async def test_update_sleep_goals_invalid_hours(
        self, user_service: UserService, test_user: User
    ):
        """Test that invalid sleep hours raises ValueError."""
        with pytest.raises(ValueError):
            await user_service.update_sleep_goals(test_user, target_sleep_hours=30)

    @pytest.mark.asyncio
    async def test_is_onboarded_true(self, user_service: UserService, test_user: User):
        """Test is_onboarded returns True for onboarded user."""
        # Complete onboarding first
        await user_service.complete_onboarding(test_user)

        assert user_service.is_onboarded(test_user) is True

    @pytest.mark.asyncio
    async def test_is_onboarded_false(self, user_service: UserService, test_user: User):
        """Test is_onboarded returns False for non-onboarded user."""
        # test_user is not onboarded by default
        assert user_service.is_onboarded(test_user) is False

    @pytest.mark.asyncio
    async def test_has_sleep_goals_true(self, user_service: UserService, test_user: User):
        """Test has_sleep_goals returns True when goals are set."""
        await user_service.update_sleep_goals(test_user, target_sleep_hours=8)

        assert user_service.has_sleep_goals(test_user) is True

    @pytest.mark.asyncio
    async def test_has_sleep_goals_false(self, user_service: UserService, test_user: User):
        """Test has_sleep_goals returns False when goals are not set."""
        # test_user has target_sleep_hours=8 by default from fixture
        # Create a user without sleep goals
        user, _ = await user_service.get_or_create_user(telegram_id=88888, username="nogoals")
        assert user_service.has_sleep_goals(user) is False
