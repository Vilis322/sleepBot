from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import get_quality_rating_keyboard, get_quality_confirmation_keyboard
from bot.states.onboarding import QualityStates
from database import get_session
from localization import LocalizationService
from services.sleep_service import SleepService, SessionUpdateValidation
from services.user_service import UserService
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="quality")


@router.message(Command("quality"))
async def cmd_quality(message: Message, state: FSMContext, lang: str, loc: LocalizationService) -> None:
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

    # If no parameter provided, show rating keyboard
    if len(parts) < 2:
        async for session in get_session():
            try:
                user_service = UserService(session)
                sleep_service = SleepService(session)

                db_user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not db_user:
                    await message.answer(loc.get("errors.generic", lang))
                    await session.commit()
                    break

                # Check if there's a completed session to rate
                last_session = await sleep_service.get_last_completed_session(db_user)
                if not last_session:
                    no_session_msg = loc.get("commands.quality.no_last_session", lang)
                    await message.answer(no_session_msg)
                    await session.commit()
                    break

                # Show rating selection keyboard
                select_msg = loc.get("commands.quality.select_rating", lang)
                custom_msg = loc.get("commands.quality.enter_custom", lang)
                await message.answer(f"{select_msg}\n\n{custom_msg}", reply_markup=get_quality_rating_keyboard())

                await session.commit()
                break

            except Exception as e:
                logger.error("quality_keyboard_error", telegram_id=message.from_user.id, error=str(e))
                await message.answer(loc.get("errors.generic", lang))
                await session.commit()
                break
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
                # Commit before break - otherwise changes won't be saved
                await session.commit()
                break

            # Get last completed session
            last_session = await sleep_service.get_last_completed_session(db_user)

            if not last_session:
                no_session_msg = loc.get("commands.quality.no_last_session", lang)
                await message.answer(no_session_msg)
                logger.info("quality_no_session", telegram_id=message.from_user.id)
                # Commit before break - otherwise changes won't be saved
                await session.commit()
                break

            # Validate session update
            has_existing_data = last_session.quality_rating is not None
            validation, hours_since_wake = sleep_service.validate_session_update(
                last_session, "quality", has_existing_data
            )

            if validation == SessionUpdateValidation.ALLOW:
                # First time rating - save directly
                await sleep_service.add_quality_rating(last_session, rating)

                # Check if note exists, suggest adding one if not
                if last_session.note is None:
                    success_msg = loc.get("commands.quality.saved_suggest_note", lang, rating=rating)
                else:
                    success_msg = loc.get("commands.quality.saved", lang, rating=rating)

                await message.answer(success_msg)

                logger.info(
                    "quality_rated",
                    telegram_id=message.from_user.id,
                    session_id=last_session.id,
                    rating=rating,
                )

            elif validation == SessionUpdateValidation.ASK_CONFIRMATION:
                # Session is fresh but already has rating - ask confirmation
                confirm_msg = loc.get(
                    "commands.quality.confirm_overwrite",
                    lang,
                    rating=last_session.quality_rating,
                    new_rating=rating,
                )
                await message.answer(
                    confirm_msg,
                    reply_markup=get_quality_confirmation_keyboard(rating, loc, lang),
                )

                # Save rating in FSM state for confirmation
                await state.set_state(QualityStates.waiting_for_confirmation)
                await state.update_data(pending_rating=rating)

            elif validation == SessionUpdateValidation.SHOW_WARNING:
                # Session is old - show warning
                time_ago = sleep_service.format_time_ago(hours_since_wake)
                warning_msg = loc.get(
                    "commands.quality.old_session_warning",
                    lang,
                    time_ago=time_ago,
                    rating=rating,
                )
                await message.answer(
                    warning_msg,
                    reply_markup=get_quality_confirmation_keyboard(rating, loc, lang),
                )

                # Save rating in FSM state for confirmation
                await state.set_state(QualityStates.waiting_for_confirmation)
                await state.update_data(pending_rating=rating)

        except ValueError as e:
            logger.error("quality_error", telegram_id=message.from_user.id, error=str(e))
            await message.answer(loc.get("commands.quality.invalid_range", lang))
        except Exception as e:
            logger.error("quality_error", telegram_id=message.from_user.id, error=str(e))
            await message.answer(loc.get("errors.generic", lang))

        # Commit before break - otherwise changes won't be saved
        await session.commit()
        break


@router.callback_query(F.data.startswith("quality_rate_"))
async def handle_quality_rating_callback(callback: CallbackQuery, state: FSMContext, lang: str, loc: LocalizationService) -> None:
    """Handle quality rating selection from keyboard.

    Args:
        callback: Callback query
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    if not callback.data or not callback.from_user or not callback.message:
        return

    # Extract rating from callback data
    rating = int(callback.data.split("_")[-1])

    async for session in get_session():
        try:
            user_service = UserService(session)
            sleep_service = SleepService(session)

            db_user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not db_user:
                await callback.answer(loc.get("errors.generic", lang), show_alert=True)
                await session.commit()
                break

            # Get last completed session
            last_session = await sleep_service.get_last_completed_session(db_user)
            if not last_session:
                no_session_msg = loc.get("commands.quality.no_last_session", lang)
                await callback.message.edit_text(no_session_msg)
                await callback.answer()
                await session.commit()
                break

            # Validate session update
            has_existing_data = last_session.quality_rating is not None
            validation, hours_since_wake = sleep_service.validate_session_update(
                last_session, "quality", has_existing_data
            )

            if validation == SessionUpdateValidation.ALLOW:
                # First time rating - save directly
                await sleep_service.add_quality_rating(last_session, float(rating))

                # Check if note exists, suggest adding one if not
                if last_session.note is None:
                    success_msg = loc.get("commands.quality.saved_suggest_note", lang, rating=rating)
                else:
                    success_msg = loc.get("commands.quality.saved", lang, rating=rating)

                await callback.message.edit_text(success_msg)
                await callback.answer()

                logger.info(
                    "quality_rated_callback",
                    telegram_id=callback.from_user.id,
                    session_id=last_session.id,
                    rating=rating,
                )

            elif validation == SessionUpdateValidation.ASK_CONFIRMATION:
                # Session is fresh but already has rating - ask confirmation
                confirm_msg = loc.get(
                    "commands.quality.confirm_overwrite",
                    lang,
                    rating=last_session.quality_rating,
                    new_rating=rating,
                )
                await callback.message.edit_text(
                    confirm_msg,
                    reply_markup=get_quality_confirmation_keyboard(rating, loc, lang),
                )
                await callback.answer()

                # Save rating in FSM state for confirmation
                await state.set_state(QualityStates.waiting_for_confirmation)
                await state.update_data(pending_rating=rating)

            elif validation == SessionUpdateValidation.SHOW_WARNING:
                # Session is old - show warning
                time_ago = sleep_service.format_time_ago(hours_since_wake)
                warning_msg = loc.get(
                    "commands.quality.old_session_warning",
                    lang,
                    time_ago=time_ago,
                    rating=rating,
                )
                await callback.message.edit_text(
                    warning_msg,
                    reply_markup=get_quality_confirmation_keyboard(rating, loc, lang),
                )
                await callback.answer()

                # Save rating in FSM state for confirmation
                await state.set_state(QualityStates.waiting_for_confirmation)
                await state.update_data(pending_rating=rating)

        except Exception as e:
            logger.error("quality_callback_error", telegram_id=callback.from_user.id, error=str(e))
            await callback.answer(loc.get("errors.generic", lang), show_alert=True)

        await session.commit()
        break


@router.callback_query(F.data.startswith("quality_confirm_"))
async def handle_quality_confirm(callback: CallbackQuery, state: FSMContext, lang: str, loc: LocalizationService) -> None:
    """Handle quality rating confirmation.

    Args:
        callback: Callback query
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    if not callback.data or not callback.from_user or not callback.message:
        return

    # Extract rating from callback data
    rating_str = callback.data.replace("quality_confirm_", "")
    rating = float(rating_str)

    async for session in get_session():
        try:
            user_service = UserService(session)
            sleep_service = SleepService(session)

            db_user = await user_service.get_user_by_telegram_id(callback.from_user.id)
            if not db_user:
                await callback.answer(loc.get("errors.generic", lang), show_alert=True)
                await session.commit()
                break

            # Get last completed session
            last_session = await sleep_service.get_last_completed_session(db_user)
            if not last_session:
                no_session_msg = loc.get("commands.quality.no_last_session", lang)
                await callback.message.edit_text(no_session_msg)
                await callback.answer()
                await state.clear()
                await session.commit()
                break

            # Save rating
            await sleep_service.add_quality_rating(last_session, rating)

            # Check if note exists, suggest adding one if not
            if last_session.note is None:
                success_msg = loc.get("commands.quality.saved_suggest_note", lang, rating=rating)
            else:
                success_msg = loc.get("commands.quality.saved", lang, rating=rating)

            await callback.message.edit_text(success_msg)
            await callback.answer()

            logger.info(
                "quality_confirmed",
                telegram_id=callback.from_user.id,
                session_id=last_session.id,
                rating=rating,
            )

            # Clear FSM state
            await state.clear()

        except Exception as e:
            logger.error("quality_confirm_error", telegram_id=callback.from_user.id, error=str(e))
            await callback.answer(loc.get("errors.generic", lang), show_alert=True)
            await state.clear()

        await session.commit()
        break


@router.callback_query(F.data == "quality_cancel")
async def handle_quality_cancel(callback: CallbackQuery, state: FSMContext, lang: str, loc: LocalizationService) -> None:
    """Handle quality rating cancellation.

    Args:
        callback: Callback query
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    if not callback.from_user or not callback.message:
        return

    cancel_msg = loc.get("commands.quality.cancelled", lang)
    await callback.message.edit_text(cancel_msg)
    await callback.answer()

    # Clear FSM state
    await state.clear()

    logger.info("quality_cancelled", telegram_id=callback.from_user.id)
