"""Run schema migration or drift check without leaking connection diagnostics."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["upgrade", "check", "current"])
    args = parser.parse_args()
    try:
        config = Config(str(Path(__file__).resolve().parent.parent / "alembic.ini"))
        if args.action == "upgrade":
            command.upgrade(config, "head")
        elif args.action == "check":
            command.check(config)
        else:
            command.current(config)
        print(json.dumps({"check": "migration_" + args.action, "status": "PASS"}))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "check": "migration_" + args.action,
                    "status": "FAIL",
                    "error_type": type(exc).__name__,
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
