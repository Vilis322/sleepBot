from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import get_note_confirmation_keyboard
from bot.states.onboarding import NoteStates
from database import get_session
from localization import LocalizationService
from services.sleep_service import SleepService, SessionUpdateValidation
from services.user_service import UserService
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="note")


@router.message(Command("note"))
async def cmd_note(message: Message, state: FSMContext, lang: str, loc: LocalizationService) -> None:
    """Handle /note command - add note to sleep session.

    Args:
        message: Telegram message
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    if not message.from_user or not message.text:
        return

    # Extract note from command
    parts = message.text.split(maxsplit=1)

    # If no parameter provided, enter FSM state to wait for next message
    if len(parts) < 2 or not parts[1].strip():
        async for session in get_session():
            try:
                user_service = UserService(session)
                sleep_service = SleepService(session)

                db_user = await user_service.get_user_by_telegram_id(message.from_user.id)
                if not db_user:
                    await message.answer(loc.get("errors.generic", lang))
                    await session.commit()
                    break

                # Check if there's a completed session to add note to
                last_session = await sleep_service.get_last_completed_session(db_user)
                if not last_session:
                    no_session_msg = loc.get("commands.note.no_last_session", lang)
                    await message.answer(no_session_msg)
                    await session.commit()
                    break

                # Enter FSM state to wait for note text
                await state.set_state(NoteStates.waiting_for_note_text)
                waiting_msg = loc.get("commands.note.waiting_for_note", lang)
                await message.answer(waiting_msg)

                await session.commit()
                break

            except Exception as e:
                logger.error("note_fsm_error", telegram_id=message.from_user.id, error=str(e))
                await message.answer(loc.get("errors.generic", lang))
                await session.commit()
                break
        return

    note_text = parts[1].strip()

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
                no_session_msg = loc.get("commands.note.no_last_session", lang)
                await message.answer(no_session_msg)
                logger.info("note_no_session", telegram_id=message.from_user.id)
                # Commit before break - otherwise changes won't be saved
                await session.commit()
                break

            # Validate session update
            has_existing_data = last_session.note is not None
            validation, hours_since_wake = sleep_service.validate_session_update(
                last_session, "note", has_existing_data
            )

            if validation == SessionUpdateValidation.ALLOW:
                # First time adding note - save directly
                await sleep_service.add_note(last_session, note_text)

                # Check if quality rating exists, suggest adding one if not
                if last_session.quality_rating is None:
                    success_msg = loc.get("commands.note.saved_suggest_quality", lang, note=note_text)
                else:
                    success_msg = loc.get("commands.note.saved", lang, note=note_text)

                await message.answer(success_msg)

                logger.info(
                    "note_added",
                    telegram_id=message.from_user.id,
                    session_id=last_session.id,
                    is_update=False,
                )

            elif validation == SessionUpdateValidation.ASK_CONFIRMATION:
                # Session is fresh but already has note - ask confirmation
                confirm_msg = loc.get(
                    "commands.note.confirm_overwrite",
                    lang,
                    existing_note=last_session.note,
                    new_note=note_text,
                )
                await message.answer(
                    confirm_msg,
                    reply_markup=get_note_confirmation_keyboard(loc, lang),
                )

                # Save note in FSM state for confirmation
                await state.set_state(NoteStates.waiting_for_note_confirmation)
                await state.update_data(pending_note=note_text)

            elif validation == SessionUpdateValidation.SHOW_WARNING:
                # Session is old - show warning
                time_ago = sleep_service.format_time_ago(hours_since_wake)
                warning_msg = loc.get(
                    "commands.note.old_session_warning",
                    lang,
                    time_ago=time_ago,
                )
                await message.answer(
                    warning_msg,
                    reply_markup=get_note_confirmation_keyboard(loc, lang),
                )

                # Save note in FSM state for confirmation
                await state.set_state(NoteStates.waiting_for_note_confirmation)
                await state.update_data(pending_note=note_text)

        except ValueError as e:
            logger.error("note_validation_error", telegram_id=message.from_user.id, error=str(e))
            await message.answer(loc.get("commands.note.empty", lang))
        except Exception as e:
            logger.error("note_command_error", telegram_id=message.from_user.id, error=str(e))
            await message.answer(loc.get("errors.generic", lang))

        # Commit before break - otherwise changes won't be saved
        await session.commit()
        break


@router.message(NoteStates.waiting_for_note_text)
async def process_note_text(message: Message, state: FSMContext, lang: str, loc: LocalizationService) -> None:
    """Process note text input from FSM state.

    Args:
        message: Telegram message with note text
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    if not message.from_user or not message.text:
        return

    note_text = message.text.strip()

    # Validate note text
    if not note_text:
        error_msg = loc.get("commands.note.empty", lang)
        await message.answer(error_msg)
        return

    async for session in get_session():
        try:
            user_service = UserService(session)
            sleep_service = SleepService(session)

            db_user = await user_service.get_user_by_telegram_id(message.from_user.id)
            if not db_user:
                await message.answer(loc.get("errors.generic", lang))
                await session.commit()
                break

            # Get last completed session
            last_session = await sleep_service.get_last_completed_session(db_user)
            if not last_session:
                no_session_msg = loc.get("commands.note.no_last_session", lang)
                await message.answer(no_session_msg)
                await state.clear()
                await session.commit()
                break

            # Validate session update
            has_existing_data = last_session.note is not None
            validation, hours_since_wake = sleep_service.validate_session_update(
                last_session, "note", has_existing_data
            )

            if validation == SessionUpdateValidation.ALLOW:
                # First time adding note - save directly
                await sleep_service.add_note(last_session, note_text)

                # Check if quality rating exists, suggest adding one if not
                if last_session.quality_rating is None:
                    success_msg = loc.get("commands.note.saved_suggest_quality", lang, note=note_text)
                else:
                    success_msg = loc.get("commands.note.saved", lang, note=note_text)

                await message.answer(success_msg)

                logger.info(
                    "note_added_fsm",
                    telegram_id=message.from_user.id,
                    session_id=last_session.id,
                    is_update=False,
                )

                # Clear FSM state
                await state.clear()

            elif validation == SessionUpdateValidation.ASK_CONFIRMATION:
                # Session is fresh but already has note - ask confirmation
                confirm_msg = loc.get(
                    "commands.note.confirm_overwrite",
                    lang,
                    existing_note=last_session.note,
                    new_note=note_text,
                )
                await message.answer(
                    confirm_msg,
                    reply_markup=get_note_confirmation_keyboard(loc, lang),
                )

                # Update FSM state for confirmation (change from waiting_for_note_text to waiting_for_note_confirmation)
                await state.set_state(NoteStates.waiting_for_note_confirmation)
                await state.update_data(pending_note=note_text)

            elif validation == SessionUpdateValidation.SHOW_WARNING:
                # Session is old - show warning
                time_ago = sleep_service.format_time_ago(hours_since_wake)
                warning_msg = loc.get(
                    "commands.note.old_session_warning",
                    lang,
                    time_ago=time_ago,
                )
                await message.answer(
                    warning_msg,
                    reply_markup=get_note_confirmation_keyboard(loc, lang),
                )

                # Update FSM state for confirmation (change from waiting_for_note_text to waiting_for_note_confirmation)
                await state.set_state(NoteStates.waiting_for_note_confirmation)
                await state.update_data(pending_note=note_text)

        except ValueError as e:
            logger.error("note_validation_error_fsm", telegram_id=message.from_user.id, error=str(e))
            await message.answer(loc.get("commands.note.empty", lang))
            await state.clear()
        except Exception as e:
            logger.error("note_fsm_process_error", telegram_id=message.from_user.id, error=str(e))
            await message.answer(loc.get("errors.generic", lang))
            await state.clear()

        await session.commit()
        break


@router.callback_query(F.data == "note_confirm")
async def handle_note_confirm(callback: CallbackQuery, state: FSMContext, lang: str, loc: LocalizationService) -> None:
    """Handle note confirmation.

    Args:
        callback: Callback query
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    if not callback.from_user or not callback.message:
        return

    # Get pending note from FSM data
    data = await state.get_data()
    note_text = data.get("pending_note")

    if not note_text:
        await callback.answer(loc.get("errors.generic", lang), show_alert=True)
        await state.clear()
        return

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
                no_session_msg = loc.get("commands.note.no_last_session", lang)
                await callback.message.edit_text(no_session_msg)
                await callback.answer()
                await state.clear()
                await session.commit()
                break

            # Save note
            await sleep_service.add_note(last_session, note_text)

            # Check if quality rating exists, suggest adding one if not
            if last_session.quality_rating is None:
                success_msg = loc.get("commands.note.saved_suggest_quality", lang, note=note_text)
            else:
                success_msg = loc.get("commands.note.saved", lang, note=note_text)

            await callback.message.edit_text(success_msg)
            await callback.answer()

            logger.info(
                "note_confirmed",
                telegram_id=callback.from_user.id,
                session_id=last_session.id,
            )

            # Clear FSM state
            await state.clear()

        except Exception as e:
            logger.error("note_confirm_error", telegram_id=callback.from_user.id, error=str(e))
            await callback.answer(loc.get("errors.generic", lang), show_alert=True)
            await state.clear()

        await session.commit()
        break


@router.callback_query(F.data == "note_cancel")
async def handle_note_cancel(callback: CallbackQuery, state: FSMContext, lang: str, loc: LocalizationService) -> None:
    """Handle note cancellation.

    Args:
        callback: Callback query
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    if not callback.from_user or not callback.message:
        return

    cancel_msg = loc.get("commands.note.cancelled", lang)
    await callback.message.edit_text(cancel_msg)
    await callback.answer()

    # Clear FSM state
    await state.clear()

    logger.info("note_cancelled", telegram_id=callback.from_user.id)
