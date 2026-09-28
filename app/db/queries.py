"""Owner-scoped queries shared by future authenticated resource endpoints."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import GatewayError
from app.db.models import Conversation


async def get_owned_conversation(
    session: AsyncSession, conversation_id: UUID, owner_id: UUID
) -> Conversation:
    conversation = await session.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == owner_id,
        )
    )
    if conversation is None:
        raise GatewayError(
            404,
            "CONVERSATION_NOT_FOUND",
            "The conversation was not found.",
        )
    return conversation
