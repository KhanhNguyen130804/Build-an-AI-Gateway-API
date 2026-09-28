"""Create a private development .env without overwriting existing credentials."""

import secrets
from pathlib import Path

root = Path(__file__).resolve().parent.parent
target = root / ".env"
if target.exists():
    print("Existing .env preserved.")
else:
    content = (root / ".env.example").read_text(encoding="utf-8")
    for name in ("JWT_SECRET", "RATE_LIMIT_HASH_SECRET"):
        content = content.replace(f"{name}=\n", f"{name}={secrets.token_hex(32)}\n")
    # Exclusive creation avoids a race that could overwrite an existing config.
    with target.open("x", encoding="utf-8") as handle:
        handle.write(content)
    print("Created private development .env; DB and provider access still need configuration.")
