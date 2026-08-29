import io
import json
import logging

import pytest
from app.logging_config import JSONFormatter, configure_logging


@pytest.mark.parametrize(
    ("env_value", "expected_level"),
    [
        (None, logging.INFO),
        ("DEBUG", logging.DEBUG),
        ("warning", logging.WARNING),
        ("NOT_A_REAL_LEVEL", logging.INFO),
    ],
)
def test_configure_logging_reads_log_level_env_var(
    monkeypatch: pytest.MonkeyPatch, env_value: str | None, expected_level: int
) -> None:
    if env_value is None:
        monkeypatch.delenv("LOG_LEVEL", raising=False)
    else:
        monkeypatch.setenv("LOG_LEVEL", env_value)

    configure_logging()

    assert logging.getLogger().level == expected_level


def test_json_formatter_renders_structured_fields() -> None:
    logger = logging.getLogger("test.json.formatter")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    try:
        logger.info(
            "request completed",
            extra={"method": "GET", "path": "/health", "status_code": 200, "duration_ms": 1.23},
        )
    finally:
        logger.removeHandler(handler)

    payload = json.loads(stream.getvalue())

    assert payload["message"] == "request completed"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "test.json.formatter"
    assert payload["method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 1.23
    assert "exc_info" not in payload


def test_json_formatter_includes_exc_info_on_errors() -> None:
    logger = logging.getLogger("test.json.formatter.errors")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    try:
        try:
            raise ValueError("boom")
        except ValueError:
            logger.exception("unhandled error handling request")
    finally:
        logger.removeHandler(handler)

    payload = json.loads(stream.getvalue())

    assert payload["level"] == "ERROR"
    assert "ValueError: boom" in payload["exc_info"]
