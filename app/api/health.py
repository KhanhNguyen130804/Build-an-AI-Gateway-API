import asyncio
import logging

from fastapi import APIRouter, Request

from app.core.errors import GatewayError
from app.schemas.health import HealthResult

router = APIRouter(prefix="/health", tags=["Health"])
logger = logging.getLogger("app.health")


@router.get("/live", response_model=HealthResult)
async def liveness() -> HealthResult:
    return HealthResult(status="alive")


@router.get("/ready", response_model=HealthResult, responses={503: {"description": "DB not ready"}})
async def readiness(request: Request) -> HealthResult:
    # Database-only readiness; no inference call belongs in a healthcheck.
    probe = request.app.state.database_probe
    if probe is None:
        raise GatewayError(503, "DATABASE_NOT_READY", "The database is not ready.")
    try:
        async with asyncio.timeout(request.app.state.settings.database_check_timeout_seconds):
            await probe()
    except Exception as exc:
        logger.warning("database_not_ready", extra={"error_type": type(exc).__name__})
        raise GatewayError(503, "DATABASE_NOT_READY", "The database is not ready.") from None
    return HealthResult(status="ready")
