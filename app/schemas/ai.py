"""Schemas for the first-turn chat API."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChatInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=4000)
    route: Literal["standard"] = "standard"

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must contain non-whitespace characters")
        return value


class TokenUsage(BaseModel):
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    complete: bool


class ChatResult(BaseModel):
    request_id: UUID
    conversation_id: UUID
    reply: str
    provider: Literal["openai"]
    model: str
    latency_ms: int = Field(ge=0)
    usage: TokenUsage
