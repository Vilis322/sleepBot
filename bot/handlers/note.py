from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import get_session
from localization import LocalizationService
from services.sleep_service import SleepService
from services.user_service import UserService
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="note")


@router.message(Command("note"))
async def cmd_note(message: Message, lang: str, loc: LocalizationService) -> None:
    """Handle /note command - add note to sleep session.

    Args:
        message: Telegram message
        lang: User's language code
        loc: Localization service
    """
    if not message.from_user or not message.text:
        return

    # Extract note from command
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        error_msg = loc.get("commands.note.empty", lang)
        await message.answer(error_msg)
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

            # Check if note already exists
            has_existing_note = last_session.note is not None

            # Add/update note
            await sleep_service.add_note(last_session, note_text)

            # Choose message based on whether this is an update and if quality rating exists
            if has_existing_note:
                success_msg = loc.get("commands.note.updated", lang, note=note_text)
            elif last_session.quality_rating is None:
                # New note and no quality rating - suggest adding quality
                success_msg = loc.get("commands.note.saved_suggest_quality", lang, note=note_text)
            else:
                success_msg = loc.get("commands.note.saved", lang, note=note_text)

            await message.answer(success_msg)

            logger.info(
                "note_added",
                telegram_id=message.from_user.id,
                session_id=last_session.id,
                is_update=has_existing_note,
            )

        except ValueError as e:
            logger.error("note_validation_error", telegram_id=message.from_user.id, error=str(e))
            await message.answer(loc.get("commands.note.empty", lang))
        except Exception as e:
            logger.error("note_command_error", telegram_id=message.from_user.id, error=str(e))
            await message.answer(loc.get("errors.generic", lang))

        # Commit before break - otherwise changes won't be saved
        await session.commit()
        break
