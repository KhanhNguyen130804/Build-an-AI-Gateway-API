from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_request_settings
from app.core.config import Settings
from app.core.errors import GatewayError
from app.core.passwords import verify_password, verify_unknown_user
from app.core.tokens import create_access_token
from app.db.models import User
from app.db.session import get_session
from app.schemas.auth import AuthenticatedUser, LoginInput, TokenResult

router = APIRouter(prefix="/v1/auth", tags=["Auth"])


@router.post(
    "",
    response_model=TokenResult,
    responses={
        401: {
            "description": "Invalid credentials.",
            "headers": {
                "WWW-Authenticate": {
                    "description": "Bearer challenge.",
                    "schema": {"type": "string", "example": "Bearer"},
                }
            },
        },
        503: {"description": "Database or authentication configuration unavailable."},
    },
    summary="Login a seeded user with JSON credentials.",
    operation_id="login",
)
async def login(
    body: LoginInput,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_request_settings),
):
    if settings.jwt_secret is None:
        raise GatewayError(503, "AUTH_NOT_CONFIGURED", "Authentication is not configured.")

    user = await session.scalar(select(User).where(User.username == body.username))
    password = body.password.get_secret_value()
    if user is None:
        verify_unknown_user(password)
    elif not verify_password(password, user.password_hash):
        user = None

    if user is None or not user.is_active:
        raise GatewayError(
            401,
            "INVALID_CREDENTIALS",
            "Username or password is incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return TokenResult(
        access_token=create_access_token(user.id, settings),
        token_type="bearer",
        expires_in=settings.jwt_ttl_seconds,
    )


@router.get(
    "/me",
    response_model=AuthenticatedUser,
    responses={
        401: {
            "description": "Missing or invalid bearer token.",
            "headers": {
                "WWW-Authenticate": {
                    "description": "Bearer challenge.",
                    "schema": {"type": "string", "example": "Bearer"},
                }
            },
        },
        503: {"description": "Database unavailable."},
    },
    summary="Return the identity associated with the bearer token.",
    operation_id="getCurrentUser",
)
async def current_user(user: User = Depends(get_current_user)) -> AuthenticatedUser:
    return AuthenticatedUser(id=user.id, username=user.username)
