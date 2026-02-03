from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import get_language_keyboard
from bot.states.onboarding import OnboardingStates
from database import get_session
from localization import LocalizationService
from services.user_service import UserService
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message, state: FSMContext, lang: str, loc: LocalizationService
) -> None:
    """Handle /start command.

    Args:
        message: Telegram message
        state: FSM context
        lang: User's language code
        loc: Localization service
    """
    user = message.from_user
    if not user:
        return

    async for session in get_session():
        try:
            user_service = UserService(session)
            db_user, is_created = await user_service.get_or_create_user(
                telegram_id=user.id,
                language_code=user.language_code,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )

            if is_created or not db_user.is_onboarded:
                # Show language selection for new/non-onboarded users
                welcome_text = loc.get("commands.start.welcome", lang)
                description = loc.get("commands.start.description", lang)
                language_prompt = loc.get("commands.start.select_language", lang)

                await message.answer(f"{welcome_text}\n\n{description}")
                await message.answer(language_prompt, reply_markup=get_language_keyboard())

                logger.info(
                    "user_started",
                    telegram_id=user.id,
                    new_user=is_created,
                )
            else:
                # Existing user - show welcome back message
                welcome_text = loc.get("commands.start.welcome", lang)
                help_text = loc.get("commands.help.commands_list", lang)

                await message.answer(f"{welcome_text}\n\n{help_text}")

                logger.debug("user_returning", telegram_id=user.id)

        except Exception as e:
            logger.error("start_error", telegram_id=user.id, error=str(e), error_type=type(e).__name__, error_repr=repr(e))
            import traceback
            traceback.print_exc()
            await message.answer(loc.get("errors.generic", lang))

        # Commit before break - otherwise changes won't be saved
        await session.commit()
        break


@router.callback_query(F.data.startswith("lang_"))
async def handle_language_selection(
    callback: CallbackQuery, state: FSMContext, loc: LocalizationService
) -> None:
    """Handle language selection from inline keyboard.

    Args:
        callback: Callback query
        state: FSM context
        loc: Localization service
    """
    if not callback.data or not callback.from_user:
        return

    selected_lang = callback.data.split("_")[1]  # Extract language code

    async for session in get_session():
        try:
            user_service = UserService(session)
            db_user = await user_service.get_user_by_telegram_id(callback.from_user.id)

            if db_user:
                # Update language
                await user_service.update_language(db_user, selected_lang)

                # Start onboarding if not completed
                if not db_user.is_onboarded:
                    # Ask for bedtime
                    bedtime_question = loc.get(
                        "commands.start.onboarding.question_bedtime", selected_lang
                    )
                    await callback.message.edit_text(bedtime_question)
                    await state.set_state(OnboardingStates.waiting_for_bedtime)
                    await state.update_data(language=selected_lang)
                else:
                    # Language changed for existing user
                    changed_msg = loc.get("commands.language.changed", selected_lang)
                    await callback.message.edit_text(changed_msg)

                await callback.answer()

                logger.info(
                    "lang_selected",
                    telegram_id=callback.from_user.id,
                    lang=selected_lang,
                )

        except Exception as e:
            logger.error(
                "lang_error",
                telegram_id=callback.from_user.id,
                error=str(e),
            )
            await callback.answer(loc.get("errors.generic", selected_lang), show_alert=True)

        # Commit before break - otherwise changes won't be saved
        await session.commit()
        break
