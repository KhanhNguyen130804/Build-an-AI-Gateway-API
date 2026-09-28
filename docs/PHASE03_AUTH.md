# Phase03 — authentication and owner boundary

Phase03 implements seeded-user JSON login, HS256 JWTs, active-user bearer validation, and an owner-scoped conversation query primitive. It does not add public registration, refresh/revocation, login rate limiting, or AI endpoints.

## Local use

Run the app with the configured private `.env`:

```powershell
& .\.venv\Scripts\python.exe -m app
```

In Swagger, call `POST /v1/auth` with the seeded username/password, copy `access_token` into **Authorize** as a Bearer token, then call `GET /v1/auth/me`. The identity response contains only the database UUID and username. Login accepts JSON, not OAuth2 password-flow form data.

Login errors for unknown usernames, wrong passwords, and inactive users share the same status and message. Unknown names still incur a dummy Argon2id verification. Passwords are constrained to 16–256 characters when seeding and 1–256 characters at login. Login rate limiting is planned for Phase08.

## Token rules

- Algorithm is fixed to HS256; no client-selected algorithm is accepted.
- Required claims are `sub`, `iat`, `exp`, `iss`, and `aud`.
- `sub` is the seeded user's UUID. Issuer, audience, and TTL come from settings.
- Every protected request checks the JWT and reloads the user as active. Missing, malformed, expired, wrong-signature, wrong-issuer/audience, unknown-user, and inactive-user tokens return the same 401 bearer error.
- `JWT_SECRET` must be at least 32 characters. Production already rejects missing auth configuration at startup.

Future resource handlers must pass the authenticated user's UUID to owner-filtered queries. `get_owned_conversation` filters by both conversation ID and owner ID, returning the same 404 for absent and foreign conversations. Conversation HTTP endpoints and full cross-user integration are part of Phase05.

## Verification

The unit suite covers successful login/token claims, invalid account cases, missing and invalid JWT variants, inactive/unknown database users, payload validation, and owner-filter SQL behavior:

```powershell
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m ruff check app tests scripts migrations
```

For a real read-only check against the already seeded database, run:

```powershell
& .\.venv\Scripts\python.exe scripts/verify_auth.py
```

It uses `DEMO_USERNAME`/`DEMO_PASSWORD` from `.env`, makes read-only database queries, and calls no LLM. It writes sanitized results to `artifacts/evidence/phase03.json`; it never prints credentials or the bearer token. This does not verify deployed auth: Vercel still serves the Phase01 skeleton.
