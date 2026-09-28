import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    def __init__(self, secret_values: tuple[str, ...] = ()):
        super().__init__()
        self.secret_values = tuple(sorted(filter(None, secret_values), key=len, reverse=True))

    def redact(self, value: str) -> str:
        for secret in self.secret_values:
            value = value.replace(secret, "[REDACTED]")
        return re.sub(r"(?i)\bbearer\s+[^\s\"']+", "Bearer [REDACTED]", value)

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": self.redact(record.getMessage()),
        }
        request_id = getattr(record, "request_id", None) or request_id_context.get()
        if request_id:
            data["request_id"] = request_id
        for key in ("method", "route", "status", "latency_ms", "error_type"):
            if (value := getattr(record, key, None)) is not None:
                data[key] = self.redact(value) if isinstance(value, str) else value
        # Never append exc_info, request bodies, headers or arbitrary record extras.
        return json.dumps(data, ensure_ascii=False)


def configure_logging(level: str, secret_values: tuple[str, ...] = ()) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter(secret_values))
    logging.basicConfig(level=level, handlers=[handler], force=True)
    for name in ("httpx", "httpcore", "httpx2", "httpcore2", "openai", "sqlalchemy.engine"):
        logging.getLogger(name).setLevel(logging.WARNING)
