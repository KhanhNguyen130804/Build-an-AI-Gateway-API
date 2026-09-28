import asyncio
import logging
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.config import Settings
from app.core.tokens import create_access_token
from app.db.models import AIRequest, Conversation, ProviderAttempt, User
from app.db.session import get_session
from app.main import create_app
from app.providers.base import ProviderFailure, ProviderResult
from app.providers.dependencies import get_llm_provider
from app.providers.openai import OpenAIResponsesProvider


class FakeSession:
    def __init__(self, user, *, fail_commit_number=None):
        self.user = user
        self.rows = []
        self.pending_rows = []
        self.snapshots = {}
        self.flush_types = []
        self.commit_calls = 0
        self.rollback_calls = 0
        self.fail_commit_number = fail_commit_number

    async def scalar(self, statement):
        return self.user

    def add(self, row):
        self.pending_rows.append(row)

    async def flush(self):
        self.flush_types.append(tuple(type(row) for row in self.pending_rows))

    async def commit(self):
        self.commit_calls += 1
        if self.commit_calls == self.fail_commit_number:
            raise RuntimeError("simulated database failure")
        self.rows.extend(self.pending_rows)
        self.pending_rows.clear()
        for row in self.rows:
            self.snapshots[id(row)] = {
                column.key: getattr(row, column.key) for column in row.__table__.columns
            }

    async def rollback(self):
        self.rollback_calls += 1
        self.pending_rows.clear()
        for row in self.rows:
            for field, value in self.snapshots[id(row)].items():
                setattr(row, field, value)


class FakeProvider:
    def __init__(self, session, result=None, failure=None):
        self.session = session
        self.result = result
        self.failure = failure
        self.calls = []

    async def generate_text(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        assert self.session.commit_calls == 2
        if self.failure:
            raise self.failure
        return self.result

    async def generate_structured(self, prompt, **kwargs):
        raise AssertionError("structured output is not connected to the Phase04 route")


def make_settings(**overrides):
    values = {
        "_env_file": None,
        "app_env": "test",
        "database_url": None,
        "openai_api_key": "test-provider-key",
        "openai_model": "test-model",
        "jwt_secret": "j" * 64,
        "jwt_issuer": "test-gateway",
        "jwt_audience": "test-clients",
        "request_deadline_seconds": 30,
        "llm_deadline_seconds": 27,
        "attempt_timeout_seconds": 10,
    }
    values.update(overrides)
    return Settings(**values)


def make_user():
    return User(
        id=uuid4(),
        username="reviewer",
        password_hash="not-used-by-this-test",
        is_active=True,
    )


def make_client(*, session=None, provider=None, settings=None):
    settings = settings or make_settings()
    user = session.user if session else make_user()
    session = session or FakeSession(user)
    provider = provider or FakeProvider(
        session,
        result=ProviderResult(
            provider="openai",
            requested_model=settings.openai_model,
            actual_model="actual-test-model",
            provider_request_id="provider-request-test",
            provider_response_id="provider-response-test",
            input_tokens=5,
            output_tokens=2,
            text="Hello from the fake provider.",
        ),
    )
    app = create_app(settings)

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_llm_provider] = lambda: provider
    token = create_access_token(user.id, settings)
    return TestClient(app), session, provider, {"Authorization": f"Bearer {token}"}


def rows_of_type(session, row_type):
    return [row for row in session.rows if isinstance(row, row_type)]


def test_chat_success_commits_request_and_attempt_before_provider_and_correlates_ids(caplog):
    client, session, provider, headers = make_client()
    with client, caplog.at_level(logging.INFO, logger="app.ai"):
        response = client.post(
            "/v1/ai/chat",
            json={"message": "Hello", "route": "standard"},
            headers=headers,
        )

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Hello from the fake provider."
    assert body["provider"] == "openai"
    assert body["model"] == "actual-test-model"
    assert body["usage"] == {"input_tokens": 5, "output_tokens": 2, "complete": True}
    assert body["request_id"] == response.headers["X-Request-ID"]
    assert UUID(body["conversation_id"])
    assert len(provider.calls) == 1
    assert provider.calls[0][1]["model"] == "test-model"
    assert provider.calls[0][1]["timeout_seconds"] <= 10

    request = rows_of_type(session, AIRequest)[0]
    attempt = rows_of_type(session, ProviderAttempt)[0]
    assert request.id == UUID(body["request_id"])
    assert request.conversation_id == UUID(body["conversation_id"])
    assert request.status == "succeeded"
    assert request.started_at.tzinfo is not None
    assert request.final_model == "actual-test-model"
    assert request.attempt_count == 1
    assert request.token_usage_complete is True
    assert attempt.request_id == request.id
    assert attempt.status == "succeeded"
    assert attempt.provider_request_id == "provider-request-test"
    assert attempt.provider_response_id == "provider-response-test"
    assert session.commit_calls == 3
    assert session.flush_types[0] == (Conversation,)
    attempt_log = next(
        record for record in caplog.records if record.getMessage() == "provider_attempt_finished"
    )
    assert attempt_log.request_id == body["request_id"]
    assert attempt_log.provider_request_id == "provider-request-test"
    assert "Hello" not in caplog.text
    assert "Hello from the fake provider." not in caplog.text


def test_chat_rejects_missing_auth_and_extra_client_model_without_provider_dispatch():
    client, session, provider, headers = make_client()
    with client:
        missing_auth = client.post("/v1/ai/chat", json={"message": "Hello"})
        extra_model = client.post(
            "/v1/ai/chat",
            json={"message": "Hello", "model": "client-selected"},
            headers=headers,
        )

    assert missing_auth.status_code == 401
    assert missing_auth.json()["error"]["code"] == "UNAUTHORIZED"
    assert extra_model.status_code == 422
    assert extra_model.json()["error"]["code"] == "VALIDATION_ERROR"
    assert provider.calls == []
    assert rows_of_type(session, AIRequest) == []
    assert rows_of_type(session, ProviderAttempt) == []


@pytest.mark.parametrize(
    "body",
    [
        {"message": "   "},
        {"message": "x" * 4001},
        {"message": "Hello", "route": "premium"},
        {"message": "Hello", "conversation_id": str(uuid4())},
        {"message": "Hello", "base_url": "https://provider.invalid"},
    ],
)
def test_chat_rejects_invalid_fields_and_limits_before_admission(body):
    client, session, provider, headers = make_client()
    with client:
        response = client.post("/v1/ai/chat", json=body, headers=headers)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert provider.calls == []
    assert rows_of_type(session, AIRequest) == []
    assert rows_of_type(session, ProviderAttempt) == []


@pytest.mark.parametrize(
    ("failure", "http_status", "request_status", "attempt_status", "input_tokens"),
    [
        (ProviderFailure(504, "UPSTREAM_TIMEOUT"), 504, "timeout", "timeout", None),
        (
            ProviderFailure(502, "INCOMPLETE_MODEL_OUTPUT", input_tokens=4),
            502,
            "failed",
            "incomplete",
            4,
        ),
        (ProviderFailure(422, "MODEL_REFUSAL"), 422, "refused", "refused", None),
    ],
)
def test_provider_failures_are_terminal_and_preserve_partial_usage(
    failure, http_status, request_status, attempt_status, input_tokens
):
    session = FakeSession(make_user())
    provider = FakeProvider(session, failure=failure)
    client, session, _, headers = make_client(session=session, provider=provider)
    with client:
        response = client.post(
            "/v1/ai/chat", json={"message": "Hello"}, headers=headers
        )

    assert response.status_code == http_status
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
    request = rows_of_type(session, AIRequest)[0]
    attempt = rows_of_type(session, ProviderAttempt)[0]
    assert request.status == request_status
    assert request.error_code == failure.code
    assert request.http_status == http_status
    assert attempt.status == attempt_status
    assert attempt.input_tokens == input_tokens
    assert request.input_tokens == input_tokens
    assert request.token_usage_complete is False


def test_missing_provider_configuration_fails_before_ledger_or_dispatch():
    settings = make_settings(openai_api_key=None)
    session = FakeSession(make_user())
    provider = FakeProvider(session)
    client, session, _, headers = make_client(
        session=session, provider=provider, settings=settings
    )
    with client:
        response = client.post(
            "/v1/ai/chat", json={"message": "Hello"}, headers=headers
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PROVIDER_NOT_CONFIGURED"
    assert provider.calls == []
    assert rows_of_type(session, AIRequest) == []
    assert rows_of_type(session, ProviderAttempt) == []


def test_finalization_database_failure_never_returns_unsaved_success():
    session = FakeSession(make_user(), fail_commit_number=3)
    provider = FakeProvider(
        session,
        result=ProviderResult(
            provider="openai",
            requested_model="test-model",
            actual_model="actual-test-model",
            provider_request_id="provider-request-test",
            provider_response_id="provider-response-test",
            input_tokens=5,
            output_tokens=2,
            text="This output must not be returned as a success.",
        ),
    )
    client, session, _, headers = make_client(session=session, provider=provider)
    with client:
        response = client.post(
            "/v1/ai/chat", json={"message": "Hello"}, headers=headers
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PERSISTENCE_ERROR"
    assert "This output must not be returned" not in response.text
    assert len(provider.calls) == 1
    assert session.rollback_calls == 1
    assert rows_of_type(session, AIRequest)[0].status == "pending"
    assert rows_of_type(session, ProviderAttempt)[0].status == "started"


def test_attempt_persistence_failure_prevents_provider_dispatch_and_finalizes_request():
    session = FakeSession(make_user(), fail_commit_number=2)
    provider = FakeProvider(session)
    client, session, _, headers = make_client(session=session, provider=provider)
    with client:
        response = client.post(
            "/v1/ai/chat", json={"message": "Hello"}, headers=headers
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "PERSISTENCE_ERROR"
    assert provider.calls == []
    request = rows_of_type(session, AIRequest)[0]
    assert request.status == "failed"
    assert request.error_code == "PERSISTENCE_ERROR"
    assert request.attempt_count == 0
    assert request.input_tokens == 0 and request.output_tokens == 0
    assert rows_of_type(session, ProviderAttempt) == []


def test_provider_call_is_cancelled_at_configured_attempt_timeout():
    class SlowProvider(FakeProvider):
        async def generate_text(self, prompt, **kwargs):
            self.calls.append((prompt, kwargs))
            assert self.session.commit_calls == 2
            await asyncio.sleep(0.1)

    settings = make_settings(
        attempt_timeout_seconds=0.01,
        llm_deadline_seconds=0.02,
        connect_timeout_seconds=0.005,
    )
    session = FakeSession(make_user())
    provider = SlowProvider(session)
    client, session, _, headers = make_client(
        session=session, provider=provider, settings=settings
    )
    with client:
        response = client.post(
            "/v1/ai/chat", json={"message": "Hello"}, headers=headers
        )

    assert response.status_code == 504
    assert response.json()["error"]["code"] == "UPSTREAM_TIMEOUT"
    assert rows_of_type(session, AIRequest)[0].status == "timeout"
    assert rows_of_type(session, ProviderAttempt)[0].status == "timeout"
    assert rows_of_type(session, AIRequest)[0].token_usage_complete is False


@pytest.mark.asyncio
async def test_openai_adapter_normalizes_text_and_structured_responses(monkeypatch):
    from app.providers import openai as openai_adapter

    class Ticket(BaseModel):
        category: str

    responses = SimpleNamespace(
        create_result=SimpleNamespace(
            status="completed",
            output_text="reply",
            model="actual-model",
            _request_id="request-1",
            id="response-1",
            output=[],
            usage=SimpleNamespace(input_tokens=3, output_tokens=1),
        ),
        parse_result=SimpleNamespace(
            status="completed",
            output_parsed=Ticket(category="billing"),
            model="actual-model",
            _request_id="request-2",
            id="response-2",
            output=[],
            usage=SimpleNamespace(input_tokens=6, output_tokens=2),
        ),
    )
    calls = []
    client_options = []

    class ResponseMethods:
        async def create(self, **kwargs):
            calls.append(("create", kwargs))
            return responses.create_result

        async def parse(self, **kwargs):
            calls.append(("parse", kwargs))
            return responses.parse_result

    class FakeOpenAIClient:
        def __init__(self, **kwargs):
            client_options.append(kwargs)
            self.responses = ResponseMethods()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

    monkeypatch.setattr(openai_adapter, "AsyncOpenAI", FakeOpenAIClient)
    provider = OpenAIResponsesProvider(make_settings())
    text_result = await provider.generate_text(
        "hello", model="server-model", max_output_tokens=8, timeout_seconds=4
    )
    structured_result = await provider.generate_structured(
        "ticket",
        model="server-model",
        response_model=Ticket,
        max_output_tokens=8,
        timeout_seconds=4,
    )

    assert text_result.text == "reply"
    assert text_result.actual_model == "actual-model"
    assert text_result.provider_request_id == "request-1"
    assert text_result.usage_complete is True
    assert structured_result.structured_output == {"category": "billing"}
    assert structured_result.provider_response_id == "response-2"
    assert calls[0][0] == "create"
    assert calls[0][1]["model"] == "server-model"
    assert calls[1][0] == "parse"
    assert calls[1][1]["text_format"] is Ticket
    assert all(options["max_retries"] == 0 for options in client_options)
    assert all(options["timeout"] == 4 for options in client_options)
