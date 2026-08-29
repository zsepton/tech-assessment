import logging

import pytest
from app.middleware.logging import RequestLoggingMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient


def build_app() -> FastAPI:
    test_app = FastAPI()
    test_app.add_middleware(RequestLoggingMiddleware)

    @test_app.get("/ok")
    def _ok() -> dict[str, str]:
        return {"status": "ok"}

    @test_app.get("/boom")
    def _boom() -> dict[str, str]:
        raise ValueError("boom")

    return test_app


def test_logs_method_path_status_and_duration_as_discrete_fields(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.request")
    client = TestClient(build_app())

    response = client.get("/ok")

    assert response.status_code == 200
    records = [r for r in caplog.records if r.name == "app.request"]
    assert len(records) == 1
    record = records[0]
    assert record.method == "GET"  # type: ignore[attr-defined]
    assert record.path == "/ok"  # type: ignore[attr-defined]
    assert record.status_code == 200  # type: ignore[attr-defined]
    assert isinstance(record.duration_ms, float)  # type: ignore[attr-defined]


def test_logs_unhandled_error_with_request_context_as_discrete_fields(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="app.request")
    client = TestClient(build_app())

    response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(error_records) == 1
    record = error_records[0]
    assert record.exc_info is not None
    assert record.method == "GET"  # type: ignore[attr-defined]
    assert record.path == "/boom"  # type: ignore[attr-defined]
