"""Logging configuration using Loguru."""

import sys
from loguru import logger

from oagent.config.settings import settings


def setup_logging() -> None:
    """Configure logging with Loguru."""
    # Remove default handler
    logger.remove()

    # Console handler
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.log_level,
        colorize=True,
    )

    # File handler (if configured)
    if settings.log_file:
        logger.add(
            settings.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level=settings.log_level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
        )

    logger.info(f"Logging configured with level: {settings.log_level}")