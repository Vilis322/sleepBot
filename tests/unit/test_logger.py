"""Unit tests for logger utility functions."""

from colorama import Fore, Style

from utils.logger import add_color_to_level


class TestAddColorToLevel:
    """Test add_color_to_level function."""

    def test_add_color_to_debug_level(self):
        """Test adding color to DEBUG level."""
        event_dict = {"level": "debug", "message": "test"}
        result = add_color_to_level(None, "", event_dict)

        assert "level" in result
        assert Fore.CYAN in result["level"]
        assert "DEBUG" in result["level"]
        assert Style.RESET_ALL in result["level"]

    def test_add_color_to_info_level(self):
        """Test adding color to INFO level."""
        event_dict = {"level": "info", "message": "test"}
        result = add_color_to_level(None, "", event_dict)

        assert "level" in result
        assert Fore.GREEN in result["level"]
        assert "INFO" in result["level"]
        assert Style.RESET_ALL in result["level"]

    def test_add_color_to_warning_level(self):
        """Test adding color to WARNING level."""
        event_dict = {"level": "warning", "message": "test"}
        result = add_color_to_level(None, "", event_dict)

        assert "level" in result
        assert Fore.YELLOW in result["level"]
        assert "WARNING" in result["level"]
        assert Style.RESET_ALL in result["level"]

    def test_add_color_to_error_level(self):
        """Test adding color to ERROR level."""
        event_dict = {"level": "error", "message": "test"}
        result = add_color_to_level(None, "", event_dict)

        assert "level" in result
        assert Fore.RED in result["level"]
        assert "ERROR" in result["level"]
        assert Style.RESET_ALL in result["level"]

    def test_add_color_to_critical_level(self):
        """Test adding color to CRITICAL level."""
        event_dict = {"level": "critical", "message": "test"}
        result = add_color_to_level(None, "", event_dict)

        assert "level" in result
        assert Fore.RED in result["level"]
        assert Style.BRIGHT in result["level"]
        assert "CRITICAL" in result["level"]
        assert Style.RESET_ALL in result["level"]

    def test_add_color_unknown_level(self):
        """Test adding color to unknown level."""
        event_dict = {"level": "unknown", "message": "test"}
        result = add_color_to_level(None, "", event_dict)

        # Unknown levels should not be modified
        assert result["level"] == "unknown"

    def test_add_color_missing_level(self):
        """Test adding color when level key is missing."""
        event_dict = {"message": "test"}
        result = add_color_to_level(None, "", event_dict)

        # Should not crash, just return the dict as-is
        assert "level" not in result

    def test_add_color_preserves_other_keys(self):
        """Test that other keys in event_dict are preserved."""
        event_dict = {
            "level": "info",
            "message": "test message",
            "user_id": 12345,
            "timestamp": "2026-01-14",
        }
        result = add_color_to_level(None, "", event_dict)

        # Level should be colored
        assert Fore.GREEN in result["level"]
        # Other keys should be preserved
        assert result["message"] == "test message"
        assert result["user_id"] == 12345
        assert result["timestamp"] == "2026-01-14"

    def test_add_color_case_insensitive(self):
        """Test that level matching is case-insensitive."""
        # Test with mixed case
        event_dict = {"level": "InFo", "message": "test"}
        result = add_color_to_level(None, "", event_dict)

        # Should convert to uppercase and add color
        assert Fore.GREEN in result["level"]
        assert "INFO" in result["level"]

    def test_add_color_empty_level(self):
        """Test adding color when level is empty string."""
        event_dict = {"level": "", "message": "test"}
        result = add_color_to_level(None, "", event_dict)

        # Empty level should not be modified
        assert result["level"] == ""
