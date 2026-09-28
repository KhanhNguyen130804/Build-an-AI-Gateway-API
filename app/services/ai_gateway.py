"""Chat orchestration and durable request/attempt ledger lifecycle."""

import asyncio
import logging
import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import GatewayError
from app.db.models import AIRequest, Conversation, ProviderAttempt, User
from app.providers.base import LLMProvider, ProviderFailure, ProviderResult
from app.schemas.ai import ChatInput, ChatResult, TokenUsage

logger = logging.getLogger("app.ai")
FINALIZATION_RESERVE_SECONDS = 3.0


def _latency_ms(started: float) -> int:
    return max(0, round((time.perf_counter() - started) * 1000))


def _usage_summary(attempts: list[ProviderAttempt]) -> tuple[int | None, int | None, bool]:
    if not attempts:
        return 0, 0, True
    input_values = [item.input_tokens for item in attempts if item.input_tokens is not None]
    output_values = [item.output_tokens for item in attempts if item.output_tokens is not None]
    complete = all(
        item.usage_known and item.input_tokens is not None and item.output_tokens is not None
        for item in attempts
    )
    return (
        sum(input_values) if input_values else None,
        sum(output_values) if output_values else None,
        complete,
    )


async def _rollback_safely(session: AsyncSession) -> None:
    try:
        await session.rollback()
    except Exception:
        pass


async def _commit_or_persistence_error(
    session: AsyncSession,
    *,
    phase: str,
    timeout_seconds: float | None = None,
) -> None:
    try:
        if timeout_seconds is None:
            await session.commit()
        else:
            async with asyncio.timeout(timeout_seconds):
                await session.commit()
    except Exception as exc:
        await _rollback_safely(session)
        logger.error("ledger_persistence_failed", extra={"error_type": type(exc).__name__})
        raise GatewayError(
            503,
            "PERSISTENCE_ERROR",
            "The gateway could not persist the request state.",
            {"phase": phase},
        ) from None


def _failure_attempt_status(failure: ProviderFailure) -> str:
    if failure.code == "UPSTREAM_TIMEOUT":
        return "timeout"
    if failure.code == "MODEL_REFUSAL":
        return "refused"
    if failure.code == "INCOMPLETE_MODEL_OUTPUT":
        return "incomplete"
    return "failed"


def _failure_request_status(failure: ProviderFailure) -> str:
    if failure.code == "UPSTREAM_TIMEOUT":
        return "timeout"
    if failure.code == "MODEL_REFUSAL":
        return "refused"
    return "failed"


def _safe_message(code: str) -> str:
    return {
        "UPSTREAM_TIMEOUT": "The AI provider did not complete within the request deadline.",
        "UPSTREAM_RATE_LIMITED": "The AI provider is temporarily rate limited.",
        "PROVIDER_UNAVAILABLE": "The AI provider is not available to this gateway.",
        "INCOMPLETE_MODEL_OUTPUT": "The AI provider returned incomplete output.",
        "MODEL_REFUSAL": "The AI provider declined this request.",
        "UPSTREAM_ERROR": "The AI provider could not complete this request.",
    }.get(code, "The AI provider could not complete this request.")


def _apply_usage(request: AIRequest, attempts: list[ProviderAttempt]) -> None:
    request.attempt_count = len(attempts)
    (
        request.input_tokens,
        request.output_tokens,
        request.token_usage_complete,
    ) = _usage_summary(attempts)


def _finish_request(request: AIRequest, *, started: float, status: str, http_status: int) -> None:
    request.status = status
    request.http_status = http_status
    request.finished_at = datetime.now(UTC)
    request.latency_ms = _latency_ms(started)


def _provider_timeout(settings: Settings, request_started: float) -> float:
    elapsed = time.perf_counter() - request_started
    remaining_request = (
        settings.request_deadline_seconds - elapsed - FINALIZATION_RESERVE_SECONDS
    )
    remaining_llm = settings.llm_deadline_seconds - elapsed
    return min(settings.attempt_timeout_seconds, remaining_llm, remaining_request)


def _finalization_timeout(settings: Settings, request_started: float) -> float:
    remaining = settings.request_deadline_seconds - (time.perf_counter() - request_started)
    return max(0.001, min(FINALIZATION_RESERVE_SECONDS, remaining))


async def _admit_request(
    session: AsyncSession,
    *,
    user: User,
    request_id: UUID,
    conversation_id: UUID,
    body: ChatInput,
    model: str,
    started_at: datetime,
) -> AIRequest:
    conversation = Conversation(id=conversation_id, user_id=user.id)
    ai_request = AIRequest(
        id=request_id,
        user_id=user.id,
        conversation_id=conversation_id,
        operation="chat",
        route=body.route,
        requested_provider="openai",
        requested_model=model,
        status="pending",
        started_at=started_at,
    )
    session.add(conversation)
    # The composite AIRequest FK must see its owner conversation in the same transaction.
    await session.flush()
    session.add(ai_request)
    await _commit_or_persistence_error(session, phase="request_admission")
    return ai_request


async def _finalize_without_dispatch(
    session: AsyncSession,
    ai_request: AIRequest,
    *,
    started: float,
    code: str,
    settings: Settings,
) -> None:
    ai_request.error_code = code
    _apply_usage(ai_request, [])
    _finish_request(ai_request, started=started, status="timeout", http_status=504)
    await _commit_or_persistence_error(
        session,
        phase="request_finalize",
        timeout_seconds=_finalization_timeout(settings, started),
    )


async def _start_attempt(
    session: AsyncSession,
    *,
    request_id: UUID,
    model: str,
    ai_request: AIRequest,
    request_started: float,
) -> ProviderAttempt:
    attempt = ProviderAttempt(
        id=uuid4(),
        request_id=request_id,
        attempt_number=1,
        provider="openai",
        requested_model=model,
        status="started",
        started_at=datetime.now(UTC),
    )
    session.add(attempt)
    try:
        await _commit_or_persistence_error(session, phase="attempt_start")
    except GatewayError as error:
        ai_request.error_code = "PERSISTENCE_ERROR"
        _apply_usage(ai_request, [])
        _finish_request(ai_request, started=request_started, status="failed", http_status=503)
        await _commit_or_persistence_error(session, phase="pre_dispatch_finalize")
        raise error
    return attempt


def _apply_provider_metadata(
    attempt: ProviderAttempt,
    *,
    actual_model: str | None,
    provider_request_id: str | None,
    provider_response_id: str | None,
    input_tokens: int | None,
    output_tokens: int | None,
) -> None:
    attempt.actual_model = actual_model
    attempt.provider_request_id = provider_request_id
    attempt.provider_response_id = provider_response_id
    attempt.input_tokens = input_tokens
    attempt.output_tokens = output_tokens
    attempt.usage_known = input_tokens is not None and output_tokens is not None


def _log_attempt(attempt: ProviderAttempt) -> None:
    logger.info(
        "provider_attempt_finished",
        extra={
            "request_id": str(attempt.request_id),
            "provider": attempt.provider,
            "model": attempt.actual_model or attempt.requested_model,
            "attempt": attempt.attempt_number,
            "status": attempt.status,
            "latency_ms": attempt.latency_ms,
            "error_code": attempt.error_code,
            "provider_request_id": attempt.provider_request_id,
        },
    )


async def _finalize_success(
    session: AsyncSession,
    *,
    ai_request: AIRequest,
    attempt: ProviderAttempt,
    result: ProviderResult,
    attempts: list[ProviderAttempt],
    request_started: float,
    attempt_started: float,
    settings: Settings,
) -> None:
    now = datetime.now(UTC)
    _apply_provider_metadata(
        attempt,
        actual_model=result.actual_model,
        provider_request_id=result.provider_request_id,
        provider_response_id=result.provider_response_id,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
    attempt.status = "succeeded"
    attempt.http_status = 200
    attempt.finished_at = now
    attempt.latency_ms = _latency_ms(attempt_started)
    ai_request.final_provider = result.provider
    ai_request.final_model = result.actual_model
    ai_request.error_code = None
    _apply_usage(ai_request, attempts)
    _finish_request(ai_request, started=request_started, status="succeeded", http_status=200)
    await _commit_or_persistence_error(
        session,
        phase="success_finalize",
        timeout_seconds=_finalization_timeout(settings, request_started),
    )
    _log_attempt(attempt)


async def _finalize_failure(
    session: AsyncSession,
    *,
    ai_request: AIRequest,
    attempt: ProviderAttempt,
    failure: ProviderFailure,
    attempts: list[ProviderAttempt],
    request_started: float,
    attempt_started: float,
    settings: Settings,
) -> None:
    now = datetime.now(UTC)
    _apply_provider_metadata(
        attempt,
        actual_model=failure.actual_model,
        provider_request_id=failure.provider_request_id,
        provider_response_id=failure.provider_response_id,
        input_tokens=failure.input_tokens,
        output_tokens=failure.output_tokens,
    )
    attempt.status = _failure_attempt_status(failure)
    attempt.http_status = failure.http_status
    attempt.error_code = failure.code
    attempt.finished_at = now
    attempt.latency_ms = _latency_ms(attempt_started)
    ai_request.final_provider = failure.provider
    ai_request.final_model = failure.actual_model
    ai_request.error_code = failure.code
    _apply_usage(ai_request, attempts)
    _finish_request(
        ai_request,
        started=request_started,
        status=_failure_request_status(failure),
        http_status=failure.status_code,
    )
    await _commit_or_persistence_error(
        session,
        phase="failure_finalize",
        timeout_seconds=_finalization_timeout(settings, request_started),
    )
    _log_attempt(attempt)


async def chat_once(
    session: AsyncSession,
    *,
    user: User,
    request_id: str,
    request_started_monotonic: float,
    body: ChatInput,
    settings: Settings,
    provider: LLMProvider,
) -> ChatResult:
    request_started = request_started_monotonic
    if settings.openai_api_key is None or settings.openai_model is None:
        raise GatewayError(
            503,
            "PROVIDER_NOT_CONFIGURED",
            "The AI provider is not configured for this gateway.",
        )

    ledger_request_id = UUID(request_id)
    conversation_id = uuid4()
    requested_model = settings.openai_model
    ai_request = await _admit_request(
        session,
        user=user,
        request_id=ledger_request_id,
        conversation_id=conversation_id,
        body=body,
        model=requested_model,
        started_at=datetime.now(UTC),
    )
    # Phase05 will persist turns and use the conversation for context.
    provider_timeout = _provider_timeout(settings, request_started)
    if provider_timeout <= 0:
        await _finalize_without_dispatch(
            session,
            ai_request,
            started=request_started,
            code="UPSTREAM_TIMEOUT",
            settings=settings,
        )
        raise GatewayError(504, "UPSTREAM_TIMEOUT", _safe_message("UPSTREAM_TIMEOUT"))

    attempt = await _start_attempt(
        session,
        request_id=ledger_request_id,
        model=requested_model,
        ai_request=ai_request,
        request_started=request_started,
    )
    attempts = [attempt]
    provider_timeout = _provider_timeout(settings, request_started)
    if provider_timeout <= 0:
        failure = ProviderFailure(
            504,
            "UPSTREAM_TIMEOUT",
            input_tokens=0,
            output_tokens=0,
        )
        await _finalize_failure(
            session,
            ai_request=ai_request,
            attempt=attempt,
            failure=failure,
            attempts=attempts,
            request_started=request_started,
            attempt_started=time.perf_counter(),
            settings=settings,
        )
        raise GatewayError(504, "UPSTREAM_TIMEOUT", _safe_message("UPSTREAM_TIMEOUT"))
    attempt_started = time.perf_counter()
    try:
        async with asyncio.timeout(provider_timeout):
            result = await provider.generate_text(
                body.message,
                model=requested_model,
                max_output_tokens=settings.chat_max_output_tokens,
                timeout_seconds=provider_timeout,
            )
        if not isinstance(result.text, str) or not result.text.strip():
            raise ProviderFailure(
                502,
                "INCOMPLETE_MODEL_OUTPUT",
                provider=result.provider,
                http_status=200,
                actual_model=result.actual_model,
                provider_request_id=result.provider_request_id,
                provider_response_id=result.provider_response_id,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
            )
    except TimeoutError:
        failure = ProviderFailure(504, "UPSTREAM_TIMEOUT")
    except ProviderFailure as exc:
        failure = exc
    except Exception as exc:
        logger.warning("provider_call_failed", extra={"error_type": type(exc).__name__})
        failure = ProviderFailure(502, "UPSTREAM_ERROR")
    else:
        await _finalize_success(
            session,
            ai_request=ai_request,
            attempt=attempt,
            result=result,
            attempts=attempts,
            request_started=request_started,
            attempt_started=attempt_started,
            settings=settings,
        )
        input_tokens, output_tokens, usage_complete = _usage_summary(attempts)
        return ChatResult(
            request_id=ledger_request_id,
            conversation_id=conversation_id,
            reply=result.text,
            provider="openai",
            model=result.actual_model or requested_model,
            latency_ms=ai_request.latency_ms,
            usage=TokenUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                complete=usage_complete,
            ),
        )

    await _finalize_failure(
        session,
        ai_request=ai_request,
        attempt=attempt,
        failure=failure,
        attempts=attempts,
        request_started=request_started,
        attempt_started=attempt_started,
        settings=settings,
    )
    raise GatewayError(
        failure.status_code,
        failure.code,
        _safe_message(failure.code),
    )
