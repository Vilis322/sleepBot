"""Unit tests for formatting functions in sleep_service.py."""

from datetime import datetime
from unittest.mock import Mock

import pytest
import pytz

from services.sleep_service import SleepService


@pytest.fixture
def sleep_service():
    """Create SleepService instance with mock session."""
    mock_session = Mock()
    return SleepService(mock_session)


class TestFormatDuration:
    """Test format_duration function."""

    def test_format_duration_whole_hours(self, sleep_service):
        """Test formatting duration with whole hours."""
        hours, minutes = sleep_service.format_duration(8.0)
        assert hours == 8
        assert minutes == 0

    def test_format_duration_with_minutes(self, sleep_service):
        """Test formatting duration with hours and minutes."""
        hours, minutes = sleep_service.format_duration(7.5)
        assert hours == 7
        assert minutes == 30

    def test_format_duration_quarter_hour(self, sleep_service):
        """Test formatting duration with quarter hour."""
        hours, minutes = sleep_service.format_duration(5.25)
        assert hours == 5
        assert minutes == 15

    def test_format_duration_three_quarters(self, sleep_service):
        """Test formatting duration with three quarters."""
        hours, minutes = sleep_service.format_duration(9.75)
        assert hours == 9
        assert minutes == 45

    def test_format_duration_less_than_hour(self, sleep_service):
        """Test formatting duration less than one hour."""
        hours, minutes = sleep_service.format_duration(0.5)
        assert hours == 0
        assert minutes == 30

    def test_format_duration_fractional_minutes(self, sleep_service):
        """Test formatting duration with fractional minutes."""
        hours, minutes = sleep_service.format_duration(7.33)
        assert hours == 7
        assert minutes == 19  # 0.33 * 60 = 19.8 -> 19

    def test_format_duration_zero(self, sleep_service):
        """Test formatting zero duration."""
        hours, minutes = sleep_service.format_duration(0.0)
        assert hours == 0
        assert minutes == 0

    def test_format_duration_large_value(self, sleep_service):
        """Test formatting large duration value."""
        hours, minutes = sleep_service.format_duration(23.99)
        assert hours == 23
        assert minutes == 59


class TestFormatTimeAgo:
    """Test format_time_ago function."""

    def test_format_time_ago_minutes(self, sleep_service):
        """Test formatting time less than 1 hour ago."""
        result = sleep_service.format_time_ago(0.5)
        assert result == "30 minutes ago"

    def test_format_time_ago_one_minute(self, sleep_service):
        """Test formatting 1 minute ago."""
        result = sleep_service.format_time_ago(0.016)  # ~1 minute
        assert result == "0 minutes ago"

    def test_format_time_ago_59_minutes(self, sleep_service):
        """Test formatting 59 minutes ago."""
        result = sleep_service.format_time_ago(0.99)
        assert result == "59 minutes ago"

    def test_format_time_ago_one_hour(self, sleep_service):
        """Test formatting exactly 1 hour ago."""
        result = sleep_service.format_time_ago(1.0)
        assert result == "1 hours ago"

    def test_format_time_ago_multiple_hours(self, sleep_service):
        """Test formatting multiple hours ago."""
        result = sleep_service.format_time_ago(5.3)
        assert result == "5 hours ago"

    def test_format_time_ago_23_hours(self, sleep_service):
        """Test formatting 23 hours ago (just under 1 day)."""
        result = sleep_service.format_time_ago(23.5)
        assert result == "23 hours ago"

    def test_format_time_ago_one_day(self, sleep_service):
        """Test formatting exactly 1 day ago."""
        result = sleep_service.format_time_ago(24.0)
        assert result == "1 days ago"

    def test_format_time_ago_multiple_days(self, sleep_service):
        """Test formatting multiple days ago."""
        result = sleep_service.format_time_ago(72.5)
        assert result == "3 days ago"

    def test_format_time_ago_one_week(self, sleep_service):
        """Test formatting one week ago."""
        result = sleep_service.format_time_ago(168.0)
        assert result == "7 days ago"

    def test_format_time_ago_zero(self, sleep_service):
        """Test formatting zero hours ago."""
        result = sleep_service.format_time_ago(0.0)
        assert result == "0 minutes ago"


class TestCalculateGoalPercentage:
    """Test calculate_goal_percentage function."""

    def test_calculate_goal_percentage_100_percent(self, sleep_service):
        """Test calculating goal percentage when exactly meeting goal."""
        user = Mock(target_sleep_hours=8.0)
        session = Mock(duration_hours=8.0)

        percentage = sleep_service.calculate_goal_percentage(user, session)
        assert percentage == 100

    def test_calculate_goal_percentage_over_100(self, sleep_service):
        """Test calculating goal percentage when exceeding goal."""
        user = Mock(target_sleep_hours=8.0)
        session = Mock(duration_hours=10.0)

        percentage = sleep_service.calculate_goal_percentage(user, session)
        assert percentage == 125

    def test_calculate_goal_percentage_under_100(self, sleep_service):
        """Test calculating goal percentage when under goal."""
        user = Mock(target_sleep_hours=8.0)
        session = Mock(duration_hours=6.0)

        percentage = sleep_service.calculate_goal_percentage(user, session)
        assert percentage == 75

    def test_calculate_goal_percentage_50_percent(self, sleep_service):
        """Test calculating 50% of goal."""
        user = Mock(target_sleep_hours=8.0)
        session = Mock(duration_hours=4.0)

        percentage = sleep_service.calculate_goal_percentage(user, session)
        assert percentage == 50

    def test_calculate_goal_percentage_fractional(self, sleep_service):
        """Test calculating goal percentage with fractional hours."""
        user = Mock(target_sleep_hours=7.5)
        session = Mock(duration_hours=6.0)

        percentage = sleep_service.calculate_goal_percentage(user, session)
        assert percentage == 80  # 6.0 / 7.5 = 0.8

    def test_calculate_goal_percentage_no_target(self, sleep_service):
        """Test calculating goal percentage when user has no target."""
        user = Mock(target_sleep_hours=None)
        session = Mock(duration_hours=8.0)

        percentage = sleep_service.calculate_goal_percentage(user, session)
        assert percentage is None

    def test_calculate_goal_percentage_no_duration(self, sleep_service):
        """Test calculating goal percentage when session has no duration."""
        user = Mock(target_sleep_hours=8.0)
        session = Mock(duration_hours=None)

        percentage = sleep_service.calculate_goal_percentage(user, session)
        assert percentage is None

    def test_calculate_goal_percentage_both_none(self, sleep_service):
        """Test calculating goal percentage when both are None."""
        user = Mock(target_sleep_hours=None)
        session = Mock(duration_hours=None)

        percentage = sleep_service.calculate_goal_percentage(user, session)
        assert percentage is None

    def test_calculate_goal_percentage_very_high(self, sleep_service):
        """Test calculating goal percentage with very high value."""
        user = Mock(target_sleep_hours=6.0)
        session = Mock(duration_hours=12.0)

        percentage = sleep_service.calculate_goal_percentage(user, session)
        assert percentage == 200


class TestFormatTimeForUser:
    """Test format_time_for_user function."""

    def test_format_time_for_user_utc(self, sleep_service):
        """Test formatting time for user in UTC timezone."""
        user = Mock(timezone="UTC")
        dt = datetime(2026, 1, 14, 15, 30, 0, tzinfo=pytz.UTC)

        result = sleep_service.format_time_for_user(dt, user)
        assert result == "15:30"

    def test_format_time_for_user_tallinn(self, sleep_service):
        """Test formatting time for user in Tallinn timezone."""
        user = Mock(timezone="Europe/Tallinn")
        dt = datetime(2026, 1, 14, 13, 30, 0, tzinfo=pytz.UTC)  # 13:30 UTC

        result = sleep_service.format_time_for_user(dt, user)
        # Tallinn is UTC+2 in winter
        assert result == "15:30"

    def test_format_time_for_user_new_york(self, sleep_service):
        """Test formatting time for user in New York timezone."""
        user = Mock(timezone="America/New_York")
        dt = datetime(2026, 1, 14, 20, 0, 0, tzinfo=pytz.UTC)  # 20:00 UTC

        result = sleep_service.format_time_for_user(dt, user)
        # New York is UTC-5 in winter
        assert result == "15:00"

    def test_format_time_for_user_midnight(self, sleep_service):
        """Test formatting midnight time."""
        user = Mock(timezone="UTC")
        dt = datetime(2026, 1, 14, 0, 0, 0, tzinfo=pytz.UTC)

        result = sleep_service.format_time_for_user(dt, user)
        assert result == "00:00"

    def test_format_time_for_user_single_digit_hour(self, sleep_service):
        """Test formatting time with single digit hour."""
        user = Mock(timezone="UTC")
        dt = datetime(2026, 1, 14, 9, 5, 0, tzinfo=pytz.UTC)

        result = sleep_service.format_time_for_user(dt, user)
        assert result == "09:05"

    def test_format_time_for_user_tokyo(self, sleep_service):
        """Test formatting time for user in Tokyo timezone."""
        user = Mock(timezone="Asia/Tokyo")
        dt = datetime(2026, 1, 14, 15, 0, 0, tzinfo=pytz.UTC)  # 15:00 UTC

        result = sleep_service.format_time_for_user(dt, user)
        # Tokyo is UTC+9
        assert result == "00:00"  # Next day
