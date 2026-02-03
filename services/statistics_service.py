from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.sleep_repository import SleepRepository
from utils.logger import get_logger

logger = get_logger(__name__)


class StatisticsService:
    """Service for generating sleep statistics and exports."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize statistics service.

        Args:
            session: Async database session
        """
        self.repository = SleepRepository(session)

    async def get_statistics(
        self,
        user: User,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, any]:
        """Get aggregated sleep statistics.

        Args:
            user: User
            start_date: Optional start date filter (UTC)
            end_date: Optional end date filter (UTC)

        Returns:
            Dictionary with statistics
        """
        stats = await self.repository.get_statistics(
            user.id, start_date=start_date, end_date=end_date
        )

        logger.info(
            "statistics_generated",
            user_id=user.id,
            total_sessions=stats["total_sessions"],
            avg_duration=stats["avg_duration"],
        )

        return stats

    async def prepare_export_data(
        self,
        user: User,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict[str, any]]:
        """Prepare sleep data for export.

        Args:
            user: User
            start_date: Optional start date filter (UTC)
            end_date: Optional end date filter (UTC)

        Returns:
            List of dictionaries with sleep session data
        """
        # Get sessions
        if start_date and end_date:
            sessions = await self.repository.get_sessions_by_date_range(
                user.id, start_date, end_date, only_completed=True
            )
        else:
            sessions = await self.repository.get_all_user_sessions(user.id, only_completed=True)

        # Format data for export
        export_data = []
        for session in sessions:
            export_data.append({
                "date": session.sleep_start.strftime("%Y-%m-%d"),
                "sleep_start": session.sleep_start.strftime("%Y-%m-%d %H:%M:%S"),
                "sleep_end": session.sleep_end.strftime("%Y-%m-%d %H:%M:%S")
                if session.sleep_end
                else "N/A",
                "duration_hours": session.duration_hours if session.duration_hours else 0,
                "quality_rating": session.quality_rating if session.quality_rating else "N/A",
                "note": session.note if session.note else "N/A",
            })

        logger.info(
            "export_data_prepared",
            user_id=user.id,
            records_count=len(export_data),
        )

        return export_data

    def format_export_message(
        self, stats: dict[str, any], total_records: int, date_range: Optional[str] = None
    ) -> str:
        """Format statistics message for export.

        Args:
            stats: Statistics dictionary
            total_records: Number of records exported
            date_range: Optional date range string

        Returns:
            Formatted message
        """
        message = "📊 Sleep Statistics Export\n\n"

        if date_range:
            message += f"📅 Period: {date_range}\n"

        message += f"📝 Total sessions: {stats['total_sessions']}\n"
        message += f"⏱ Average duration: {stats['avg_duration']:.1f}h\n"

        if stats.get("avg_quality", 0) > 0:
            message += f"⭐️ Average quality: {stats['avg_quality']:.1f}/10\n"

        message += f"💤 Total sleep: {stats['total_sleep_hours']:.1f}h\n"

        return message

    async def has_any_data(self, user: User) -> bool:
        """Check if user has any sleep data.

        Args:
            user: User to check

        Returns:
            True if user has at least one completed session
        """
        stats = await self.repository.get_statistics(user.id)
        return stats["total_sessions"] > 0
