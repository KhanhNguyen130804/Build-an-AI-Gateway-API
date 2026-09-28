"""Request dependencies for gateway authentication and current-user access."""

from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import GatewayError
from app.core.tokens import decode_access_token
from app.db.models import User
from app.db.session import get_session

gateway_bearer = HTTPBearer(scheme_name="GatewayBearer", auto_error=False)


def get_request_settings(request: Request) -> Settings:
    return request.app.state.settings


async def get_token_subject(
    credentials: HTTPAuthorizationCredentials | None = Depends(gateway_bearer),
    settings: Settings = Depends(get_request_settings),
) -> UUID:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise GatewayError(
            401,
            "UNAUTHORIZED",
            "A valid bearer token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decode_access_token(credentials.credentials, settings)
    if user_id is None:
        raise GatewayError(
            401,
            "UNAUTHORIZED",
            "A valid bearer token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id


async def get_current_user(
    user_id: UUID = Depends(get_token_subject),
    session: AsyncSession = Depends(get_session),
) -> User:
    user = await session.scalar(
        select(User).where(User.id == user_id, User.is_active.is_(True))
    )
    if user is None:
        raise GatewayError(
            401,
            "UNAUTHORIZED",
            "A valid bearer token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
