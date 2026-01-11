from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Get language selection keyboard.

    Returns:
        Keyboard with language options
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="🇬🇧 English", callback_data="lang_en")
    builder.button(text="🇷🇺 Русский", callback_data="lang_ru")
    builder.button(text="🇪🇪 Eesti", callback_data="lang_et")
    builder.adjust(1)  # One button per row
    return builder.as_markup()


def get_sleep_conflict_keyboard(duration_hours: int, duration_minutes: int) -> InlineKeyboardMarkup:
    """Get keyboard for handling sleep session conflict.

    Args:
        duration_hours: Current session duration in hours
        duration_minutes: Current session duration in minutes

    Returns:
        Keyboard with conflict resolution options
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"💾 Save ({duration_hours}h {duration_minutes}m) & Start New",
        callback_data="sleep_save_and_start",
    )
    builder.button(text="▶️ Continue Current", callback_data="sleep_continue")
    builder.button(text="🔄 Cancel & Start New", callback_data="sleep_cancel_and_start")
    builder.adjust(1)
    return builder.as_markup()


def get_stats_period_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for statistics period selection.

    Returns:
        Keyboard with period options
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Last 7 days", callback_data="stats_period_week")
    builder.button(text="📅 Last 30 days", callback_data="stats_period_month")
    builder.button(text="📅 All time", callback_data="stats_period_all")
    builder.button(text="📅 Custom range", callback_data="stats_period_custom")
    builder.adjust(1)
    return builder.as_markup()


def get_stats_format_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for export format selection.

    Returns:
        Keyboard with format options
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 CSV", callback_data="stats_format_csv")
    builder.button(text="📄 JSON", callback_data="stats_format_json")
    builder.button(text="⬅️ Back", callback_data="stats_back")
    builder.adjust(2, 1)  # 2 buttons in first row, 1 in second
    return builder.as_markup()


def get_confirmation_keyboard(confirm_data: str, cancel_data: str = "cancel") -> InlineKeyboardMarkup:
    """Get confirmation keyboard.

    Args:
        confirm_data: Callback data for confirm button
        cancel_data: Callback data for cancel button

    Returns:
        Keyboard with confirm/cancel buttons
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Confirm", callback_data=confirm_data)
    builder.button(text="❌ Cancel", callback_data=cancel_data)
    builder.adjust(2)
    return builder.as_markup()


def get_back_button(callback_data: str = "back") -> InlineKeyboardMarkup:
    """Get keyboard with back button only.

    Args:
        callback_data: Callback data for back button

    Returns:
        Keyboard with back button
    """
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Back", callback_data=callback_data)
    return builder.as_markup()
