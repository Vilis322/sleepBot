from datetime import time
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.user_repository import UserRepository


class UserService:
    """Service layer for user-related business logic.

    Implements user management operations following the Service pattern.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize user service.

        Args:
            session: Async database session
        """
        self.repository = UserRepository(session)

    async def get_or_create_user(
        self,
        telegram_id: int,
        language_code: Optional[str] = None,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        timezone: str = "UTC",
    ) -> tuple[User, bool]:
        """Get existing user or create new one.

        Args:
            telegram_id: Telegram user ID
            language_code: User's language from Telegram (optional)
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
            timezone: User's timezone

        Returns:
            Tuple of (User, is_created)
        """
        # Determine language: use provided or default to 'en'
        lang = language_code if language_code in ["en", "ru", "et"] else "en"

        user, is_created = await self.repository.get_or_create_user(
            telegram_id=telegram_id,
            language_code=lang,
            username=username,
            first_name=first_name,
            last_name=last_name,
            timezone=timezone,
        )

        return user, is_created

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User if found, None otherwise
        """
        return await self.repository.get_by_telegram_id(telegram_id)

    async def update_language(self, user: User, language_code: str) -> User:
        """Update user's language preference.

        Args:
            user: User to update
            language_code: New language code (en, ru, et)

        Returns:
            Updated user

        Raises:
            ValueError: If language code is not supported
        """
        if language_code not in ["en", "ru", "et"]:
            raise ValueError(f"Unsupported language: {language_code}")

        return await self.repository.update_language(user, language_code)

    async def update_timezone(self, user: User, timezone: str) -> User:
        """Update user's timezone.

        Args:
            user: User to update
            timezone: New timezone (e.g., 'Europe/Tallinn')

        Returns:
            Updated user
        """
        return await self.repository.update_timezone(user, timezone)

    async def complete_onboarding(
        self,
        user: User,
        target_bedtime: Optional[time] = None,
        target_wake_time: Optional[time] = None,
        target_sleep_hours: Optional[int] = None,
    ) -> User:
        """Complete user onboarding and set sleep goals.

        Args:
            user: User to update
            target_bedtime: Target bedtime
            target_wake_time: Target wake time
            target_sleep_hours: Target sleep hours

        Returns:
            Updated user

        Raises:
            ValueError: If target_sleep_hours is invalid
        """
        if target_sleep_hours is not None and (target_sleep_hours < 1 or target_sleep_hours > 24):
            raise ValueError("Target sleep hours must be between 1 and 24")

        return await self.repository.complete_onboarding(
            user,
            target_bedtime=target_bedtime,
            target_wake_time=target_wake_time,
            target_sleep_hours=target_sleep_hours,
        )

    async def update_sleep_goals(
        self,
        user: User,
        target_bedtime: Optional[time] = None,
        target_wake_time: Optional[time] = None,
        target_sleep_hours: Optional[int] = None,
    ) -> User:
        """Update user's sleep goals.

        Args:
            user: User to update
            target_bedtime: Target bedtime
            target_wake_time: Target wake time
            target_sleep_hours: Target sleep hours

        Returns:
            Updated user

        Raises:
            ValueError: If target_sleep_hours is invalid
        """
        if target_sleep_hours is not None and (target_sleep_hours < 1 or target_sleep_hours > 24):
            raise ValueError("Target sleep hours must be between 1 and 24")

        return await self.repository.update_sleep_goals(
            user,
            target_bedtime=target_bedtime,
            target_wake_time=target_wake_time,
            target_sleep_hours=target_sleep_hours,
        )

    def is_onboarded(self, user: User) -> bool:
        """Check if user has completed onboarding.

        Args:
            user: User to check

        Returns:
            True if user is onboarded
        """
        return user.is_onboarded

    def has_sleep_goals(self, user: User) -> bool:
        """Check if user has set sleep goals.

        Args:
            user: User to check

        Returns:
            True if user has set sleep goals
        """
        return user.target_sleep_hours is not None
