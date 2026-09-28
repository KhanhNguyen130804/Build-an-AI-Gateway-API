from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects import postgresql

from app.core.config import Settings
from app.core.errors import GatewayError
from app.core.passwords import password_hasher
from app.core.tokens import ALGORITHM, create_access_token
from app.db.models import Conversation, User
from app.db.queries import get_owned_conversation
from app.db.session import get_session
from app.main import create_app

PASSWORD = "reviewer-test-password-long-enough"


class FakeSession:
    def __init__(self, users=(), conversations=()):
        self.users = {user.username: user for user in users}
        self.users_by_id = {user.id: user for user in users}
        self.conversations = {conversation.id: conversation for conversation in conversations}
        self.last_statement = None

    async def scalar(self, statement):
        self.last_statement = statement
        entity = statement.column_descriptions[0]["entity"]
        params = statement.compile(dialect=postgresql.dialect()).params
        if entity is User:
            if username := next((v for k, v in params.items() if k.startswith("username")), None):
                return self.users.get(username)
            user_id = next((v for k, v in params.items() if k.startswith("id_")), None)
            user = self.users_by_id.get(user_id)
            if "is_active" in str(statement.whereclause) and user and not user.is_active:
                return None
            return user
        if entity is Conversation:
            conversation_id = next((v for k, v in params.items() if k.startswith("id_")), None)
            owner_id = next((v for k, v in params.items() if k.startswith("user_id_")), None)
            conversation = self.conversations.get(conversation_id)
            return conversation if conversation and conversation.user_id == owner_id else None
        raise AssertionError(f"Unexpected query entity: {entity}")


def make_settings():
    return Settings(
        _env_file=None,
        app_env="test",
        database_url=None,
        openai_api_key=None,
        openai_model=None,
        jwt_secret="j" * 64,
        jwt_issuer="test-gateway",
        jwt_audience="test-clients",
        jwt_ttl_seconds=300,
    )


def make_user(*, active=True):
    return User(
        id=uuid4(),
        username="reviewer",
        password_hash=password_hasher.hash(PASSWORD),
        is_active=active,
    )


def make_app(settings, session):
    app = create_app(settings)

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    return app


def signed_token(settings, user_id, **overrides):
    now = datetime.now(UTC)
    claims = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        **overrides,
    }
    return jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm=ALGORITHM)


def assert_auth_error(response, code="UNAUTHORIZED"):
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    body = response.json()["error"]
    assert body["code"] == code
    assert body["request_id"] == response.headers["X-Request-ID"]
    UUID(body["request_id"])
    return body


def test_login_issues_short_lived_jwt_and_bearer_identity():
    settings = make_settings()
    user = make_user()
    app = make_app(settings, FakeSession([user]))

    with TestClient(app) as client:
        response = client.post(
            "/v1/auth", json={"username": user.username, "password": PASSWORD}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["token_type"] == "bearer"
        assert result["expires_in"] == settings.jwt_ttl_seconds
        claims = jwt.decode(
            result["access_token"],
            settings.jwt_secret.get_secret_value(),
            algorithms=[ALGORITHM],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
        assert claims["sub"] == str(user.id)
        assert claims["exp"] - claims["iat"] == settings.jwt_ttl_seconds

        identity = client.get(
            "/v1/auth/me", headers={"Authorization": f"Bearer {result['access_token']}"}
        )
        assert identity.status_code == 200
        assert identity.json() == {"id": str(user.id), "username": user.username}


def test_login_does_not_disclose_unknown_wrong_or_inactive_accounts():
    settings = make_settings()
    active = make_user()
    inactive = User(
        id=uuid4(),
        username="inactive",
        password_hash=password_hasher.hash(PASSWORD),
        is_active=False,
    )
    app = make_app(settings, FakeSession([active, inactive]))

    with TestClient(app) as client:
        responses = [
            client.post("/v1/auth", json={"username": "missing", "password": PASSWORD}),
            client.post("/v1/auth", json={"username": active.username, "password": "wrong"}),
            client.post("/v1/auth", json={"username": inactive.username, "password": PASSWORD}),
        ]

    bodies = [assert_auth_error(response, "INVALID_CREDENTIALS") for response in responses]
    assert {(body["code"], body["message"]) for body in bodies} == {
        ("INVALID_CREDENTIALS", "Username or password is incorrect.")
    }
    assert all(body["details"] == {} for body in bodies)


@pytest.mark.parametrize(
    "token_kind",
    [
        "missing",
        "wrong_scheme",
        "malformed",
        "expired",
        "tampered",
        "wrong_issuer",
        "wrong_audience",
    ],
)
def test_protected_identity_rejects_invalid_tokens(token_kind):
    settings = make_settings()
    user = make_user()
    session = FakeSession([user])
    app = make_app(settings, session)
    token = signed_token(settings, user.id)
    headers = {"Authorization": f"Bearer {token}"}
    if token_kind == "wrong_scheme":
        headers = {"Authorization": f"Basic {token}"}
    elif token_kind == "malformed":
        headers = {"Authorization": "Bearer not-a-jwt"}
    elif token_kind == "expired":
        expired = signed_token(settings, user.id, exp=datetime.now(UTC) - timedelta(seconds=2))
        headers = {"Authorization": f"Bearer {expired}"}
    elif token_kind == "tampered":
        headers = {"Authorization": f"Bearer {token}x"}
    elif token_kind == "wrong_issuer":
        headers = {
            "Authorization": f"Bearer {signed_token(settings, user.id, iss='another-issuer')}"
        }
    elif token_kind == "wrong_audience":
        headers = {
            "Authorization": f"Bearer {signed_token(settings, user.id, aud='another-audience')}"
        }
    elif token_kind == "missing":
        headers = {}

    with TestClient(app) as client:
        assert_auth_error(client.get("/v1/auth/me", headers=headers))


def test_missing_inactive_or_unknown_database_user_cannot_use_valid_token():
    settings = make_settings()
    inactive = make_user(active=False)
    unknown_id = uuid4()
    app = make_app(settings, FakeSession([inactive]))

    with TestClient(app) as client:
        inactive_response = client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {create_access_token(inactive.id, settings)}"},
        )
        unknown_response = client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {create_access_token(unknown_id, settings)}"},
        )

    inactive_error = assert_auth_error(inactive_response)
    unknown_error = assert_auth_error(unknown_response)
    assert (inactive_error["code"], inactive_error["message"]) == (
        unknown_error["code"],
        unknown_error["message"],
    )


def test_login_input_rejects_extra_fields_without_echoing_values():
    app = make_app(make_settings(), FakeSession())

    with TestClient(app) as client:
        response = client.post(
            "/v1/auth",
            json={"username": "reviewer", "password": "sensitive-example", "user_id": "attacker"},
        )

    assert response.status_code == 422
    assert "sensitive-example" not in response.text
    assert "attacker" not in response.text


@pytest.mark.asyncio
async def test_owned_conversation_query_uses_owner_and_hides_missing_or_foreign_rows():
    owner_id = uuid4()
    other_user_id = uuid4()
    conversation = Conversation(id=uuid4(), user_id=owner_id)
    session = FakeSession(conversations=[conversation])

    assert await get_owned_conversation(session, conversation.id, owner_id) is conversation
    compiled = str(session.last_statement.compile(dialect=postgresql.dialect()))
    assert "gateway.conversations.user_id" in compiled

    errors = []
    for conversation_id, requested_owner in (
        (conversation.id, other_user_id),
        (uuid4(), owner_id),
    ):
        with pytest.raises(GatewayError) as raised:
            await get_owned_conversation(session, conversation_id, requested_owner)
        errors.append(raised.value)
    assert [(error.status_code, error.code, error.message) for error in errors] == [
        (404, "CONVERSATION_NOT_FOUND", "The conversation was not found."),
        (404, "CONVERSATION_NOT_FOUND", "The conversation was not found."),
    ]
