"""Short-lived gateway JWT creation and strict claim validation."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.core.config import Settings

ALGORITHM = "HS256"


def create_access_token(user_id: UUID, settings: Settings) -> str:
    if settings.jwt_secret is None:
        raise ValueError("JWT signing is not configured")
    now = datetime.now(UTC)
    claims = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(seconds=settings.jwt_ttl_seconds),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }
    return jwt.encode(claims, settings.jwt_secret.get_secret_value(), algorithm=ALGORITHM)


def decode_access_token(token: str, settings: Settings) -> UUID | None:
    if settings.jwt_secret is None:
        return None
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[ALGORITHM],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "iat", "exp", "iss", "aud"]},
        )
        subject = claims.get("sub")
        if not isinstance(subject, str):
            return None
        return UUID(subject)
    except (jwt.InvalidTokenError, TypeError, ValueError, OverflowError):
        return None
