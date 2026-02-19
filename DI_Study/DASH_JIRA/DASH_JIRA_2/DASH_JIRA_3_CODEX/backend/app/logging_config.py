from __future__ import annotations

from logging.config import dictConfig


def configure_logging() -> None:
    """Apply structured logging defaults for the API process."""

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "loggers": {
                "jira_monitor": {
                    "handlers": ["console"],
                    "level": "INFO",
                    "propagate": False,
                },
            },
            "root": {
                "handlers": ["console"],
                "level": "WARNING",
            },
        }
    )
