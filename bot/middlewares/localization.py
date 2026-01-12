from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from database import get_db_session
from localization import localization
from services.user_service import UserService
from utils.logger import get_logger

logger = get_logger(__name__)


class LocalizationMiddleware(BaseMiddleware):
    """Middleware for automatic localization based on user's language preference."""

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        """Process update and inject localization.

        Args:
            handler: Next handler in chain
            event: Telegram update (Message or CallbackQuery)
            data: Handler data

        Returns:
            Handler result
        """
        # Get user from event
        user = event.from_user
        if not user:
            # Fallback to English if no user info
            data["lang"] = "en"
            data["loc"] = localization
            return await handler(event, data)

        # Get user's language from database
        session = await get_db_session()
        try:
            user_service = UserService(session)
            db_user = await user_service.get_user_by_telegram_id(user.id)

            if db_user:
                lang = db_user.language_code
            else:
                # New user - use Telegram's language or default to English
                lang = user.language_code if user.language_code in ["en", "ru", "et"] else "en"

            data["lang"] = lang
            data["loc"] = localization

            logger.debug(
                "localization_middleware",
                telegram_id=user.id,
                language=lang,
            )
        except Exception as e:
            logger.error(
                "localization_middleware_error",
                telegram_id=user.id,
                error=str(e),
            )
            # Fallback to English on error
            data["lang"] = "en"
            data["loc"] = localization
        finally:
            await session.close()

        return await handler(event, data)
