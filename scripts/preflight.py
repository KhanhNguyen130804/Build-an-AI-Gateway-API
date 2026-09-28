"""Check access explicitly without printing credentials or running probes on startup.

Default: configuration/import checks only. --provider performs one paid inference.
--database performs SELECT 1 only; neither flag creates or changes database objects.
"""

import argparse
import asyncio
import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import ConfigurationError, Settings, load_settings  # noqa: E402


async def check_provider(settings: Settings) -> dict:
    if not settings.openai_api_key or not settings.openai_model:
        return {
            "check": "provider",
            "status": "NOT_CONFIGURED",
            "required": ["OPENAI_API_KEY", "OPENAI_MODEL"],
        }

    from openai import AsyncOpenAI, OpenAIError
    from pydantic import BaseModel

    class Result(BaseModel):
        ok: bool

    try:
        async with AsyncOpenAI(
            api_key=settings.openai_api_key.get_secret_value(), max_retries=0, timeout=10
        ) as client:
            async with asyncio.timeout(15):
                response = await client.responses.parse(
                    model=settings.openai_model,
                    input="Return the schema object with ok=true.",
                    text_format=Result,
                    max_output_tokens=256,
                    store=False,
                )
        if response.output_parsed is None or not response.output_parsed.ok:
            return {"check": "provider", "status": "FAIL", "reason": "No valid structured result"}
        usage = response.usage
        return {
            "check": "provider",
            "status": "PASS",
            "model": response.model,
            "provider_request_id": response._request_id,
            "input_tokens": usage.input_tokens if usage else None,
            "output_tokens": usage.output_tokens if usage else None,
        }
    except (OpenAIError, TimeoutError, ValueError) as exc:
        return {"check": "provider", "status": "FAIL", "error_type": type(exc).__name__}


async def check_database(settings: Settings) -> dict:
    if not settings.database_url:
        return {"check": "database", "status": "NOT_CONFIGURED", "required": ["DATABASE_URL"]}

    import psycopg
    from sqlalchemy.engine import make_url

    url = make_url(settings.database_url.get_secret_value()).set(drivername="postgresql")
    try:
        async with asyncio.timeout(10):
            async with await psycopg.AsyncConnection.connect(
                url.render_as_string(hide_password=False),
                connect_timeout=5,
                prepare_threshold=None,
                autocommit=True,
            ) as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute("SELECT 1")
                    row = await cursor.fetchone()
        return {"check": "database", "status": "PASS" if row == (1,) else "FAIL"}
    except (psycopg.Error, TimeoutError) as exc:
        return {"check": "database", "status": "FAIL", "error_type": type(exc).__name__}


async def checks(settings: Settings, provider: bool, database: bool) -> int:
    failed = False
    for enabled, check in ((provider, check_provider), (database, check_database)):
        if enabled:
            result = await check(settings)
            print(json.dumps(result))
            failed |= result["status"] != "PASS"
    return 2 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider", action="store_true", help="One real, potentially paid LLM call"
    )
    parser.add_argument("--database", action="store_true", help="Read-only PostgreSQL SELECT 1")
    args = parser.parse_args()
    try:
        settings = load_settings()
    except ConfigurationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    modules = (
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "greenlet",
        "psycopg",
        "alembic",
        "openai",
        "jwt",
        "pwdlib",
    )
    for module in modules:
        importlib.import_module(module)
    print(json.dumps({"check": "imports", "status": "PASS", "modules": modules}))
    print(
        json.dumps(
            {
                "check": "configuration",
                "status": "PASS",
                "environment": settings.app_env,
                "database_configured": bool(settings.database_url),
                "provider_configured": bool(settings.openai_api_key and settings.openai_model),
            }
        )
    )
    if sys.platform == "win32":
        # Psycopg async does not support Windows' default Proactor loop.
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    return asyncio.run(checks(settings, args.provider, args.database))


if __name__ == "__main__":
    raise SystemExit(main())
