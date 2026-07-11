"""
Logging configuration for the application.
Configures Loguru to handle all logs and intercept standard library logging.
"""

import logging
import sys
from loguru import logger
from app.config.settings import settings


class InterceptHandler(logging.Handler):
    """
    Custom handler to intercept standard library logging messages and redirect them to Loguru.
    Reference: https://loguru.readthedocs.io/en/stable/resources/recipes.html#intercepting-py-logging-messages
    """
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where the logged message originated
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    """
    Removes default logging handlers, intercepts logs of web servers, and configures Loguru.
    """
    # Intercept standard library logging on root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Intercept logs from uvicorn, gunicorn, etc.
    loggers = (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "fastapi",
    )
    for logger_name in loggers:
        mod_logger = logging.getLogger(logger_name)
        mod_logger.handlers = [InterceptHandler()]
        mod_logger.propagate = False

    # Configure Loguru format and output
    log_level = "DEBUG" if settings.DEBUG else "INFO"
    logger.remove()
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    logger.info("Loguru logging configured successfully.")
