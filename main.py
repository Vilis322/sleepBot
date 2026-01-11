import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.handlers import help, language, note, onboarding, quality, sleep, start, stats, wake
from bot.middlewares import LocalizationMiddleware
from config import settings
from database import close_database
from utils.logger import get_logger

logger = get_logger(__name__)


async def main() -> None:
    """Main application entry point."""
    logger.info("bot_starting", environment=settings.environment)

    # Initialize bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Initialize dispatcher
    dp = Dispatcher()

    # Register middlewares
    dp.message.middleware(LocalizationMiddleware())
    dp.callback_query.middleware(LocalizationMiddleware())

    # Register routers
    dp.include_router(start.router)
    dp.include_router(onboarding.router)
    dp.include_router(help.router)
    dp.include_router(language.router)
    dp.include_router(sleep.router)
    dp.include_router(wake.router)
    dp.include_router(quality.router)
    dp.include_router(note.router)
    dp.include_router(stats.router)

    logger.info("bot_handlers_registered", routers_count=9)

    try:
        # Start polling
        logger.info("bot_polling_started")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error("bot_polling_error", error=str(e))
        raise
    finally:
        # Cleanup
        await bot.session.close()
        await close_database()
        logger.info("bot_stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("bot_shutdown_requested")
        sys.exit(0)
    except Exception as e:
        logger.error("bot_fatal_error", error=str(e))
        sys.exit(1)
