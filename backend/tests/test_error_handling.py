import logging
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
from sqlalchemy.exc import OperationalError

from app.main import GENERIC_ERROR_MESSAGE, TimeoutMiddleware, register_error_handling


class _Payload(BaseModel):
    amount: float


def _build_test_app(timeout_seconds: float = 10.0) -> FastAPI:
    """A throwaway app that exercises the real error-handling machinery
    (register_error_handling, TimeoutMiddleware) from app.main without adding
    debug routes to the production app."""
    app = FastAPI()
    register_error_handling(app)
    app.add_middleware(TimeoutMiddleware, timeout_seconds=timeout_seconds)

    @app.post("/echo")
    def echo(payload: _Payload):
        return {"amount": payload.amount}

    @app.get("/boom-db")
    def boom_db():
        raise OperationalError("SELECT 1", {}, Exception("connection refused"))

    return app


@pytest.mark.parametrize(
    ("json_body", "raw_body"),
    [
        ({}, None),  # missing required field
        ({"amount": "not-a-number"}, None),  # wrong type
        (None, b"{not valid json"),  # malformed body
    ],
)
def test_invalid_input_produces_generic_error_response(json_body, raw_body):
    client = TestClient(_build_test_app())
    if raw_body is not None:
        response = client.post(
            "/echo", content=raw_body, headers={"content-type": "application/json"}
        )
    else:
        response = client.post("/echo", json=json_body)

    assert response.status_code == 422
    assert response.json() == {"error": GENERIC_ERROR_MESSAGE}


def test_invalid_input_is_logged_server_side(caplog):
    client = TestClient(_build_test_app())
    with caplog.at_level(logging.WARNING, logger="budget_checker"):
        client.post("/echo", json={})
    assert any(record.levelno == logging.WARNING for record in caplog.records)


def test_multiple_invalid_requests_are_each_logged_individually(caplog):
    client = TestClient(_build_test_app())
    with caplog.at_level(logging.WARNING, logger="budget_checker"):
        client.post("/echo", json={})
        client.post("/echo", json={"amount": "nope"})
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 2


def test_database_unavailable_produces_generic_error_response():
    client = TestClient(_build_test_app())
    response = client.get("/boom-db")
    assert response.status_code == 503
    assert response.json() == {"error": GENERIC_ERROR_MESSAGE}


def test_database_unavailable_is_logged_server_side(caplog):
    client = TestClient(_build_test_app())
    with caplog.at_level(logging.ERROR, logger="budget_checker"):
        client.get("/boom-db")
    assert any(record.levelno == logging.ERROR for record in caplog.records)


def test_timeout_produces_generic_error_response():
    app = _build_test_app(timeout_seconds=0.2)

    @app.get("/slow")
    def slow():
        time.sleep(0.6)
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/slow")
    assert response.status_code == 504
    assert response.json() == {"error": GENERIC_ERROR_MESSAGE}


def test_request_completing_at_exactly_the_timeout_is_not_treated_as_a_failure():
    app = _build_test_app(timeout_seconds=1.0)

    @app.get("/fast")
    def fast():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/fast")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_timeout_is_logged_server_side(caplog):
    app = _build_test_app(timeout_seconds=0.2)

    @app.get("/slow")
    def slow():
        time.sleep(0.6)
        return {"ok": True}

    client = TestClient(app)
    with caplog.at_level(logging.ERROR, logger="budget_checker"):
        client.get("/slow")
    assert any(record.levelno == logging.ERROR for record in caplog.records)


def test_multiple_database_unavailable_failures_are_each_logged_individually(caplog):
    client = TestClient(_build_test_app())
    with caplog.at_level(logging.ERROR, logger="budget_checker"):
        client.get("/boom-db")
        client.get("/boom-db")
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(errors) == 2


def test_request_completing_at_exactly_the_timeout_is_not_logged_as_a_failure(caplog):
    app = _build_test_app(timeout_seconds=1.0)

    @app.get("/fast")
    def fast():
        return {"ok": True}

    client = TestClient(app)
    with caplog.at_level(logging.ERROR, logger="budget_checker"):
        client.get("/fast")
    assert not any(record.levelno == logging.ERROR for record in caplog.records)


def test_multiple_timeouts_are_each_logged_individually(caplog):
    app = _build_test_app(timeout_seconds=0.2)

    @app.get("/slow")
    def slow():
        time.sleep(0.6)
        return {"ok": True}

    client = TestClient(app)
    with caplog.at_level(logging.ERROR, logger="budget_checker"):
        client.get("/slow")
        client.get("/slow")
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(errors) == 2
