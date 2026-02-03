from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import get_language_keyboard
from database import get_session
from localization import LocalizationService
from services.user_service import UserService
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="language")


@router.message(Command("language"))
async def cmd_language(message: Message, lang: str, loc: LocalizationService) -> None:
    """Handle /language command.

    Args:
        message: Telegram message
        lang: User's language code
        loc: Localization service
    """
    select_text = loc.get("commands.language.select", lang)

    await message.answer(select_text, reply_markup=get_language_keyboard())

    logger.info("language_command", telegram_id=message.from_user.id)


@router.callback_query(F.data.startswith("lang_change_"))
async def handle_language_change(
    callback: CallbackQuery, loc: LocalizationService
) -> None:
    """Handle language change from /language command.

    Args:
        callback: Callback query
        loc: Localization service
    """
    if not callback.data or not callback.from_user:
        return

    selected_lang = callback.data.split("_")[-1]  # Extract language code

    async for session in get_session():
        try:
            user_service = UserService(session)
            db_user = await user_service.get_user_by_telegram_id(callback.from_user.id)

            if db_user:
                # Update language
                await user_service.update_language(db_user, selected_lang)

                # Send confirmation
                changed_msg = loc.get("commands.language.changed", selected_lang)
                await callback.message.edit_text(changed_msg)
                await callback.answer()

                logger.info(
                    "language_changed",
                    telegram_id=callback.from_user.id,
                    language=selected_lang,
                )

        except Exception as e:
            logger.error(
                "language_change_error",
                telegram_id=callback.from_user.id,
                error=str(e),
            )
            await callback.answer(loc.get("errors.generic", selected_lang), show_alert=True)

        # Commit before break - otherwise changes won't be saved
        await session.commit()
        break
