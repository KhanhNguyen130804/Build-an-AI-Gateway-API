"""Read-only Phase03 auth smoke using the configured seeded reviewer account."""

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from app.core.config import ConfigurationError, load_settings  # noqa: E402
from app.main import create_app  # noqa: E402


async def verify():
    settings = load_settings()
    if not settings.database_url or not settings.jwt_secret or not settings.demo_password:
        raise ConfigurationError(
            "Missing configuration fields: database_url, jwt_secret, demo_password"
        )

    app = create_app(settings)
    checks = {}
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://phase03.local", timeout=10
        ) as client:
            login = await client.post(
                "/v1/auth",
                json={
                    "username": settings.demo_username,
                    "password": settings.demo_password.get_secret_value(),
                },
            )
            assert login.status_code == 200
            login_body = login.json()
            assert login_body["token_type"] == "bearer"
            assert login_body["expires_in"] == settings.jwt_ttl_seconds
            token = login_body["access_token"]
            checks["seeded_login"] = True

            identity = await client.get(
                "/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
            )
            assert identity.status_code == 200
            assert identity.json()["username"] == settings.demo_username
            checks["jwt_identity"] = True

            invalid_login = await client.post(
                "/v1/auth",
                json={"username": settings.demo_username, "password": "invalid-phase03-password"},
            )
            assert invalid_login.status_code == 401
            assert invalid_login.json()["error"]["code"] == "INVALID_CREDENTIALS"
            checks["invalid_password_rejected"] = True

            unauthenticated = await client.get("/v1/auth/me")
            assert unauthenticated.status_code == 401
            assert unauthenticated.headers["WWW-Authenticate"] == "Bearer"
            body = unauthenticated.json()["error"]
            assert body["request_id"] == unauthenticated.headers["X-Request-ID"]
            checks["missing_token_rejected"] = True
    finally:
        if app.state.database is not None:
            await app.state.database.close()

    return {
        "checked_at_utc": datetime.now(UTC).isoformat(),
        "status": "PASS",
        "checks": checks,
        "scope": (
            "Read-only authentication against the configured seeded user; "
            "no DB writes or LLM calls."
        ),
    }


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        result = asyncio.run(verify())
        target = Path(__file__).resolve().parent.parent / "artifacts/evidence/phase03.json"
        target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {"check": "phase03_auth", "status": "FAIL", "error_type": type(exc).__name__}
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
