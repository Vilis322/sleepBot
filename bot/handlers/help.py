from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from localization import LocalizationService
from utils.logger import get_logger

logger = get_logger(__name__)

router = Router(name="help")


@router.message(Command("help"))
async def cmd_help(message: Message, lang: str, loc: LocalizationService) -> None:
    """Handle /help command.

    Args:
        message: Telegram message
        lang: User's language code
        loc: Localization service
    """
    title = loc.get("commands.help.title", lang)
    commands_list = loc.get("commands.help.commands_list", lang)

    help_text = f"{title}\n\n{commands_list}"

    await message.answer(help_text)

    logger.info("help_command", telegram_id=message.from_user.id)
