"""Unit tests for keyboard builder functions."""

from unittest.mock import Mock

import pytest
from aiogram.types import InlineKeyboardMarkup

from bot.keyboards.inline import (
    get_back_button,
    get_confirmation_keyboard,
    get_language_keyboard,
    get_note_confirmation_keyboard,
    get_quality_confirmation_keyboard,
    get_quality_rating_keyboard,
    get_sleep_conflict_keyboard,
    get_stats_format_keyboard,
    get_stats_period_keyboard,
)


class TestLanguageKeyboard:
    """Test get_language_keyboard function."""

    def test_returns_inline_keyboard_markup(self):
        """Test that function returns InlineKeyboardMarkup."""
        keyboard = get_language_keyboard()
        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_has_three_language_buttons(self):
        """Test that keyboard has three language buttons."""
        keyboard = get_language_keyboard()
        # Should have 3 buttons in total (en, ru, et)
        total_buttons = sum(len(row) for row in keyboard.inline_keyboard)
        assert total_buttons == 3

    def test_button_callback_data(self):
        """Test that buttons have correct callback data."""
        keyboard = get_language_keyboard()
        callback_data = [
            button.callback_data for row in keyboard.inline_keyboard for button in row
        ]
        assert "lang_en" in callback_data
        assert "lang_ru" in callback_data
        assert "lang_et" in callback_data


class TestSleepConflictKeyboard:
    """Test get_sleep_conflict_keyboard function."""

    def test_returns_inline_keyboard_markup(self):
        """Test that function returns InlineKeyboardMarkup."""
        keyboard = get_sleep_conflict_keyboard(7, 30)
        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_has_three_buttons(self):
        """Test that keyboard has three conflict resolution buttons."""
        keyboard = get_sleep_conflict_keyboard(7, 30)
        total_buttons = sum(len(row) for row in keyboard.inline_keyboard)
        assert total_buttons == 3

    def test_displays_duration_in_button_text(self):
        """Test that duration is displayed in save button text."""
        keyboard = get_sleep_conflict_keyboard(8, 45)
        button_texts = [
            button.text for row in keyboard.inline_keyboard for button in row
        ]
        # Check that at least one button contains the duration
        assert any("8h" in text and "45m" in text for text in button_texts)

    def test_callback_data_values(self):
        """Test that buttons have correct callback data."""
        keyboard = get_sleep_conflict_keyboard(5, 15)
        callback_data = [
            button.callback_data for row in keyboard.inline_keyboard for button in row
        ]
        assert "sleep_save_and_start" in callback_data
        assert "sleep_continue" in callback_data
        assert "sleep_cancel_and_start" in callback_data


class TestStatsPeriodKeyboard:
    """Test get_stats_period_keyboard function."""

    def test_returns_inline_keyboard_markup(self):
        """Test that function returns InlineKeyboardMarkup."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_stats_period_keyboard(loc, "en")
        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_has_four_period_buttons(self):
        """Test that keyboard has four period selection buttons."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_stats_period_keyboard(loc, "en")
        total_buttons = sum(len(row) for row in keyboard.inline_keyboard)
        assert total_buttons == 4

    def test_callback_data_values(self):
        """Test that buttons have correct callback data."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_stats_period_keyboard(loc, "en")
        callback_data = [
            button.callback_data for row in keyboard.inline_keyboard for button in row
        ]
        assert "stats_period_week" in callback_data
        assert "stats_period_month" in callback_data
        assert "stats_period_all" in callback_data
        assert "stats_period_custom" in callback_data

    def test_uses_localization(self):
        """Test that localization service is called for button texts."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: f"translated_{key}")
        keyboard = get_stats_period_keyboard(loc, "ru")

        # Check that loc.get was called
        assert loc.get.called
        # Check language was passed
        assert any(call[0][1] == "ru" for call in loc.get.call_args_list)


class TestStatsFormatKeyboard:
    """Test get_stats_format_keyboard function."""

    def test_returns_inline_keyboard_markup(self):
        """Test that function returns InlineKeyboardMarkup."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_stats_format_keyboard(loc, "en")
        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_has_three_buttons(self):
        """Test that keyboard has CSV, JSON, and back buttons."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_stats_format_keyboard(loc, "en")
        total_buttons = sum(len(row) for row in keyboard.inline_keyboard)
        assert total_buttons == 3

    def test_callback_data_values(self):
        """Test that buttons have correct callback data."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_stats_format_keyboard(loc, "en")
        callback_data = [
            button.callback_data for row in keyboard.inline_keyboard for button in row
        ]
        assert "stats_format_csv" in callback_data
        assert "stats_format_json" in callback_data
        assert "stats_back" in callback_data


class TestConfirmationKeyboard:
    """Test get_confirmation_keyboard function."""

    def test_returns_inline_keyboard_markup(self):
        """Test that function returns InlineKeyboardMarkup."""
        keyboard = get_confirmation_keyboard("confirm_action")
        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_has_two_buttons(self):
        """Test that keyboard has confirm and cancel buttons."""
        keyboard = get_confirmation_keyboard("confirm_action")
        total_buttons = sum(len(row) for row in keyboard.inline_keyboard)
        assert total_buttons == 2

    def test_uses_custom_confirm_data(self):
        """Test that custom confirm callback data is used."""
        keyboard = get_confirmation_keyboard("custom_confirm")
        callback_data = [
            button.callback_data for row in keyboard.inline_keyboard for button in row
        ]
        assert "custom_confirm" in callback_data

    def test_uses_default_cancel_data(self):
        """Test that default cancel callback data is used."""
        keyboard = get_confirmation_keyboard("confirm_action")
        callback_data = [
            button.callback_data for row in keyboard.inline_keyboard for button in row
        ]
        assert "cancel" in callback_data

    def test_uses_custom_cancel_data(self):
        """Test that custom cancel callback data can be provided."""
        keyboard = get_confirmation_keyboard("confirm_action", "custom_cancel")
        callback_data = [
            button.callback_data for row in keyboard.inline_keyboard for button in row
        ]
        assert "custom_cancel" in callback_data


class TestBackButton:
    """Test get_back_button function."""

    def test_returns_inline_keyboard_markup(self):
        """Test that function returns InlineKeyboardMarkup."""
        keyboard = get_back_button()
        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_has_one_button(self):
        """Test that keyboard has one button."""
        keyboard = get_back_button()
        total_buttons = sum(len(row) for row in keyboard.inline_keyboard)
        assert total_buttons == 1

    def test_uses_default_callback_data(self):
        """Test that default callback data is 'back'."""
        keyboard = get_back_button()
        button = keyboard.inline_keyboard[0][0]
        assert button.callback_data == "back"

    def test_uses_custom_callback_data(self):
        """Test that custom callback data can be provided."""
        keyboard = get_back_button("custom_back")
        button = keyboard.inline_keyboard[0][0]
        assert button.callback_data == "custom_back"


class TestQualityRatingKeyboard:
    """Test get_quality_rating_keyboard function."""

    def test_returns_inline_keyboard_markup(self):
        """Test that function returns InlineKeyboardMarkup."""
        keyboard = get_quality_rating_keyboard()
        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_has_ten_buttons(self):
        """Test that keyboard has ten rating buttons (1-10)."""
        keyboard = get_quality_rating_keyboard()
        total_buttons = sum(len(row) for row in keyboard.inline_keyboard)
        assert total_buttons == 10

    def test_buttons_arranged_in_two_rows(self):
        """Test that buttons are arranged in two rows of 5."""
        keyboard = get_quality_rating_keyboard()
        assert len(keyboard.inline_keyboard) == 2
        assert len(keyboard.inline_keyboard[0]) == 5
        assert len(keyboard.inline_keyboard[1]) == 5

    def test_callback_data_format(self):
        """Test that callback data follows quality_rate_N format."""
        keyboard = get_quality_rating_keyboard()
        callback_data = [
            button.callback_data for row in keyboard.inline_keyboard for button in row
        ]
        for i in range(1, 11):
            assert f"quality_rate_{i}" in callback_data

    def test_button_text_matches_rating(self):
        """Test that button text matches the rating number."""
        keyboard = get_quality_rating_keyboard()
        button_texts = [
            button.text for row in keyboard.inline_keyboard for button in row
        ]
        for i in range(1, 11):
            assert str(i) in button_texts


class TestQualityConfirmationKeyboard:
    """Test get_quality_confirmation_keyboard function."""

    def test_returns_inline_keyboard_markup(self):
        """Test that function returns InlineKeyboardMarkup."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_quality_confirmation_keyboard(7.5, loc, "en")
        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_has_two_buttons(self):
        """Test that keyboard has confirm and cancel buttons."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_quality_confirmation_keyboard(8.0, loc, "en")
        total_buttons = sum(len(row) for row in keyboard.inline_keyboard)
        assert total_buttons == 2

    def test_callback_data_includes_rating(self):
        """Test that confirm callback data includes the rating."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_quality_confirmation_keyboard(7.5, loc, "en")
        callback_data = [
            button.callback_data for row in keyboard.inline_keyboard for button in row
        ]
        assert "quality_confirm_7.5" in callback_data

    def test_cancel_callback_data(self):
        """Test that cancel callback data is correct."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_quality_confirmation_keyboard(9.0, loc, "en")
        callback_data = [
            button.callback_data for row in keyboard.inline_keyboard for button in row
        ]
        assert "quality_cancel" in callback_data

    def test_uses_localization(self):
        """Test that localization service is used for button texts."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_quality_confirmation_keyboard(8.0, loc, "ru")

        # Check that loc.get was called for confirm and cancel buttons
        assert loc.get.call_count >= 2


class TestNoteConfirmationKeyboard:
    """Test get_note_confirmation_keyboard function."""

    def test_returns_inline_keyboard_markup(self):
        """Test that function returns InlineKeyboardMarkup."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_note_confirmation_keyboard(loc, "en")
        assert isinstance(keyboard, InlineKeyboardMarkup)

    def test_has_two_buttons(self):
        """Test that keyboard has confirm and cancel buttons."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_note_confirmation_keyboard(loc, "en")
        total_buttons = sum(len(row) for row in keyboard.inline_keyboard)
        assert total_buttons == 2

    def test_callback_data_values(self):
        """Test that buttons have correct callback data."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_note_confirmation_keyboard(loc, "en")
        callback_data = [
            button.callback_data for row in keyboard.inline_keyboard for button in row
        ]
        assert "note_confirm" in callback_data
        assert "note_cancel" in callback_data

    def test_uses_localization(self):
        """Test that localization service is used for button texts."""
        loc = Mock()
        loc.get = Mock(side_effect=lambda key, lang: key)
        keyboard = get_note_confirmation_keyboard(loc, "et")

        # Check that loc.get was called
        assert loc.get.called
        # Check that the correct language was used
        assert any(call[0][1] == "et" for call in loc.get.call_args_list)
