"""Provider-independent result and failure contracts."""

from dataclasses import dataclass
from typing import Any, Protocol

from pydantic import BaseModel


@dataclass(frozen=True, slots=True)
class ProviderResult:
    provider: str
    requested_model: str
    actual_model: str | None
    provider_request_id: str | None
    provider_response_id: str | None
    input_tokens: int | None
    output_tokens: int | None
    text: str | None = None
    structured_output: dict[str, Any] | None = None

    @property
    def usage_complete(self) -> bool:
        return self.input_tokens is not None and self.output_tokens is not None


class ProviderFailure(Exception):
    """Safe provider failure metadata; provider response bodies are never retained."""

    def __init__(
        self,
        status_code: int,
        code: str,
        *,
        provider: str = "openai",
        http_status: int | None = None,
        provider_request_id: str | None = None,
        provider_response_id: str | None = None,
        actual_model: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code
        self.provider = provider
        self.http_status = http_status
        self.provider_request_id = provider_request_id
        self.provider_response_id = provider_response_id
        self.actual_model = actual_model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class LLMProvider(Protocol):
    async def generate_text(
        self,
        prompt: str,
        *,
        model: str,
        max_output_tokens: int,
        timeout_seconds: float,
    ) -> ProviderResult: ...

    async def generate_structured(
        self,
        prompt: str,
        *,
        model: str,
        response_model: type[BaseModel],
        max_output_tokens: int,
        timeout_seconds: float,
    ) -> ProviderResult: ...
