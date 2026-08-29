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


def test_logs_method_path_status_and_duration(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app.request")
    client = TestClient(build_app())

    response = client.get("/ok")

    assert response.status_code == 200
    assert "GET" in caplog.text
    assert "/ok" in caplog.text
    assert "200" in caplog.text
    assert "ms)" in caplog.text


def test_logs_unhandled_error_with_request_context(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO, logger="app.request")
    client = TestClient(build_app(), raise_server_exceptions=False)

    response = client.get("/boom")

    assert response.status_code == 500
    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert len(error_records) == 1
    assert error_records[0].exc_info is not None
    assert "/boom" in caplog.text
