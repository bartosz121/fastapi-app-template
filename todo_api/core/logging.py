"""
https://www.structlog.org/en/stable/standard-library.html#rendering-using-structlog-based-formatters-within-logging
"""

import logging
import logging.config
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from todo_api.core.config import Environment


def _get_renderer(
    environment: Environment,
) -> structlog.processors.JSONRenderer | structlog.dev.ConsoleRenderer:
    if environment.is_production:
        return structlog.processors.JSONRenderer()
    return structlog.dev.ConsoleRenderer(colors=True)


def _configure_std_logging(
    log_level: str,
    environment: Environment,
    enabled_loggers: list[str],
) -> None:
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": True,
            "formatters": {
                "todo_api": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processors": [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        _get_renderer(environment),
                    ],
                    "foreign_pre_chain": [
                        structlog.contextvars.merge_contextvars,
                        structlog.stdlib.add_log_level,
                        structlog.stdlib.add_logger_name,
                        structlog.stdlib.PositionalArgumentsFormatter(),
                        structlog.stdlib.ExtraAdder(),
                        structlog.processors.TimeStamper(fmt="iso", utc=True),
                        structlog.processors.UnicodeDecoder(),
                        structlog.processors.StackInfoRenderer(),
                        structlog.processors.format_exc_info,
                    ],
                },
            },
            "handlers": {
                "default": {
                    "level": log_level,
                    "class": "logging.StreamHandler",
                    "formatter": "todo_api",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": log_level,
                    "propagate": False,
                },
                **{
                    logger: {
                        "handlers": [],
                        "propagate": True,
                    }
                    for logger in enabled_loggers
                },
            },
        }
    )


def _configure_structlog() -> None:
    structlog.configure_once(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.UnicodeDecoder(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def configure(
    log_level: str,
    environment: Environment,
    enabled_loggers: list[str],
) -> None:
    _configure_std_logging(log_level, environment, enabled_loggers)
    _configure_structlog()


__all__ = ("configure",)
