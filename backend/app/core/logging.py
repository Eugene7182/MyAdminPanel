"""Structured logging helpers."""
from __future__ import annotations

import logging
import sys
from typing import Any, Dict


class ContextFilter(logging.Filter):
    """Inject correlation identifiers into log records."""

    def __init__(self) -> None:
        super().__init__()
        self.correlation_id = "unknown"

    def set_correlation_id(self, correlation_id: str) -> None:
        self.correlation_id = correlation_id

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003 - required by logging
        record.correlation_id = self.correlation_id
        return True


def configure_logging(level: str = "INFO") -> ContextFilter:
    """Configure structured logging with JSON-like formatting."""

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | corr_id=%(correlation_id)s | %(name)s | %(message)s"
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]
    context_filter = ContextFilter()
    root_logger.addFilter(context_filter)
    return context_filter


def log_extra(**kwargs: Any) -> Dict[str, Any]:
    """Return a dictionary for structured log binding."""

    return {"extra": kwargs}
