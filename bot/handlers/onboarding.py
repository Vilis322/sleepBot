from datetime import time

import pytz
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states.onboarding import OnboardingStates
from database import get_session
from localization import LocalizationService
from services.user_service import UserService
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="onboarding")


@router.message(OnboardingStates.waiting_for_bedtime)
async def process_bedtime(message: Message, state: FSMContext, lang: str, loc: LocalizationService) -> None:
    """Process bedtime input during onboarding.

    Args:
        message: Telegram message
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    try:
        # Parse time (HH:MM format)
        time_parts = message.text.strip().split(":")
        if len(time_parts) != 2:
            raise ValueError("Invalid time format")

        hours, minutes = int(time_parts[0]), int(time_parts[1])
        bedtime = time(hour=hours, minute=minutes)

        # Save to state
        await state.update_data(bedtime=bedtime)

        # Ask for wake time
        waketime_question = loc.get("commands.start.onboarding.question_waketime", lang)
        await message.answer(waketime_question)
        await state.set_state(OnboardingStates.waiting_for_waketime)

        logger.info("onboarding_bedtime_set", telegram_id=message.from_user.id, bedtime=str(bedtime))

    except (ValueError, IndexError):
        # Invalid format
        error_msg = loc.get("commands.start.onboarding.invalid_time", lang)
        await message.answer(error_msg)


@router.message(OnboardingStates.waiting_for_waketime)
async def process_waketime(message: Message, state: FSMContext, lang: str, loc: LocalizationService) -> None:
    """Process wake time input during onboarding.

    Args:
        message: Telegram message
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    try:
        # Parse time (HH:MM format)
        time_parts = message.text.strip().split(":")
        if len(time_parts) != 2:
            raise ValueError("Invalid time format")

        hours, minutes = int(time_parts[0]), int(time_parts[1])
        waketime = time(hour=hours, minute=minutes)

        # Save to state
        await state.update_data(waketime=waketime)

        # Ask for target hours
        hours_question = loc.get("commands.start.onboarding.question_target_hours", lang)
        await message.answer(hours_question)
        await state.set_state(OnboardingStates.waiting_for_target_hours)

        logger.info("onboarding_waketime_set", telegram_id=message.from_user.id, waketime=str(waketime))

    except (ValueError, IndexError):
        # Invalid format
        error_msg = loc.get("commands.start.onboarding.invalid_time", lang)
        await message.answer(error_msg)


@router.message(OnboardingStates.waiting_for_target_hours)
async def process_target_hours(message: Message, state: FSMContext, lang: str, loc: LocalizationService) -> None:
    """Process target sleep hours input during onboarding.

    Args:
        message: Telegram message
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    try:
        target_hours = int(message.text.strip())

        if not (1 <= target_hours <= 24):
            raise ValueError("Hours out of range")

        # Save to state
        await state.update_data(target_hours=target_hours)

        # Ask for timezone
        timezone_question = loc.get("commands.start.onboarding.question_timezone", lang)
        await message.answer(timezone_question)
        await state.set_state(OnboardingStates.waiting_for_timezone)

        logger.info("onboarding_target_hours_set", telegram_id=message.from_user.id, target_hours=target_hours)

    except ValueError:
        # Invalid format or out of range
        error_msg = loc.get("commands.start.onboarding.invalid_hours", lang)
        await message.answer(error_msg)


@router.message(OnboardingStates.waiting_for_timezone)
async def process_timezone(message: Message, state: FSMContext, lang: str, loc: LocalizationService) -> None:
    """Process timezone input during onboarding.

    Args:
        message: Telegram message
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    timezone_str = message.text.strip()

    # Validate timezone
    try:
        pytz.timezone(timezone_str)
    except pytz.exceptions.UnknownTimeZoneError:
        error_msg = loc.get("commands.start.onboarding.invalid_timezone", lang)
        await message.answer(error_msg)
        return

    # Get all data from state
    data = await state.get_data()
    bedtime = data.get("bedtime")
    waketime = data.get("waketime")
    target_hours = data.get("target_hours")

    # Complete onboarding
    async for session in get_session():
        try:
            user_service = UserService(session)
            db_user = await user_service.get_user_by_telegram_id(message.from_user.id)

            if db_user:
                # Update timezone
                await user_service.update_timezone(db_user, timezone_str)

                # Complete onboarding with goals
                await user_service.complete_onboarding(
                    db_user,
                    target_bedtime=bedtime,
                    target_wake_time=waketime,
                    target_sleep_hours=target_hours,
                )

                # Clear state
                await state.clear()

                # Send completion message
                completion_msg = loc.get("commands.start.onboarding.completed", lang)
                await message.answer(completion_msg)

                logger.info(
                    "onboarding_completed",
                    telegram_id=message.from_user.id,
                    timezone=timezone_str,
                )

        except Exception as e:
            logger.error("onboarding_completion_error", telegram_id=message.from_user.id, error=str(e))
            await message.answer(loc.get("errors.generic", lang))
            await state.clear()
