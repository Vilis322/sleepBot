from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.sleep_session import SleepSession
from repositories.base import BaseRepository


class SleepRepository(BaseRepository[SleepSession]):
    """Repository for SleepSession model with sleep-specific operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize sleep repository.

        Args:
            session: Async database session
        """
        super().__init__(SleepSession, session)

    async def get_active_session(self, user_id: int) -> Optional[SleepSession]:
        """Get active (not ended) sleep session for user.

        Args:
            user_id: User ID

        Returns:
            Active sleep session if found, None otherwise
        """
        result = await self.session.execute(
            select(SleepSession)
            .where(
                and_(
                    SleepSession.user_id == user_id,
                    SleepSession.sleep_end.is_(None),
                )
            )
            .order_by(desc(SleepSession.sleep_start))
        )
        return result.scalar_one_or_none()

    async def get_last_completed_session(self, user_id: int) -> Optional[SleepSession]:
        """Get the most recent completed sleep session for user.

        Args:
            user_id: User ID

        Returns:
            Last completed sleep session if found, None otherwise
        """
        result = await self.session.execute(
            select(SleepSession)
            .where(
                and_(
                    SleepSession.user_id == user_id,
                    SleepSession.sleep_end.is_not(None),
                )
            )
            .order_by(desc(SleepSession.sleep_end))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def start_sleep_session(self, user_id: int, sleep_start: datetime) -> SleepSession:
        """Start a new sleep session.

        Args:
            user_id: User ID
            sleep_start: Sleep start time (UTC)

        Returns:
            Created sleep session
        """
        session = await self.create(
            user_id=user_id,
            sleep_start=sleep_start,
        )
        return session

    async def end_sleep_session(
        self, session: SleepSession, sleep_end: datetime
    ) -> SleepSession:
        """End an active sleep session.

        Args:
            session: Sleep session to end
            sleep_end: Sleep end time (UTC)

        Returns:
            Updated sleep session
        """
        duration_hours = session.calculate_duration() if session.sleep_end else None
        if sleep_end:
            # Ensure both datetimes are timezone-aware or both naive for subtraction
            import pytz
            sleep_start = session.sleep_start
            sleep_end_calc = sleep_end

            # Make both timezone-aware for calculation
            if sleep_start.tzinfo is None:
                sleep_start = sleep_start.replace(tzinfo=pytz.UTC)
            if sleep_end_calc.tzinfo is None:
                sleep_end_calc = sleep_end_calc.replace(tzinfo=pytz.UTC)

            delta = sleep_end_calc - sleep_start
            duration_hours = round(delta.total_seconds() / 3600, 2)

        session = await self.update(
            session,
            sleep_end=sleep_end,
            duration_hours=duration_hours,
        )
        return session

    async def add_quality_rating(
        self, session: SleepSession, quality_rating: float
    ) -> SleepSession:
        """Add quality rating to a sleep session.

        Args:
            session: Sleep session to rate
            quality_rating: Quality rating (1.0 - 10.0)

        Returns:
            Updated sleep session
        """
        session = await self.update(session, quality_rating=quality_rating)
        return session

    async def add_note(self, session: SleepSession, note: str) -> SleepSession:
        """Add or update note for a sleep session.

        Args:
            session: Sleep session
            note: Note text

        Returns:
            Updated sleep session
        """
        session = await self.update(session, note=note)
        return session

    async def get_sessions_by_date_range(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        only_completed: bool = True,
    ) -> list[SleepSession]:
        """Get sleep sessions within a date range.

        Args:
            user_id: User ID
            start_date: Start date (UTC)
            end_date: End date (UTC)
            only_completed: If True, only return completed sessions

        Returns:
            List of sleep sessions
        """
        query = select(SleepSession).where(
            and_(
                SleepSession.user_id == user_id,
                SleepSession.sleep_start >= start_date,
                SleepSession.sleep_start <= end_date,
            )
        )

        if only_completed:
            query = query.where(SleepSession.sleep_end.is_not(None))

        query = query.order_by(SleepSession.sleep_start)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_user_sessions(
        self, user_id: int, only_completed: bool = True
    ) -> list[SleepSession]:
        """Get all sleep sessions for a user.

        Args:
            user_id: User ID
            only_completed: If True, only return completed sessions

        Returns:
            List of sleep sessions
        """
        query = select(SleepSession).where(SleepSession.user_id == user_id)

        if only_completed:
            query = query.where(SleepSession.sleep_end.is_not(None))

        query = query.order_by(desc(SleepSession.sleep_start))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_first_session_date(self, user_id: int) -> Optional[datetime]:
        """Get the date of the first sleep session for a user.

        Args:
            user_id: User ID

        Returns:
            Date of first session if exists, None otherwise
        """
        result = await self.session.execute(
            select(func.min(SleepSession.sleep_start)).where(SleepSession.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_statistics(
        self, user_id: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> dict[str, any]:
        """Get sleep statistics for a user.

        Args:
            user_id: User ID
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with statistics
        """
        query = select(SleepSession).where(
            and_(
                SleepSession.user_id == user_id,
                SleepSession.sleep_end.is_not(None),
            )
        )

        if start_date:
            query = query.where(SleepSession.sleep_start >= start_date)
        if end_date:
            query = query.where(SleepSession.sleep_start <= end_date)

        result = await self.session.execute(query)
        sessions = list(result.scalars().all())

        if not sessions:
            return {
                "total_sessions": 0,
                "avg_duration": 0,
                "avg_quality": 0,
                "total_sleep_hours": 0,
            }

        total_duration = sum(s.duration_hours or 0 for s in sessions)
        quality_ratings = [s.quality_rating for s in sessions if s.quality_rating is not None]

        return {
            "total_sessions": len(sessions),
            "avg_duration": round(total_duration / len(sessions), 2) if sessions else 0,
            "avg_quality": round(sum(quality_ratings) / len(quality_ratings), 2)
            if quality_ratings
            else 0,
            "total_sleep_hours": round(total_duration, 2),
        }
