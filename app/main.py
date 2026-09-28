import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.health import router as health_router
from app.core.config import Settings, load_settings
from app.core.errors import install_exception_handlers
from app.core.middleware import RequestContextMiddleware
from app.db.session import Database

logger = logging.getLogger("app.lifecycle")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else load_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("application_started")
        yield
        if app.state.database is not None:
            await app.state.database.close()
        logger.info("application_stopped")

    app = FastAPI(
        title="AI Gateway",
        version=__version__,
        lifespan=lifespan,
        description=(
            "Phase 02: PostgreSQL storage and health infrastructure. Business APIs follow."
        ),
    )
    app.state.settings = settings
    app.state.database = Database(settings) if settings.database_url else None
    app.state.database_probe = app.state.database.probe if app.state.database else None
    install_exception_handlers(app)
    app.add_middleware(RequestContextMiddleware, max_body_bytes=settings.max_body_bytes)
    app.include_router(health_router)
    return app
