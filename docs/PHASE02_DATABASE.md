# Phase02 — PostgreSQL implementation and verification

The Supabase database configured privately in `.env` now contains six application tables in
schema `gateway`, plus `gateway.alembic_version`. Revision: `0001_gateway`.
`app/db/models.py` provides ORM mappings; the immutable Alembic revision owns DDL.
The design SQL is a reference, not a second migration command.

## Reproduce

Run from the repository root with its Python3.12 venv:

```powershell
& .\.venv\Scripts\python.exe scripts/migrate.py upgrade
& .\.venv\Scripts\python.exe scripts/migrate.py check
& .\.venv\Scripts\python.exe scripts/seed.py
& .\.venv\Scripts\python.exe scripts/verify_database.py
& .\.venv\Scripts\python.exe scripts/verify_restart.py
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m app
```

The live verification commands explicitly access the configured Supabase database.
Constraint fixtures run inside a rolled-back transaction; existing records are preserved.
Seed creates absent accounts and preserves existing UUIDs, active flags and hashes.
Changing a configured password does not reset an existing account's password.
For another clean database, supply a new connection URL and run the migration/seed commands.
The initial downgrade intentionally requires a separate reviewed backup/removal plan.

## Passwords and account access

Two accounts: `reviewer` and `other-reviewer` (unless usernames were configured differently).
Missing seed passwords were generated privately into `.env` as `DEMO_PASSWORD` and
`SECOND_TEST_PASSWORD`; no plaintext or hash was printed or committed. Argon2id hashes
are stored in PostgreSQL. Read the passwords locally when auth is implemented in Phase03.
Passwords must contain16–256 characters for this seed command.

## Connection policy

Local/migration uses the configured Supabase Session pooler. SQLAlchemy uses psycopg,
NullPool, disabled prepared statements, connect timeout5s, transaction-local statement
timeout10s/lock timeout3s and UTC timezone. All ORM tables are explicitly schema-qualified.
Transaction-local settings avoid relying on session state when using transaction pooling later.
NullPool closes application connections; Supabase provides the external pool.

`/health/ready` checks connectivity, migration revision and users table accessibility;
total budget5s, safe503 errors on failure. No provider inference or migrations on startup.
The Windows runner explicitly selects a Selector event loop, since Uvicorn otherwise
overrides the asyncio policy with Proactor, which psycopg async cannot use.

## Security and limits

`gateway` schema/table privileges are revoked from PUBLIC, anon and authenticated;
six tables have RLS enabled with no direct-client policies. Live checks verify role
privileges and RLS. Keep `gateway` out of Supabase exposed schemas; dashboard exposure
settings were not independently read, while denied schema/table grants were verified.
Backend uses the privileged database credential currently supplied by the user, which
can bypass RLS. Gateway owner checks and JWT auth are added in later phases; a dedicated
least-privilege backend DB role is a future hardening step.

## Evidence and deployment boundary

[Phase02 evidence](../artifacts/evidence/phase02.json) covers migration, constraints,
security grants, Argon2id verification, repeated seed and fresh app/process readiness/persistence.
The normal pytest suite runs without external credentials; live checks are separate.

The current public Vercel deployment is the Phase01 skeleton. Cloud DB credentials and
Phase02 release are not deployed by this phase; its readiness stays503 until that happens.
Auth/chat/analyze/history/usage/ledger/retry/limiter remain later work.
