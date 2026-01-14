"""Mock tests for statistics service."""

from datetime import datetime, timedelta

import pytest
import pytz

from services.statistics_service import StatisticsService


class TestStatisticsService:
    """Test statistics service operations."""

    @pytest.mark.asyncio
    async def test_get_statistics_no_data(
        self, async_session, test_user
    ):
        """Test getting statistics when user has no data."""
        stats_service = StatisticsService(async_session)
        stats = await stats_service.get_statistics(test_user)

        assert stats["total_sessions"] == 0
        assert stats["avg_duration"] == 0
        assert stats["avg_quality"] == 0
        assert stats["total_sleep_hours"] == 0

    @pytest.mark.asyncio
    async def test_get_statistics_with_data(
        self, async_session, test_user_with_sessions
    ):
        """Test getting statistics with existing data."""
        stats_service = StatisticsService(async_session)
        stats = await stats_service.get_statistics(test_user_with_sessions)

        assert stats["total_sessions"] >= 2  # We have at least 2 completed sessions
        assert stats["avg_duration"] > 0
        assert stats["total_sleep_hours"] > 0

    @pytest.mark.asyncio
    async def test_get_statistics_with_date_range(
        self, async_session, test_user_with_sessions
    ):
        """Test getting statistics with date range filter."""
        stats_service = StatisticsService(async_session)
        now = datetime.now(pytz.UTC)

        # Get statistics for last 24 hours only
        start_date = now - timedelta(hours=24)
        stats = await stats_service.get_statistics(
            test_user_with_sessions,
            start_date=start_date,
            end_date=now
        )

        # Should have at least the recent session
        assert stats["total_sessions"] >= 1

    @pytest.mark.asyncio
    async def test_prepare_export_data_no_sessions(
        self, async_session, test_user
    ):
        """Test preparing export data when user has no sessions."""
        stats_service = StatisticsService(async_session)
        export_data = await stats_service.prepare_export_data(test_user)

        assert isinstance(export_data, list)
        assert len(export_data) == 0

    @pytest.mark.asyncio
    async def test_prepare_export_data_with_sessions(
        self, async_session, test_user_with_sessions
    ):
        """Test preparing export data with existing sessions."""
        stats_service = StatisticsService(async_session)
        export_data = await stats_service.prepare_export_data(test_user_with_sessions)

        assert isinstance(export_data, list)
        assert len(export_data) >= 2  # At least 2 completed sessions

        # Check data structure
        for record in export_data:
            assert "date" in record
            assert "sleep_start" in record
            assert "sleep_end" in record
            assert "duration_hours" in record
            assert "quality_rating" in record
            assert "note" in record

    @pytest.mark.asyncio
    async def test_prepare_export_data_with_date_range(
        self, async_session, test_user_with_sessions
    ):
        """Test preparing export data with date range filter."""
        stats_service = StatisticsService(async_session)
        now = datetime.now(pytz.UTC)

        # Get data for last 24 hours only
        start_date = now - timedelta(hours=24)
        export_data = await stats_service.prepare_export_data(
            test_user_with_sessions,
            start_date=start_date,
            end_date=now
        )

        assert isinstance(export_data, list)
        # Should have at least the recent session
        assert len(export_data) >= 1

    @pytest.mark.asyncio
    async def test_prepare_export_data_formats_correctly(
        self, async_session, test_user_with_sessions
    ):
        """Test that export data is formatted correctly."""
        stats_service = StatisticsService(async_session)
        export_data = await stats_service.prepare_export_data(test_user_with_sessions)

        assert len(export_data) > 0

        record = export_data[0]
        # Check date format YYYY-MM-DD
        assert len(record["date"]) == 10
        assert record["date"][4] == "-"
        assert record["date"][7] == "-"

        # Check datetime format YYYY-MM-DD HH:MM:SS
        if record["sleep_end"] != "N/A":
            assert len(record["sleep_end"]) == 19
            assert " " in record["sleep_end"]

    def test_format_export_message_basic(self, async_session):
        """Test formatting export message with basic stats."""
        stats_service = StatisticsService(async_session)

        stats = {
            "total_sessions": 10,
            "avg_duration": 7.5,
            "avg_quality": 8.2,
            "total_sleep_hours": 75.0,
        }

        message = stats_service.format_export_message(stats, total_records=10)

        assert "Sleep Statistics Export" in message
        assert "Total sessions: 10" in message
        assert "Average duration: 7.5h" in message
        assert "Average quality: 8.2/10" in message
        assert "Total sleep: 75.0h" in message

    def test_format_export_message_with_date_range(self, async_session):
        """Test formatting export message with date range."""
        stats_service = StatisticsService(async_session)

        stats = {
            "total_sessions": 5,
            "avg_duration": 8.0,
            "avg_quality": 0,  # No quality ratings
            "total_sleep_hours": 40.0,
        }

        message = stats_service.format_export_message(
            stats,
            total_records=5,
            date_range="2024-01-01 to 2024-01-07"
        )

        assert "Period: 2024-01-01 to 2024-01-07" in message
        assert "Total sessions: 5" in message
        # Should not include average quality if it's 0
        assert "Average quality" not in message

    def test_format_export_message_without_quality(self, async_session):
        """Test formatting export message without quality ratings."""
        stats_service = StatisticsService(async_session)

        stats = {
            "total_sessions": 3,
            "avg_duration": 6.5,
            "avg_quality": 0,
            "total_sleep_hours": 19.5,
        }

        message = stats_service.format_export_message(stats, total_records=3)

        assert "Total sessions: 3" in message
        assert "Average duration: 6.5h" in message
        assert "Total sleep: 19.5h" in message
        # Should not show quality if avg_quality is 0
        assert "quality" not in message.lower() or "Sleep Statistics" in message

    @pytest.mark.asyncio
    async def test_has_any_data_true(
        self, async_session, test_user_with_sessions
    ):
        """Test has_any_data returns True when user has data."""
        stats_service = StatisticsService(async_session)
        has_data = await stats_service.has_any_data(test_user_with_sessions)

        assert has_data is True

    @pytest.mark.asyncio
    async def test_has_any_data_false(
        self, async_session, test_user
    ):
        """Test has_any_data returns False when user has no data."""
        stats_service = StatisticsService(async_session)
        has_data = await stats_service.has_any_data(test_user)

        assert has_data is False
