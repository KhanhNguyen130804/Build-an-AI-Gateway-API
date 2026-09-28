import asyncio

from fastapi import APIRouter, Request

from app.core.errors import GatewayError
from app.schemas.health import HealthResult

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live", response_model=HealthResult)
async def liveness() -> HealthResult:
    return HealthResult(status="alive")


@router.get("/ready", response_model=HealthResult, responses={503: {"description": "DB not ready"}})
async def readiness(request: Request) -> HealthResult:
    # Phase 02 attaches the real DB probe. No inference call belongs in a healthcheck.
    probe = request.app.state.database_probe
    if probe is None:
        raise GatewayError(503, "DATABASE_NOT_READY", "The database is not ready.")
    try:
        async with asyncio.timeout(request.app.state.settings.database_check_timeout_seconds):
            await probe()
    except Exception:
        raise GatewayError(503, "DATABASE_NOT_READY", "The database is not ready.") from None
    return HealthResult(status="ready")
