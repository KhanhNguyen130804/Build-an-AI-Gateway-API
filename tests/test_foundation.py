import asyncio
import json
import logging
from pathlib import Path
from uuid import UUID

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict

from app.core.config import ConfigurationError, Settings, load_settings
from app.core.logging import JsonFormatter, request_id_context
from app.main import create_app


@pytest.fixture
def settings():
    return Settings(
        _env_file=None,
        app_env="test",
        database_url=None,
        openai_api_key=None,
        openai_model=None,
        jwt_secret=None,
        rate_limit_hash_secret=None,
    )


@pytest.fixture
def app(settings):
    application = create_app(settings)

    class Input(BaseModel):
        model_config = ConfigDict(extra="forbid")
        text: str

    @application.post("/test/echo")
    async def echo(body: Input):
        return {"text": body.text}

    @application.get("/test/crash")
    async def crash():
        raise RuntimeError("sensitive database/password exception must not be disclosed")

    @application.get("/test/private")
    async def private():
        raise HTTPException(401, detail="do not disclose internal detail")

    return application


def assert_error(response, status, code):
    assert response.status_code == status
    body = response.json()["error"]
    assert body["code"] == code
    assert body["request_id"] == response.headers["X-Request-ID"]
    UUID(body["request_id"])


def test_liveness_and_docs_without_external_credentials(app):
    with TestClient(app) as client:
        response = client.get("/health/live")
        assert response.json() == {"status": "alive"}
        UUID(response.headers["X-Request-ID"])
        assert client.get("/docs").status_code == 200
        assert "/health/live" in client.get("/openapi.json").json()["paths"]
        assert_error(client.get("/health/ready"), 503, "DATABASE_NOT_READY")
        # Business APIs must not silently return mocked success in Phase 01.
        assert_error(client.post("/v1/ai/chat", json={"message": "hello"}), 404, "NOT_FOUND")


def test_database_probe_failure_and_success(app):
    async def failure():
        raise RuntimeError("postgresql://user:secret@host/private")

    async def success():
        return None

    with TestClient(app) as client:
        app.state.database_probe = failure
        response = client.get("/health/ready")
        assert_error(response, 503, "DATABASE_NOT_READY")
        assert "secret" not in response.text
        app.state.database_probe = success
        assert client.get("/health/ready").json() == {"status": "ready"}


def test_database_probe_is_bounded(app):
    async def slow():
        await asyncio.sleep(1)

    app.state.database_probe = slow
    app.state.settings.database_check_timeout_seconds = 0.01
    with TestClient(app) as client:
        assert_error(client.get("/health/ready"), 503, "DATABASE_NOT_READY")


@pytest.mark.parametrize(
    "body",
    [{"text": {"password": "private-test-value"}}, {"text": "ok", "secret": "private-test-value"}],
)
def test_validation_never_returns_input_values(app, body):
    with TestClient(app) as client:
        response = client.post("/test/echo", json=body)
        assert_error(response, 422, "VALIDATION_ERROR")
        assert "private-test-value" not in response.text
        assert "input" not in response.json()["error"]["details"]


def test_malformed_json(app):
    with TestClient(app) as client:
        assert_error(
            client.post(
                "/test/echo", content="{not-json", headers={"Content-Type": "application/json"}
            ),
            422,
            "VALIDATION_ERROR",
        )


def test_unhandled_error_is_redacted_and_correlated(app, caplog):
    with TestClient(app) as client, caplog.at_level(logging.INFO, logger="app.http"):
        response = client.get("/test/crash")
        assert_error(response, 500, "INTERNAL_ERROR")
        assert "password" not in response.text
        assert "sensitive database" not in caplog.text
        assert any(r.getMessage() == "request_failed" for r in caplog.records)


def test_auth_header_and_method_errors(app):
    with TestClient(app) as client:
        response = client.get("/test/private")
        assert_error(response, 401, "UNAUTHORIZED")
        assert response.headers["WWW-Authenticate"] == "Bearer"
        assert "internal detail" not in response.text
        assert_error(client.post("/health/live"), 405, "METHOD_NOT_ALLOWED")


def test_declared_oversized_body_is_rejected(app):
    with TestClient(app) as client:
        response = client.post("/test/echo", json={"text": "x" * 65536})
        assert_error(response, 413, "PAYLOAD_TOO_LARGE")


async def test_streamed_oversized_body_without_content_length(app):
    async def chunks():
        yield b'{"text":"' + b"x" * 40000
        yield b"x" * 40000 + b'"}'

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/test/echo", content=chunks(), headers={"Content-Type": "application/json"}
        )
        assert_error(response, 413, "PAYLOAD_TOO_LARGE")


def test_unknown_route_and_query_never_log_client_secrets(app, caplog):
    with TestClient(app) as client, caplog.at_level(logging.INFO, logger="app.http"):
        response = client.get("/private-test-value?password=private-test-value")
        assert_error(response, 404, "NOT_FOUND")
        assert "private-test-value" not in caplog.text
        finish = next(r for r in caplog.records if r.getMessage() == "request_finished")
        assert finish.route == "<unmatched>"


async def test_request_ids_are_server_generated_and_isolated(app):
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        results = await asyncio.gather(
            *(
                client.get(
                    "/health/live",
                    headers={
                        "X-Request-ID": "untrusted-client-id",
                    },
                )
                for _ in range(10)
            )
        )
    ids = {response.headers["X-Request-ID"] for response in results}
    assert len(ids) == 10
    assert "untrusted-client-id" not in ids
    assert request_id_context.get() is None


def test_formatter_redacts_known_secrets_and_bearer():
    formatter = JsonFormatter(("private-key-value",))
    record = logging.LogRecord(
        "app", logging.ERROR, "", 0, "private-key-value Bearer private-token-value", (), None
    )
    record.password = "ignored-private-extra"
    value = formatter.format(record)
    assert "private-key-value" not in value
    assert "private-token-value" not in value
    assert "ignored-private-extra" not in value
    assert json.loads(value)["level"] == "ERROR"


@pytest.mark.parametrize(
    "overrides",
    [
        {"jwt_secret": "private-short-secret"},
        {"database_url": "sqlite:///private-test-db"},
        {"sdk_max_retries": 2},
        {"llm_deadline_seconds": 30},
        {
            "app_env": "production",
            "database_url": None,
            "openai_api_key": None,
            "openai_model": None,
            "jwt_secret": None,
            "rate_limit_hash_secret": None,
        },
    ],
)
def test_config_errors_are_safe_and_enforce_invariants(overrides):
    with pytest.raises(ConfigurationError) as error:
        load_settings(_env_file=None, **overrides)
    assert "private-" not in str(error.value)
    assert "input_value" not in str(error.value)


def test_valid_production_config_is_masked():
    settings = load_settings(
        _env_file=None,
        app_env="production",
        database_url="postgresql://user:private-db-password@localhost/db",
        openai_api_key="private-provider-value",
        openai_model="test-model",
        jwt_secret="j" * 64,
        rate_limit_hash_secret="r" * 64,
    )
    assert "private-db-password" not in repr(settings)
    assert "private-provider-value" not in repr(settings)


def test_development_template_loads_integer_environment_values():
    template = Path(__file__).resolve().parent.parent / ".env.example"
    settings = load_settings(_env_file=template)
    assert settings.sdk_max_retries == 0
    assert settings.port == 8000
    assert settings.database_url is None
    assert settings.openai_api_key is None
