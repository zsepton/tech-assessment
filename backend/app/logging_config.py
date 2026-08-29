import logging
import os

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"

_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


def configure_logging() -> None:
    """Configure root logging from the LOG_LEVEL env var (defaults to INFO)."""
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = _LEVELS.get(level_name, logging.INFO)
    logging.basicConfig(level=level, format=LOG_FORMAT, force=True)
