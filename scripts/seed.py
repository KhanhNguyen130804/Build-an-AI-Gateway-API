"""Seed two configured users, reporting no passwords or password hashes."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import load_settings  # noqa: E402
from app.db.seed import seed_users  # noqa: E402
from app.db.session import Database  # noqa: E402


async def run():
    database = Database(load_settings())
    try:
        result = await seed_users(database, load_settings())
        print(json.dumps({"check": "seed", "status": "PASS", "users": result}))
    finally:
        await database.close()


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(run())
        return 0
    except Exception as exc:
        print(json.dumps({"check": "seed", "status": "FAIL", "error_type": type(exc).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
