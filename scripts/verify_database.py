"""Explicit live Phase02 acceptance; fixtures rollback, existing records are preserved."""

import asyncio
import json
import secrets
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
import psycopg  # noqa: E402
from pydantic import SecretStr  # noqa: E402
from sqlalchemy import select, text  # noqa: E402

from app.core.config import load_settings  # noqa: E402
from app.db.models import Base, User  # noqa: E402
from app.db.seed import password_hasher, seed_users  # noqa: E402
from app.db.session import REVISION, Database, database_url  # noqa: E402
from app.main import create_app  # noqa: E402


def verify_constraints(settings):
    passed = []
    dsn = database_url(settings).set(drivername="postgresql").render_as_string(hide_password=False)
    with psycopg.connect(dsn, prepare_threshold=None, connect_timeout=5) as connection:
        rows = connection.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='gateway'"
        ).fetchall()
        expected = {table.name for table in Base.metadata.tables.values()}
        assert {row[0] for row in rows} == expected | {"alembic_version"}
        assert (
            connection.execute("SELECT version_num FROM gateway.alembic_version").fetchone()[0]
            == REVISION
        )
        passed.append("six_tables_and_revision")
        for role in ("anon", "authenticated"):
            if not connection.execute(
                "SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)
            ).fetchone():
                raise AssertionError("Expected Supabase role missing")
            assert not connection.execute(
                "SELECT has_schema_privilege(%s,'gateway','USAGE')", (role,)
            ).fetchone()[0]
            for table in expected:
                assert not connection.execute(
                    "SELECT has_table_privilege(%s,%s,'SELECT,INSERT,UPDATE,DELETE')",
                    (role, "gateway." + table),
                ).fetchone()[0]
        rls = connection.execute(
            "SELECT relname,relrowsecurity FROM pg_class c JOIN pg_namespace n "
            "ON n.oid=c.relnamespace WHERE n.nspname='gateway' AND c.relkind='r'"
        ).fetchall()
        assert all(enabled for name, enabled in rls if name in expected)
        passed.append("anon_authenticated_denied_and_rls_enabled")

        def reject(sql, args, expected_code, label):
            try:
                with connection.transaction():
                    connection.execute(sql, args)
            except psycopg.Error as exc:
                assert exc.sqlstate == expected_code
                passed.append(label)
            else:
                raise AssertionError("Invalid fixture accepted: " + label)

        with connection.transaction(force_rollback=True):
            connection.execute("SET LOCAL TIME ZONE 'UTC'")
            user1, user2, conv1, conv2, req1, req2 = [uuid4() for _ in range(6)]
            for user in (user1, user2):
                connection.execute(
                    "INSERT INTO gateway.users(id,username,password_hash) VALUES (%s,%s,%s)",
                    (
                        user,
                        "phase02-test-" + str(user),
                        password_hasher.hash(secrets.token_urlsafe(24)),
                    ),
                )
            for conv, user in ((conv1, user1), (conv2, user2)):
                connection.execute(
                    "INSERT INTO gateway.conversations(id,user_id) VALUES (%s,%s)", (conv, user)
                )
            request_sql = (
                "INSERT INTO gateway.ai_requests(id,user_id,conversation_id,operation,"
                "requested_provider,requested_model,status) "
                "VALUES (%s,%s,%s,'chat','test','fixture','pending')"
            )
            connection.execute(request_sql, (req1, user1, conv1))
            connection.execute(request_sql, (req2, user2, conv2))
            reject(request_sql, (uuid4(), user2, conv1), "23503", "request_owner_fk")
            connection.execute(
                "UPDATE gateway.conversations SET in_flight_request_id=%s WHERE id=%s",
                (req1, conv1),
            )
            reject(
                "UPDATE gateway.conversations SET in_flight_request_id=%s WHERE id=%s",
                (req2, conv1),
                "23503",
                "conversation_claim_owner_fk",
            )
            msg_sql = (
                "INSERT INTO gateway.messages(id,conversation_id,user_id,request_id,"
                "sequence_number,role,content) "
                "VALUES (%s,%s,%s,%s,%s,%s,'synthetic test')"
            )
            connection.execute(msg_sql, (uuid4(), conv1, user1, req1, 1, "user"))
            reject(
                msg_sql, (uuid4(), conv1, user1, req1, 1, "assistant"), "23505", "unique_sequence"
            )
            reject(
                msg_sql, (uuid4(), conv1, user1, req1, 2, "user"), "23505", "unique_request_role"
            )
            reject(
                msg_sql, (uuid4(), conv1, user2, req2, 2, "assistant"), "23503", "message_owner_fk"
            )
            reject(
                msg_sql,
                (uuid4(), conv1, user1, req2, 2, "assistant"),
                "23503",
                "message_request_owner_fk",
            )
            reject(
                msg_sql, (uuid4(), conv1, user1, req1, 0, "assistant"), "23514", "positive_sequence"
            )
            reject(
                "UPDATE gateway.ai_requests SET input_tokens=-1 WHERE id=%s",
                (req1,),
                "23514",
                "nonnegative_tokens",
            )
            reject(
                "UPDATE gateway.ai_requests SET status='succeeded' WHERE id=%s",
                (req1,),
                "23514",
                "terminal_timing_required",
            )
            reject(
                "INSERT INTO gateway.provider_attempts(id,request_id,attempt_number,provider,"
                "requested_model,status,usage_known) "
                "VALUES (%s,%s,1,'test','fixture','started',true)",
                (uuid4(), req1),
                "23514",
                "known_usage_requires_tokens",
            )
            created_at = connection.execute(
                "SELECT created_at FROM gateway.users WHERE id=%s", (user1,)
            ).fetchone()[0]
            assert created_at.utcoffset().total_seconds() == 0
            passed.append("utc_timestamps")
        assert not connection.execute(
            "SELECT 1 FROM gateway.users WHERE id=%s", (user1,)
        ).fetchone()
        passed.append("test_fixtures_rolled_back")
    return passed


async def verify_application(settings):
    database = Database(settings)
    try:
        async with database.sessions() as session:
            users = (
                await session.scalars(
                    select(User).where(
                        User.username.in_([settings.demo_username, settings.second_test_username])
                    )
                )
            ).all()
            assert len(users) == 2
            before = {u.username: (u.id, u.password_hash) for u in users}
            for name, secret in (
                (settings.demo_username, settings.demo_password),
                (settings.second_test_username, settings.second_test_password),
            ):
                assert password_hasher.verify(secret.get_secret_value(), before[name][1])
                assert before[name][1].startswith("$argon2id$")
            assert await session.scalar(text("SHOW TIME ZONE")) == "UTC"
        changed = settings.model_copy(
            update={"demo_password": SecretStr(secrets.token_urlsafe(24))}
        )
        results = await seed_users(database, changed)
        assert all(result["status"] == "PRESERVED" for result in results)
        async with database.sessions() as session:
            users = (await session.scalars(select(User).where(User.username.in_(before)))).all()
            assert {u.username: (u.id, u.password_hash) for u in users} == before
    finally:
        await database.close()
    statuses = []
    for _ in range(2):
        app = create_app(settings)
        try:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://local"
            ) as client:
                response = await client.get("/health/ready")
                assert response.status_code == 200
                assert response.json() == {"status": "ready"}
                statuses.append(response.status_code)
            async with app.state.database.sessions() as session:
                count = len(
                    (await session.scalars(select(User).where(User.username.in_(before)))).all()
                )
                assert count == 2
        finally:
            await app.state.database.close()
    return {
        "argon2_hashes_verified": True,
        "repeat_seed_preserves_ids_and_hashes": True,
        "fresh_app_instances_readiness": statuses,
        "persisted_users_after_recreation": 2,
    }


def main():
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        settings = load_settings()
        constraints = verify_constraints(settings)
        application = asyncio.run(verify_application(settings))
        evidence = {
            "checked_at_utc": datetime.now(UTC).isoformat(),
            "status": "PASS",
            "revision": REVISION,
            "database_checks": constraints,
            **application,
            "scope": "Real Supabase migration/seed/constraints and fresh local app instances; "
            "no LLM call",
        }
        target = Path(__file__).resolve().parent.parent / "artifacts/evidence/phase02.json"
        target.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(evidence))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {"check": "phase02_live", "status": "FAIL", "error_type": type(exc).__name__}
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
