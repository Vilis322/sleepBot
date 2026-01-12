from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import get_db_session
from localization import LocalizationService
from services.sleep_service import SleepService
from services.user_service import UserService
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="wake")


@router.message(Command("wake"))
async def cmd_wake(message: Message, lang: str, loc: LocalizationService) -> None:
    """Handle /wake command - end sleep tracking and show statistics.

    Args:
        message: Telegram message
        lang: User's language code
        loc: Localization service
    """
    if not message.from_user:
        return

    session = await get_db_session()
    try:
        user_service = UserService(session)
        sleep_service = SleepService(session)

        db_user = await user_service.get_user_by_telegram_id(message.from_user.id)
        if not db_user:
            await message.answer(loc.get("errors.generic", lang))
            return

        # Check if there's an active session
        active_session = await sleep_service.get_active_session(db_user)

        if not active_session:
            # No active session
            no_session_msg = loc.get("commands.wake.no_active_session", lang)
            await message.answer(no_session_msg)
            logger.warning("no_sleep_session", telegram_id=message.from_user.id)
            return

        # End the session
        completed_session = await sleep_service.end_sleep_session(db_user)

        if not completed_session:
            await message.answer(loc.get("errors.generic", lang))
            return

        # Format times
        sleep_time = sleep_service.format_time_for_user(completed_session.sleep_start, db_user)
        wake_time = sleep_service.format_time_for_user(completed_session.sleep_end, db_user)

        # Format duration
        hours, minutes = sleep_service.format_duration(completed_session.duration_hours or 0)

        # Calculate goal comparison if user has goals
        goal_comparison = ""
        if db_user.target_sleep_hours:
            percentage = sleep_service.calculate_goal_percentage(db_user, completed_session)
            if percentage is not None:
                if percentage >= 90:
                    goal_comparison = loc.get(
                        "commands.wake.goal_met",
                        lang,
                        duration=hours,
                        minutes=minutes,
                        percentage=percentage,
                        target_hours=db_user.target_sleep_hours,
                    )
                else:
                    goal_comparison = loc.get(
                        "commands.wake.goal_not_met",
                        lang,
                        duration=hours,
                        minutes=minutes,
                        percentage=percentage,
                        target_hours=db_user.target_sleep_hours,
                    )
        else:
            goal_comparison = loc.get("commands.wake.no_goal", lang)

        # Send completion message
        completion_msg = loc.get(
            "commands.wake.completed",
            lang,
            sleep_time=sleep_time,
            wake_time=wake_time,
            duration=hours,
            minutes=minutes,
            goal_comparison=goal_comparison,
        )

        await message.answer(completion_msg, parse_mode="HTML")

        logger.info(
            "wake_completed",
            telegram_id=message.from_user.id,
            session_id=completed_session.id,
            duration=completed_session.duration_hours,
        )

        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error("wake_error", telegram_id=message.from_user.id, error=str(e))
        await message.answer(loc.get("errors.generic", lang))
    finally:
        await session.close()
