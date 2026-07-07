"""Structured logging configuration via structlog."""
import logging
import sys

import structlog

from app.core.config import settings


def configure_logging() -> None:
    """Configure structlog + stdlib logging. JSON in prod, pretty console in dev."""
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")

    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    renderer = (
        structlog.processors.JSONRenderer()
        if settings.ENVIRONMENT == "production"
        else structlog.dev.ConsoleRenderer()
    )
    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "agentforge") -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
