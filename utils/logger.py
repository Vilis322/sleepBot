import logging
import sys
from pathlib import Path
from typing import Any

import structlog
from colorama import Fore, Style, init

from config import settings

# Initialize colorama for Windows compatibility
init(autoreset=True)


def add_color_to_level(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Add color to log level in development mode."""
    level = event_dict.get("level", "").upper()

    color_map = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    if level in color_map:
        event_dict["level"] = f"{color_map[level]}{level}{Style.RESET_ALL}"

    return event_dict


def setup_logging() -> None:
    """Configure structured logging with different settings for dev/prod."""

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Disable SQLAlchemy verbose logging (keep only warnings and errors)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)

    # Processors common to both dev and prod
    common_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.is_production:
        # Production: JSON logs for parsing (PM2, CloudWatch, etc.)
        processors = common_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Human-readable colored logs
        processors = common_processors + [
            add_color_to_level,
            structlog.processors.format_exc_info,
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Filter out DEBUG logs in production
    if settings.is_production:
        processors.insert(0, structlog.stdlib.filter_by_level)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structlog logger

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("user_registered", user_id=12345, username="john")
        >>> logger.error("database_error", error=str(e), query=query)
    """
    return structlog.get_logger(name)


# Initialize logging on module import
setup_logging()
