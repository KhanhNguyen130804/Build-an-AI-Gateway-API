"""Authenticated AI gateway endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_request_settings
from app.core.config import Settings
from app.db.models import User
from app.db.session import get_session
from app.providers.base import LLMProvider
from app.providers.dependencies import get_llm_provider
from app.schemas.ai import ChatInput, ChatResult
from app.services.ai_gateway import chat_once

router = APIRouter(prefix="/v1/ai", tags=["AI"])


@router.post(
    "/chat",
    response_model=ChatResult,
    summary="Generate one chat reply in a new conversation.",
    operation_id="chatOnce",
    responses={
        401: {"description": "Missing or invalid bearer token."},
        422: {"description": "Invalid input or provider refusal."},
        502: {"description": "The provider failed or returned incomplete output."},
        503: {"description": "Provider or persistence unavailable."},
        504: {"description": "Provider timeout."},
    },
)
async def chat(
    body: ChatInput,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_request_settings),
    provider: LLMProvider = Depends(get_llm_provider),
) -> ChatResult:
    return await chat_once(
        session,
        user=user,
        request_id=request.state.request_id,
        request_started_monotonic=request.state.request_started_monotonic,
        body=body,
        settings=settings,
        provider=provider,
    )
