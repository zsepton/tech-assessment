import json
import logging
import os
from typing import Any

_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Extra fields the request-logging middleware attaches to a LogRecord that
# should be surfaced as their own JSON keys, rather than folded into the
# free-text "message" field.
_STRUCTURED_FIELDS = ("method", "path", "status_code", "duration_ms")


class JSONFormatter(logging.Formatter):
    """Renders each log record as one JSON object per line.

    This is what makes the logging genuinely "structured": a log aggregator
    can filter/query on e.g. status_code or duration_ms directly, rather than
    regex-parsing a formatted sentence.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in _STRUCTURED_FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging() -> None:
    """Configure root logging from the LOG_LEVEL env var (defaults to INFO)."""
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = _LEVELS.get(level_name, logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    logging.basicConfig(level=level, handlers=[handler], force=True)
