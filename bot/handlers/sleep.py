from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import get_sleep_conflict_keyboard
from database import get_session
from localization import LocalizationService
from services.sleep_service import SleepService
from services.user_service import UserService
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="sleep")


@router.message(Command("sleep"))
async def cmd_sleep(message: Message, lang: str, loc: LocalizationService) -> None:
    """Handle /sleep command - start sleep tracking.

    Args:
        message: Telegram message
        lang: User's language code
        loc: Localization service
    """
    if not message.from_user:
        return

    async for session in get_session():
        try:
            user_service = UserService(session)
            sleep_service = SleepService(session)

            db_user = await user_service.get_user_by_telegram_id(message.from_user.id)
            if not db_user:
                await message.answer(loc.get("errors.generic", lang))
                return

            # Check if there's already an active session
            active_session = await sleep_service.get_active_session(db_user)

            if active_session:
                # Calculate duration so far
                now = datetime.now()
                delta = now - active_session.sleep_start.replace(tzinfo=None)
                duration_hours = int(delta.total_seconds() / 3600)
                duration_minutes = int((delta.total_seconds() % 3600) / 60)

                # Format start time
                start_time = sleep_service.format_time_for_user(active_session.sleep_start, db_user)

                # Show conflict resolution options
                conflict_msg = loc.get("commands.sleep.already_active", lang, time=start_time)

                await message.answer(
                    conflict_msg,
                    reply_markup=get_sleep_conflict_keyboard(duration_hours, duration_minutes),
                )

                logger.info(
                    "sleep_conflict_detected",
                    telegram_id=message.from_user.id,
                    active_session_id=active_session.id,
                )

            else:
                # No active session - start new one
                new_session = await sleep_service.start_sleep_session(db_user)

                start_time = sleep_service.format_time_for_user(new_session.sleep_start, db_user)
                success_msg = loc.get("commands.sleep.started", lang, time=start_time)

                await message.answer(success_msg)

                logger.info(
                    "sleep_session_started",
                    telegram_id=message.from_user.id,
                    session_id=new_session.id,
                )

        except Exception as e:
            logger.error("sleep_command_error", telegram_id=message.from_user.id, error=str(e))
            await message.answer(loc.get("errors.generic", lang))


@router.callback_query(F.data == "sleep_save_and_start")
async def handle_sleep_save_and_start(callback: CallbackQuery, lang: str, loc: LocalizationService) -> None:
    """Handle save current session and start new one.

    Args:
        callback: Callback query
        lang: User's language code
        loc: Localization service
    """
    if not callback.from_user:
        return

    async for session in get_session():
        try:
            user_service = UserService(session)
            sleep_service = SleepService(session)

            db_user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not db_user:
                await callback.answer(loc.get("errors.generic", lang), show_alert=True)
                return

            # End current session
            completed_session = await sleep_service.end_sleep_session(db_user)
            if completed_session:
                hours, minutes = sleep_service.format_duration(completed_session.duration_hours or 0)

                # Start new session
                new_session = await sleep_service.start_sleep_session(db_user)
                start_time = sleep_service.format_time_for_user(new_session.sleep_start, db_user)

                success_msg = loc.get(
                    "commands.sleep.session_saved",
                    lang,
                    duration=hours,
                    minutes=minutes,
                    time=start_time,
                )

                await callback.message.edit_text(success_msg)
                await callback.answer()

                logger.info(
                    "sleep_save_and_start",
                    telegram_id=callback.from_user.id,
                    old_session_id=completed_session.id,
                    new_session_id=new_session.id,
                )

        except Exception as e:
            logger.error("sleep_save_and_start_error", telegram_id=callback.from_user.id, error=str(e))
            await callback.answer(loc.get("errors.generic", lang), show_alert=True)


@router.callback_query(F.data == "sleep_continue")
async def handle_sleep_continue(callback: CallbackQuery, lang: str, loc: LocalizationService) -> None:
    """Handle continue current session.

    Args:
        callback: Callback query
        lang: User's language code
        loc: Localization service
    """
    await callback.message.delete()
    await callback.answer(loc.get("commands.sleep.already_active_continue", lang))

    logger.info("sleep_continue", telegram_id=callback.from_user.id)


@router.callback_query(F.data == "sleep_cancel_and_start")
async def handle_sleep_cancel_and_start(callback: CallbackQuery, lang: str, loc: LocalizationService) -> None:
    """Handle cancel current session and start new one.

    Args:
        callback: Callback query
        lang: User's language code
        loc: Localization service
    """
    if not callback.from_user:
        return

    async for session in get_session():
        try:
            user_service = UserService(session)
            sleep_service = SleepService(session)

            db_user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not db_user:
                await callback.answer(loc.get("errors.generic", lang), show_alert=True)
                return

            # Cancel current session
            await sleep_service.cancel_active_session(db_user)

            # Start new session
            new_session = await sleep_service.start_sleep_session(db_user)
            start_time = sleep_service.format_time_for_user(new_session.sleep_start, db_user)

            success_msg = loc.get("commands.sleep.session_cancelled", lang, time=start_time)

            await callback.message.edit_text(success_msg)
            await callback.answer()

            logger.info(
                "sleep_cancel_and_start",
                telegram_id=callback.from_user.id,
                new_session_id=new_session.id,
            )

        except Exception as e:
            logger.error("sleep_cancel_and_start_error", telegram_id=callback.from_user.id, error=str(e))
            await callback.answer(loc.get("errors.generic", lang), show_alert=True)
