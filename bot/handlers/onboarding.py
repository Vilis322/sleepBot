from datetime import time

import pytz
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from timezonefinder import TimezoneFinder

from bot.keyboards.inline import get_timezone_popular_keyboard
from bot.keyboards.reply import get_timezone_location_keyboard
from bot.states.onboarding import OnboardingStates
from database import get_session
from localization import LocalizationService
from services.user_service import UserService
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="onboarding")

tf = TimezoneFinder()


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

        # Ask for timezone with location keyboard
        prompt = loc.get("commands.start.onboarding.timezone_location_prompt", lang)
        keyboard = get_timezone_location_keyboard(loc, lang)
        await message.answer(prompt, reply_markup=keyboard)
        await state.set_state(OnboardingStates.waiting_for_timezone_location)

        logger.info("onboarding_target_hours_set", telegram_id=message.from_user.id, target_hours=target_hours)

    except ValueError:
        # Invalid format or out of range
        error_msg = loc.get("commands.start.onboarding.invalid_hours", lang)
        await message.answer(error_msg)


@router.message(OnboardingStates.waiting_for_timezone_location, F.location)
async def process_timezone_location(
    message: Message, state: FSMContext, lang: str, loc: LocalizationService
) -> None:
    """Process location message to auto-detect timezone.

    Args:
        message: Telegram message with location
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    lat = message.location.latitude
    lng = message.location.longitude
    timezone_str = tf.timezone_at(lat=lat, lng=lng)

    if timezone_str:
        detected_msg = loc.get("commands.start.onboarding.timezone_detected", lang).format(
            timezone=timezone_str
        )
        await message.answer(detected_msg, reply_markup=ReplyKeyboardRemove())
        await _complete_onboarding_with_timezone(message, state, lang, loc, timezone_str)
    else:
        failed_msg = loc.get("commands.start.onboarding.timezone_location_failed", lang)
        # Remove reply keyboard, then show popular inline keyboard
        await message.answer(failed_msg, reply_markup=ReplyKeyboardRemove())
        prompt = loc.get("commands.start.onboarding.timezone_popular_prompt", lang)
        keyboard = get_timezone_popular_keyboard(loc, lang)
        await message.answer(prompt, reply_markup=keyboard)
        await state.set_state(OnboardingStates.waiting_for_timezone_popular)


@router.message(OnboardingStates.waiting_for_timezone_location, F.text)
async def process_timezone_skip_location(
    message: Message, state: FSMContext, lang: str, loc: LocalizationService
) -> None:
    """User chose manual timezone selection instead of sharing location.

    Args:
        message: Telegram message
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    # Remove reply keyboard first, then show inline keyboard
    await message.answer(
        loc.get("commands.start.onboarding.timezone_popular_prompt", lang),
        reply_markup=ReplyKeyboardRemove(),
    )
    keyboard = get_timezone_popular_keyboard(loc, lang)
    prompt = loc.get("commands.start.onboarding.timezone_popular_prompt", lang)
    await message.answer(prompt, reply_markup=keyboard)
    await state.set_state(OnboardingStates.waiting_for_timezone_popular)


@router.callback_query(OnboardingStates.waiting_for_timezone_popular, F.data.startswith("tz_"))
async def process_timezone_popular_callback(
    callback: CallbackQuery, state: FSMContext, lang: str, loc: LocalizationService
) -> None:
    """Process popular timezone inline button press.

    Args:
        callback: Callback query from inline button
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    await callback.answer()
    data = callback.data

    if data == "tz_other":
        # Switch to manual input
        prompt = loc.get("commands.start.onboarding.timezone_manual_prompt", lang)
        await callback.message.edit_text(prompt)
        await state.set_state(OnboardingStates.waiting_for_timezone_manual)
        return

    # Extract IANA timezone id (remove "tz_" prefix)
    timezone_str = data[3:]

    confirmed_msg = loc.get("commands.start.onboarding.timezone_confirmed", lang).format(
        timezone=timezone_str
    )
    await callback.message.edit_text(confirmed_msg)
    await _complete_onboarding_with_timezone(callback.message, state, lang, loc, timezone_str)


@router.message(OnboardingStates.waiting_for_timezone_popular, F.text)
async def process_timezone_popular_text(
    message: Message, state: FSMContext, lang: str, loc: LocalizationService
) -> None:
    """Handle unexpected text in popular timezone state — prompt to use buttons.

    Args:
        message: Telegram message
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    hint = loc.get("commands.start.onboarding.timezone_use_buttons", lang)
    await message.answer(hint)


@router.message(OnboardingStates.waiting_for_timezone_manual, F.text)
async def process_timezone_manual(
    message: Message, state: FSMContext, lang: str, loc: LocalizationService
) -> None:
    """Process manual IANA timezone string input.

    Args:
        message: Telegram message
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    timezone_str = message.text.strip()

    try:
        pytz.timezone(timezone_str)
    except pytz.exceptions.UnknownTimeZoneError:
        error_msg = loc.get("commands.start.onboarding.invalid_timezone", lang)
        await message.answer(error_msg)
        return

    confirmed_msg = loc.get("commands.start.onboarding.timezone_confirmed", lang).format(
        timezone=timezone_str
    )
    await message.answer(confirmed_msg)
    await _complete_onboarding_with_timezone(message, state, lang, loc, timezone_str)


async def _complete_onboarding_with_timezone(
    message: Message,
    state: FSMContext,
    lang: str,
    loc: LocalizationService,
    timezone_str: str,
) -> None:
    """Complete onboarding after timezone is determined.

    Args:
        message: Telegram message to reply to
        state: FSM context with onboarding data
        lang: User's language code
        loc: Localization service
        timezone_str: Validated IANA timezone string
    """
    data = await state.get_data()
    bedtime = data.get("bedtime")
    waketime = data.get("waketime")
    target_hours = data.get("target_hours")

    async for session in get_session():
        try:
            user_service = UserService(session)
            db_user = await user_service.get_user_by_telegram_id(message.chat.id)

            if db_user:
                await user_service.update_timezone(db_user, timezone_str)
                await user_service.complete_onboarding(
                    db_user,
                    target_bedtime=bedtime,
                    target_wake_time=waketime,
                    target_sleep_hours=target_hours,
                )

                await state.clear()

                completion_msg = loc.get("commands.start.onboarding.completed", lang)
                await message.answer(completion_msg)

                logger.info(
                    "onboarding_completed",
                    telegram_id=message.chat.id,
                    timezone=timezone_str,
                )

        except Exception as e:
            logger.error("onboarding_completion_error", telegram_id=message.chat.id, error=str(e))
            await message.answer(loc.get("errors.generic", lang))
            await state.clear()

        await session.commit()
        break
