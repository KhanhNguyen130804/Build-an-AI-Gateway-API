import logging
from time import perf_counter
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import GatewayError, error_response
from app.core.logging import request_id_context

logger = logging.getLogger("app.http")


class RequestContextMiddleware:
    """Pure ASGI correlation, body bounds and safe unhandled-error responses."""

    def __init__(self, app: ASGIApp, max_body_bytes: int):
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid4())  # Client IDs cannot replace the ledger identity.
        scope.setdefault("state", {})["request_id"] = request_id
        context_token = request_id_context.set(request_id)
        started_at = perf_counter()
        status = 500
        response_started = False
        consumed_bytes = 0

        async def correlated_send(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                status = message["status"]
                response_started = True
                MutableHeaders(scope=message)["X-Request-ID"] = request_id
            await send(message)

        async def bounded_receive() -> Message:
            nonlocal consumed_bytes
            message = await receive()
            if message["type"] == "http.request":
                consumed_bytes += len(message.get("body", b""))
                if consumed_bytes > self.max_body_bytes:
                    raise HTTPException(413)
            return message

        logger.info("request_started", extra={"method": scope["method"]})
        try:
            raw_length = Headers(scope=scope).get("content-length")
            if raw_length is not None:
                try:
                    content_length = int(raw_length)
                    if content_length < 0:
                        raise ValueError
                except ValueError:
                    raise GatewayError(422, "VALIDATION_ERROR", "Invalid Content-Length.") from None
                if content_length > self.max_body_bytes:
                    raise GatewayError(
                        413,
                        "PAYLOAD_TOO_LARGE",
                        "The request payload exceeds the configured limit.",
                    )
            await self.app(scope, bounded_receive, correlated_send)
        except GatewayError as exc:
            if response_started:
                raise
            await error_response(request_id, exc)(scope, receive, correlated_send)
        except Exception as exc:
            logger.error("request_failed", extra={"error_type": type(exc).__name__})
            if response_started:
                raise
            await error_response(
                request_id,
                GatewayError(
                    500,
                    "INTERNAL_ERROR",
                    "An unexpected error occurred.",
                ),
            )(scope, receive, correlated_send)
        finally:
            route = getattr(scope.get("route"), "path", "<unmatched>")
            logger.info(
                "request_finished",
                extra={
                    "method": scope["method"],
                    "route": route,
                    "status": status,
                    "latency_ms": round((perf_counter() - started_at) * 1000, 2),
                },
            )
            request_id_context.reset(context_token)
