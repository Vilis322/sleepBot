from datetime import time
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User model with user-specific operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize user repository.

        Args:
            session: Async database session
        """
        super().__init__(User, session)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User if found, None otherwise
        """
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        telegram_id: int,
        language_code: str = "en",
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        timezone: str = "UTC",
    ) -> User:
        """Create a new user.

        Args:
            telegram_id: Telegram user ID
            language_code: User's preferred language
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
            timezone: User's timezone

        Returns:
            Created user
        """
        user = await self.create(
            telegram_id=telegram_id,
            language_code=language_code,
            username=username,
            first_name=first_name,
            last_name=last_name,
            timezone=timezone,
            is_onboarded=False,
        )
        return user

    async def get_or_create_user(
        self,
        telegram_id: int,
        language_code: str = "en",
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        timezone: str = "UTC",
    ) -> tuple[User, bool]:
        """Get existing user or create new one.

        Args:
            telegram_id: Telegram user ID
            language_code: User's preferred language
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
            timezone: User's timezone

        Returns:
            Tuple of (User, is_created)
        """
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user, False

        user = await self.create_user(
            telegram_id=telegram_id,
            language_code=language_code,
            username=username,
            first_name=first_name,
            last_name=last_name,
            timezone=timezone,
        )
        return user, True

    async def update_language(self, user: User, language_code: str) -> User:
        """Update user's language preference.

        Args:
            user: User to update
            language_code: New language code

        Returns:
            Updated user
        """
        user = await self.update(user, language_code=language_code)
        return user

    async def update_timezone(self, user: User, timezone: str) -> User:
        """Update user's timezone.

        Args:
            user: User to update
            timezone: New timezone

        Returns:
            Updated user
        """
        user = await self.update(user, timezone=timezone)
        return user

    async def complete_onboarding(
        self,
        user: User,
        target_bedtime: Optional[time] = None,
        target_wake_time: Optional[time] = None,
        target_sleep_hours: Optional[int] = None,
    ) -> User:
        """Mark user as onboarded and set sleep goals.

        Args:
            user: User to update
            target_bedtime: Target bedtime
            target_wake_time: Target wake time
            target_sleep_hours: Target sleep hours

        Returns:
            Updated user
        """
        user = await self.update(
            user,
            is_onboarded=True,
            target_bedtime=target_bedtime,
            target_wake_time=target_wake_time,
            target_sleep_hours=target_sleep_hours,
        )
        return user

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
        """
        updates = {}
        if target_bedtime is not None:
            updates["target_bedtime"] = target_bedtime
        if target_wake_time is not None:
            updates["target_wake_time"] = target_wake_time
        if target_sleep_hours is not None:
            updates["target_sleep_hours"] = target_sleep_hours

        user = await self.update(user, **updates)
        return user
