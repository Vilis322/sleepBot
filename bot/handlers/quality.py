from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import get_session
from localization import LocalizationService
from services.sleep_service import SleepService
from services.user_service import UserService
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="quality")


@router.message(Command("quality"))
async def cmd_quality(message: Message, lang: str, loc: LocalizationService) -> None:
    """Handle /quality command - rate sleep quality.

    Args:
        message: Telegram message
        lang: User's language code
        loc: Localization service
    """
    if not message.from_user or not message.text:
        return

    # Extract rating from command
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        error_msg = loc.get("commands.quality.invalid_format", lang)
        await message.answer(error_msg)
        return

    try:
        # Support both comma and dot as decimal separator
        rating_str = parts[1].replace(',', '.')
        rating = float(rating_str)
    except ValueError:
        error_msg = loc.get("commands.quality.invalid_format", lang)
        await message.answer(error_msg)
        return

    # Validate range
    if not (1.0 <= rating <= 10.0):
        error_msg = loc.get("commands.quality.invalid_range", lang)
        await message.answer(error_msg)
        return

    async for session in get_session():
        try:
            user_service = UserService(session)
            sleep_service = SleepService(session)

            db_user = await user_service.get_user_by_telegram_id(message.from_user.id)
            if not db_user:
                await message.answer(loc.get("errors.generic", lang))
                return

            # Get last completed session
            last_session = await sleep_service.get_last_completed_session(db_user)

            if not last_session:
                no_session_msg = loc.get("commands.quality.no_last_session", lang)
                await message.answer(no_session_msg)
                logger.info("quality_no_session", telegram_id=message.from_user.id)
                return

            # Check if already rated
            if last_session.quality_rating is not None:
                already_rated_msg = loc.get(
                    "commands.quality.already_rated",
                    lang,
                    rating=last_session.quality_rating,
                )
                await message.answer(already_rated_msg)
                # Still allow update - don't return

            # Add/update rating
            await sleep_service.add_quality_rating(last_session, rating)

            success_msg = loc.get("commands.quality.saved", lang, rating=rating)
            await message.answer(success_msg)

            logger.info(
                "quality_rated",
                telegram_id=message.from_user.id,
                session_id=last_session.id,
                rating=rating,
            )

        except ValueError as e:
            logger.error("quality_error", telegram_id=message.from_user.id, error=str(e))
            await message.answer(loc.get("commands.quality.invalid_range", lang))
        except Exception as e:
            logger.error("quality_error", telegram_id=message.from_user.id, error=str(e))
            await message.answer(loc.get("errors.generic", lang))
