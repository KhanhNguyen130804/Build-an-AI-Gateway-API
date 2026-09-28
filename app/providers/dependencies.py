"""FastAPI dependencies for configured LLM providers."""

from fastapi import Request

from app.providers.base import LLMProvider
from app.providers.openai import OpenAIResponsesProvider


def get_llm_provider(request: Request) -> LLMProvider:
    return OpenAIResponsesProvider(request.app.state.settings)
