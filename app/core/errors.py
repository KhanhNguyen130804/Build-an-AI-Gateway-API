from dataclasses import dataclass, field

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse


@dataclass
class GatewayError(Exception):
    status_code: int
    code: str
    message: str
    details: dict = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)


def error_response(request_id: str, error: GatewayError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
                "request_id": request_id,
                "details": error.details,
            }
        },
        headers=error.headers,
    )


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(GatewayError)
    async def gateway_error(request: Request, exc: GatewayError):
        return error_response(request.state.request_id, exc)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Deliberately exclude raw inputs, ctx and validation messages.
        fields = [
            {"field": ".".join(map(str, e["loc"]))[:100], "type": e["type"]} for e in exc.errors()
        ]
        return error_response(
            request.state.request_id,
            GatewayError(
                422,
                "VALIDATION_ERROR",
                "The request did not match the API schema.",
                {"fields": fields},
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        codes = {
            401: ("UNAUTHORIZED", "A valid bearer token is required."),
            404: ("NOT_FOUND", "The requested resource was not found."),
            405: ("METHOD_NOT_ALLOWED", "This HTTP method is not supported."),
            413: ("PAYLOAD_TOO_LARGE", "The request payload exceeds the configured limit."),
        }
        code, message = codes.get(exc.status_code, ("HTTP_ERROR", "The request failed."))
        headers = dict(exc.headers or {})
        if exc.status_code == 401:
            headers.setdefault("WWW-Authenticate", "Bearer")
        return error_response(
            request.state.request_id, GatewayError(exc.status_code, code, message, headers=headers)
        )
