from alembic import context
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

from app.core.config import load_settings
from app.db.models import Base
from app.db.session import connection_args, database_url


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name == "gateway"
    return True


def run():
    settings = load_settings()
    common = dict(
        target_metadata=Base.metadata,
        version_table_schema="gateway",
        include_schemas=True,
        include_name=include_name,
        compare_type=True,
    )
    if context.is_offline_mode():
        context.configure(url=database_url(settings), literal_binds=True, **common)
        context.execute("CREATE SCHEMA IF NOT EXISTS gateway")
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = create_engine(
        database_url(settings),
        poolclass=NullPool,
        connect_args=connection_args(),
        hide_parameters=True,
    )
    try:
        with engine.begin() as connection:
            connection.execute(text("SET LOCAL lock_timeout = '5s'"))
            connection.execute(text("SET LOCAL statement_timeout = '30s'"))
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS gateway"))
            context.configure(connection=connection, **common)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


run()
