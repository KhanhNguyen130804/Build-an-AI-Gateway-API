"""Vercel's ASGI entrypoint; no database migration or paid inference at import."""

from app.core.config import load_settings
from app.core.logging import configure_logging
from app.main import create_app

settings = load_settings()
configure_logging(settings.log_level, settings.redaction_values())
app = create_app(settings)
