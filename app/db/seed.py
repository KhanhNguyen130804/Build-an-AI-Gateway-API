"""One-off idempotent seed. Existing identities and hashes are never overwritten."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.config import Settings
from app.core.passwords import password_hasher
from app.db.models import User
from app.db.session import Database


async def seed_users(database: Database, settings: Settings):
    entries = (
        (settings.demo_username, settings.demo_password),
        (settings.second_test_username, settings.second_test_password),
    )
    if entries[0][0] == entries[1][0]:
        raise ValueError("Seed usernames must differ")
    if any(
        not name
        or len(name) > 100
        or not secret
        or not 16 <= len(secret.get_secret_value()) <= 256
        for name, secret in entries
    ):
        raise ValueError("Seed requires usernames and passwords of 16 to 256 characters")
    result = []
    async with database.sessions.begin() as session:
        for name, secret in entries:
            existing = await session.scalar(select(User).where(User.username == name))
            if existing is not None:
                result.append({"username": name, "status": "PRESERVED"})
                continue
            hashed = password_hasher.hash(secret.get_secret_value())
            inserted = await session.scalar(
                insert(User)
                .values(username=name, password_hash=hashed)
                .on_conflict_do_nothing(index_elements=[User.username])
                .returning(User.id)
            )
            result.append({"username": name, "status": "CREATED" if inserted else "PRESERVED"})
    return result
