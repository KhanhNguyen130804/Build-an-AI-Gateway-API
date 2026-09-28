"""Bounded PostgreSQL connections; NullPool also works with serverless poolers."""

from fastapi import Request
from sqlalchemy import event, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.core.errors import GatewayError

REVISION = "0001_gateway"


def database_url(settings: Settings):
    if not settings.database_url:
        raise ValueError("DATABASE_URL is required")
    return make_url(settings.database_url.get_secret_value()).set(drivername="postgresql+psycopg")


def connection_args():
    # No persistent session SET/options: transaction poolers may switch servers.
    return {"prepare_threshold": None, "connect_timeout": 5}


class Database:
    def __init__(self, settings: Settings):
        self.engine = create_async_engine(
            database_url(settings),
            poolclass=NullPool,
            connect_args=connection_args(),
            echo=False,
            hide_parameters=True,
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

        @event.listens_for(self.engine.sync_engine, "begin")
        def transaction_settings(connection):
            connection.exec_driver_sql(
                "SELECT set_config('statement_timeout','10s',true), "
                "set_config('lock_timeout','3s',true), set_config('TimeZone','UTC',true)"
            )

    async def probe(self):
        async with self.engine.connect() as connection:
            revision = await connection.scalar(
                text(
                    "SELECT version_num FROM gateway.alembic_version "
                    "WHERE (SELECT count(*) FROM "
                    "(SELECT id FROM gateway.users LIMIT 0) accessible_users)=0"
                )
            )
            if revision != REVISION:
                raise RuntimeError("Database migration revision mismatch")

    async def close(self):
        await self.engine.dispose()


async def get_session(request: Request):
    database = request.app.state.database
    if database is None:
        raise GatewayError(503, "DATABASE_NOT_READY", "The database is not ready.")
    async with database.sessions() as session:
        yield session
