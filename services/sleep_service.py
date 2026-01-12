from datetime import datetime
from typing import Optional

import pytz
from sqlalchemy.ext.asyncio import AsyncSession

from models.sleep_session import SleepSession
from models.user import User
from repositories.sleep_repository import SleepRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class SleepService:
    """Service layer for sleep tracking business logic."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize sleep service.

        Args:
            session: Async database session
        """
        self.repository = SleepRepository(session)

    def _convert_to_utc(self, dt: datetime, timezone_str: str) -> datetime:
        """Convert datetime from user's timezone to UTC.

        Args:
            dt: Datetime in user's timezone
            timezone_str: Timezone string (e.g., 'Europe/Tallinn')

        Returns:
            Datetime in UTC
        """
        try:
            tz = pytz.timezone(timezone_str)
            if dt.tzinfo is None:
                dt = tz.localize(dt)
            return dt.astimezone(pytz.UTC)
        except Exception as e:
            logger.warning(
                "timezone_conversion_failed",
                timezone=timezone_str,
                error=str(e),
            )
            # Fallback to UTC
            return dt.replace(tzinfo=pytz.UTC) if dt.tzinfo is None else dt

    def _convert_from_utc(self, dt: datetime, timezone_str: str) -> datetime:
        """Convert datetime from UTC to user's timezone.

        Args:
            dt: Datetime in UTC
            timezone_str: Timezone string (e.g., 'Europe/Tallinn')

        Returns:
            Datetime in user's timezone
        """
        try:
            tz = pytz.timezone(timezone_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=pytz.UTC)
            return dt.astimezone(tz)
        except Exception as e:
            logger.warning(
                "timezone_conversion_failed",
                timezone=timezone_str,
                error=str(e),
            )
            return dt

    async def get_active_session(self, user: User) -> Optional[SleepSession]:
        """Get user's active sleep session.

        Args:
            user: User to check

        Returns:
            Active session if exists, None otherwise
        """
        return await self.repository.get_active_session(user.id)

    async def start_sleep_session(self, user: User) -> SleepSession:
        """Start a new sleep tracking session.

        Args:
            user: User starting sleep

        Returns:
            Created sleep session

        Raises:
            ValueError: If user already has an active session
        """
        # Check if there's already an active session
        active_session = await self.get_active_session(user)
        if active_session:
            raise ValueError("User already has an active sleep session")

        # Create new session with current time in UTC
        now = datetime.now(pytz.UTC)
        session = await self.repository.start_sleep_session(user.id, now)

        return session

    async def end_sleep_session(self, user: User) -> Optional[SleepSession]:
        """End user's active sleep session.

        Args:
            user: User waking up

        Returns:
            Completed sleep session, or None if no active session

        Raises:
            ValueError: If no active session found
        """
        active_session = await self.get_active_session(user)
        if not active_session:
            raise ValueError("No active sleep session found")

        # End session with current time in UTC
        now = datetime.now(pytz.UTC)
        session = await self.repository.end_sleep_session(active_session, now)

        return session

    async def cancel_active_session(self, user: User) -> None:
        """Cancel and delete user's active sleep session.

        Args:
            user: User whose session to cancel
        """
        active_session = await self.get_active_session(user)
        if active_session:
            await self.repository.delete(active_session)

    async def get_last_completed_session(self, user: User) -> Optional[SleepSession]:
        """Get user's most recent completed session.

        Args:
            user: User to check

        Returns:
            Last completed session if exists, None otherwise
        """
        return await self.repository.get_last_completed_session(user.id)

    async def add_quality_rating(
        self, session: SleepSession, quality_rating: float
    ) -> SleepSession:
        """Add quality rating to a sleep session.

        Args:
            session: Sleep session to rate
            quality_rating: Quality rating (1.0 - 10.0)

        Returns:
            Updated session

        Raises:
            ValueError: If rating is out of range or session is not completed
        """
        if not (1.0 <= quality_rating <= 10.0):
            raise ValueError("Quality rating must be between 1.0 and 10.0")

        if session.sleep_end is None:
            raise ValueError("Cannot rate an active sleep session")

        return await self.repository.add_quality_rating(session, quality_rating)

    async def add_note(self, session: SleepSession, note: str) -> SleepSession:
        """Add or update note for a sleep session.

        Args:
            session: Sleep session
            note: Note text

        Returns:
            Updated session

        Raises:
            ValueError: If note is empty or session is not completed
        """
        if not note or not note.strip():
            raise ValueError("Note cannot be empty")

        if session.sleep_end is None:
            raise ValueError("Cannot add note to an active sleep session")

        return await self.repository.add_note(session, note.strip())

    def calculate_goal_percentage(self, user: User, session: SleepSession) -> Optional[int]:
        """Calculate what percentage of sleep goal was achieved.

        Args:
            user: User with sleep goals
            session: Completed sleep session

        Returns:
            Percentage (0-100+) if user has goals, None otherwise
        """
        if not user.target_sleep_hours or not session.duration_hours:
            return None

        percentage = int((session.duration_hours / user.target_sleep_hours) * 100)
        return percentage

    def format_duration(self, hours: float) -> tuple[int, int]:
        """Format duration in hours to (hours, minutes).

        Args:
            hours: Duration in hours

        Returns:
            Tuple of (hours, minutes)
        """
        h = int(hours)
        m = int((hours - h) * 60)
        return h, m

    def format_time_for_user(self, dt: datetime, user: User) -> str:
        """Format datetime for user's timezone.

        Args:
            dt: Datetime in UTC
            user: User with timezone info

        Returns:
            Formatted time string (HH:MM)
        """
        user_time = self._convert_from_utc(dt, user.timezone)
        return user_time.strftime("%H:%M")

    async def get_sessions_by_date_range(
        self, user: User, start_date: datetime, end_date: datetime
    ) -> list[SleepSession]:
        """Get sleep sessions within date range.

        Args:
            user: User
            start_date: Start date (in user's timezone)
            end_date: End date (in user's timezone)

        Returns:
            List of sleep sessions
        """
        # Convert dates to UTC
        start_utc = self._convert_to_utc(start_date, user.timezone)
        end_utc = self._convert_to_utc(end_date, user.timezone)

        return await self.repository.get_sessions_by_date_range(
            user.id, start_utc, end_utc, only_completed=True
        )

    async def get_all_user_sessions(self, user: User) -> list[SleepSession]:
        """Get all completed sessions for user.

        Args:
            user: User

        Returns:
            List of sleep sessions
        """
        return await self.repository.get_all_user_sessions(user.id, only_completed=True)

    async def get_first_session_date(self, user: User) -> Optional[datetime]:
        """Get date of user's first sleep session.

        Args:
            user: User

        Returns:
            Date of first session in user's timezone, None if no sessions
        """
        first_date_utc = await self.repository.get_first_session_date(user.id)
        if not first_date_utc:
            return None

        return self._convert_from_utc(first_date_utc, user.timezone)
