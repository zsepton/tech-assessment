import logging

import pytest
from app.logging_config import configure_logging


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
