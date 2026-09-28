"""OpenAI Responses API adapter."""

from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from pydantic import BaseModel

from app.core.config import Settings
from app.providers.base import ProviderFailure, ProviderResult


def _token_count(value: object) -> int | None:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return None


def _metadata(response: Any) -> dict[str, object]:
    usage = getattr(response, "usage", None)
    return {
        "actual_model": getattr(response, "model", None),
        "provider_request_id": getattr(response, "_request_id", None),
        "provider_response_id": getattr(response, "id", None),
        "input_tokens": _token_count(getattr(usage, "input_tokens", None)),
        "output_tokens": _token_count(getattr(usage, "output_tokens", None)),
    }


def _has_refusal(response: Any) -> bool:
    for item in getattr(response, "output", ()) or ():
        for content in getattr(item, "content", ()) or ():
            if getattr(content, "type", None) == "refusal":
                return True
    return False


class OpenAIResponsesProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def _call(self, method: str, *, timeout_seconds: float, **kwargs: Any) -> Any:
        key = self.settings.openai_api_key
        if key is None:
            raise ProviderFailure(503, "PROVIDER_NOT_CONFIGURED")

        try:
            async with AsyncOpenAI(
                api_key=key.get_secret_value(),
                max_retries=self.settings.sdk_max_retries,
                timeout=timeout_seconds,
            ) as client:
                operation = getattr(client.responses, method)
                return await operation(timeout=timeout_seconds, **kwargs)
        except APITimeoutError:
            raise ProviderFailure(504, "UPSTREAM_TIMEOUT") from None
        except APIStatusError as exc:
            provider_request_id = getattr(exc, "request_id", None)
            if exc.status_code in (401, 403):
                raise ProviderFailure(
                    503,
                    "PROVIDER_UNAVAILABLE",
                    http_status=exc.status_code,
                    provider_request_id=provider_request_id,
                ) from None
            if exc.status_code == 429:
                code = getattr(exc, "code", None)
                if isinstance(code, str) and code in {
                    "insufficient_quota",
                    "billing_hard_limit_reached",
                }:
                    raise ProviderFailure(
                        503,
                        "PROVIDER_UNAVAILABLE",
                        http_status=exc.status_code,
                        provider_request_id=provider_request_id,
                    ) from None
                raise ProviderFailure(
                    503,
                    "UPSTREAM_RATE_LIMITED",
                    http_status=exc.status_code,
                    provider_request_id=provider_request_id,
                ) from None
            if exc.status_code == 408:
                raise ProviderFailure(
                    504,
                    "UPSTREAM_TIMEOUT",
                    http_status=exc.status_code,
                    provider_request_id=provider_request_id,
                ) from None
            if exc.status_code == 404:
                raise ProviderFailure(
                    503,
                    "PROVIDER_UNAVAILABLE",
                    http_status=exc.status_code,
                    provider_request_id=provider_request_id,
                ) from None
            raise ProviderFailure(
                502,
                "UPSTREAM_ERROR",
                http_status=exc.status_code,
                provider_request_id=provider_request_id,
            ) from None
        except APIConnectionError:
            raise ProviderFailure(502, "UPSTREAM_ERROR") from None

    @staticmethod
    def _require_completed(response: Any) -> dict[str, object]:
        metadata = _metadata(response)
        if _has_refusal(response):
            raise ProviderFailure(422, "MODEL_REFUSAL", http_status=200, **metadata)
        if getattr(response, "status", None) != "completed":
            raise ProviderFailure(502, "INCOMPLETE_MODEL_OUTPUT", http_status=200, **metadata)
        return metadata

    async def generate_text(
        self,
        prompt: str,
        *,
        model: str,
        max_output_tokens: int,
        timeout_seconds: float,
    ) -> ProviderResult:
        response = await self._call(
            "create",
            model=model,
            input=prompt,
            max_output_tokens=max_output_tokens,
            timeout_seconds=timeout_seconds,
        )
        metadata = self._require_completed(response)
        text = getattr(response, "output_text", None)
        if not isinstance(text, str) or not text.strip():
            raise ProviderFailure(502, "INCOMPLETE_MODEL_OUTPUT", http_status=200, **metadata)
        return ProviderResult(
            provider="openai",
            requested_model=model,
            text=text,
            **metadata,
        )

    async def generate_structured(
        self,
        prompt: str,
        *,
        model: str,
        response_model: type[BaseModel],
        max_output_tokens: int,
        timeout_seconds: float,
    ) -> ProviderResult:
        response = await self._call(
            "parse",
            model=model,
            input=prompt,
            text_format=response_model,
            max_output_tokens=max_output_tokens,
            timeout_seconds=timeout_seconds,
        )
        metadata = self._require_completed(response)
        parsed = getattr(response, "output_parsed", None)
        if isinstance(parsed, BaseModel):
            parsed = parsed.model_dump(mode="json")
        if not isinstance(parsed, dict):
            raise ProviderFailure(502, "INCOMPLETE_MODEL_OUTPUT", http_status=200, **metadata)
        return ProviderResult(
            provider="openai",
            requested_model=model,
            structured_output=parsed,
            **metadata,
        )
