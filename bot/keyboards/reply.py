from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from localization import LocalizationService


def get_timezone_location_keyboard(loc: LocalizationService, lang: str) -> ReplyKeyboardMarkup:
    """Get keyboard for timezone detection via location sharing.

    Args:
        loc: Localization service
        lang: Language code

    Returns:
        ReplyKeyboardMarkup with location share and manual choice buttons
    """
    share_text = loc.get("commands.start.onboarding.timezone_share_location", lang)
    manual_text = loc.get("commands.start.onboarding.timezone_choose_manually", lang)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=share_text, request_location=True)],
            [KeyboardButton(text=manual_text)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard
