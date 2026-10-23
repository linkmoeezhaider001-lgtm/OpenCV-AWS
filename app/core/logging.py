"""Structured JSON logging helpers."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any


_BASE_LOG_RECORD_FIELDS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "message",
    "asctime",
}


class JSONFormatter(logging.Formatter):
    """Format log records as JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": message,
            "module": record.module,
        }

        extra = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _BASE_LOG_RECORD_FIELDS and not key.startswith("_")
        }
        if extra:
            payload["extra"] = extra

        if record.exc_info:
            payload["extra"] = payload.get("extra", {})
            payload["extra"]["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_json_logger(
    name: str = "agentic_vision",
    level: int = logging.INFO,
) -> logging.Logger:
    """Return a logger configured with JSON output to stdout."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if not any(isinstance(handler.formatter, JSONFormatter) for handler in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger

