"""Centralized logging configuration for Mneme."""

from __future__ import annotations

import logging
from typing import Any


class LogContextFilter(logging.Filter):
    """Ensure expected structured fields always exist on log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = getattr(record, "run_id", "-")
        record.source = getattr(record, "source", "-")
        record.stage = getattr(record, "stage", "-")
        return True


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logging with stable contextual fields."""
    handler = logging.StreamHandler()
    handler.addFilter(LogContextFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] "
            "run_id=%(run_id)s source=%(source)s stage=%(stage)s %(message)s"
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Return a module logger."""
    return logging.getLogger(name)


def bind_logger(logger: logging.Logger, **context: Any) -> logging.LoggerAdapter[logging.Logger]:
    """Bind stable context to a logger."""
    return logging.LoggerAdapter(logger, dict(context))
