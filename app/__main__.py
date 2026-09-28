import asyncio
import sys

import uvicorn

from app.core.config import ConfigurationError, load_settings
from app.core.logging import configure_logging
from app.main import create_app


def main() -> int:
    try:
        settings = load_settings()
    except ConfigurationError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    configure_logging(settings.log_level, settings.redaction_values())
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    uvicorn.run(
        create_app(settings), host="0.0.0.0", port=settings.port, access_log=False, log_config=None
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
