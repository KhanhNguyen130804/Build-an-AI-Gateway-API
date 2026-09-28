# Environment and deployment runbook

**Current:** Phase01 Vercel skeleton public smoke PASS at [Swagger](https://ai-gateway-challenge.vercel.app/docs); GitHub source pushed. Phase02 real Supabase migration/seed/readiness verified locally; cloud DB credentials/Phase02 release not configured. Selected path: Supabase + Vercel + OpenAI. Deploy uses Vercel CLI; Git auto-deploy connection failed and remains pending. Runtime Python3.12; Docker/uv/gh not in PATH. Earlier inventory rows below are historical Phase01 preparation; use PHASE_TASKS.md for current acceptance.

## Readiness inventory

| Dependency | Observed status | Next action |
|---|---|---|
| Workspace | FastAPI Phase01 foundation implemented/tested | Phase02 database integration next |
| Git executable | Repository initialized locally | No commit/remote/push yet |
| Node/npm | Available, Node24.19 | Optional tooling only; not backend runtime |
| Python project runtime | `.venv`3.12.14, dependency imports/20 tests pass | Verify Linux/Vercel build later |
| Docker Desktop | Not in PATH | Optional; managed PostgreSQL is an alternate local/test DB path |
| PostgreSQL | Supabase selected; no DB URL/connection verified | Create project, copy pooler URL, read-only probe |
| LLM key/model/credit | OpenAI selected; key not created | Create project key, configure env, live structured-output probe |
| Deployment account/budget | Vercel selected; user has not used it before | Entry point/config prepared; account access and budget not verified |
| GitHub repository | Not created | Create/push when implementing; consider anonymous-review implications |
| Reviewer/video links | Not available | Fill only after verification |

Do not equate “no env var in this shell” with “no account/key exists.” Do not install a large toolchain just to proceed with planning.

## Project commands

Install/start commands now exist and are verified locally. Migration/seed commands below remain future Phase02 deliverables; do not execute until created. Preserve existing `.env` rather than overwriting it.

```powershell
# Run a chosen project Python executable, then activate the project environment.
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python scripts/bootstrap_env.py
# Configure .env privately, then:
alembic upgrade head
python -m app.scripts.seed_demo
python -m app
```

If Python is not on PATH, use the verified project executable with PowerShell's call operator `&`. Avoid weakening machine-wide execution policy merely to activate a venv; executing `.venv\Scripts\python.exe` directly is an alternative. Lock dependencies after installation and run clean-checkout verification with the same Python version. Linux deploy must verify wheels for psycopg and Argon2, not just Windows imports.

Expected quality commands after files exist: `python -m pytest`, migration on a clean test DB, explicit live smoke test. Choose a minimal dependency lock approach and document it; do not generate an untested version list in the plan.

## Railway path — previous alternative, not selected

Railway officially supports FastAPI deployments from GitHub/CLI/Dockerfile, with public URL generated in Networking. PostgreSQL can be provisioned alongside the web service with service reference variables. [FastAPI deployment guide](https://docs.railway.com/guides/fastapi), [PostgreSQL guide](https://docs.railway.com/databases/postgresql).

This is a deployment path, not a claim about free pricing, account eligibility or available credit. Verify current pricing and account limits before provisioning. If another host is already available, reuse it with the same web+Postgres design; do not switch hosts just for appearance.

The selected Vercel/Supabase path is in GETTING_STARTED.md. The steps below apply only if the host selection changes explicitly.

1. Deploy the minimal health/docs skeleton. Build/install must use a pinned dependency lock. Containerized build on host does not require Docker Desktop on this computer.
2. Add PostgreSQL with persistent storage. Use the host's recommended private service connection where available; local/test access uses its supported secure endpoint. Confirm TLS/network settings instead of disabling certificate checks to fix errors.
3. Inject secrets via host variables: database URL, provider key, model, JWT/hash secrets, caps and seed passwords. Validate required variables at application startup, with redacted errors.
4. Normalize a provider PostgreSQL URL to SQLAlchemy's selected driver (`postgresql+psycopg://`) in config without printing credentials. Verify async engine connection; do not assume the host's URL scheme already selects the right driver.
5. Apply `alembic upgrade head` as a single pre-deploy/release operation. Do not run schema mutation concurrently in every web worker. For a one-instance MVP, record the manual migration step if no release hook exists.
6. Run a one-off idempotent seed command. It creates users only when absent; no surprise password overwrite on every start. Disable/remove seed passwords from runtime variables if no longer needed.
7. Start Uvicorn bound to `0.0.0.0` and the host's injected port. Start with one worker; limiter/claims still live in PostgreSQL. Verify process startup and proxy timeout can accommodate the 30-second app budget.
8. Configure readiness route, public HTTPS domain and restart policy. Verify `/docs`, `/openapi.json`, auth and DB externally, then real LLM smoke.
9. Record deployed commit/version, model, sanitized request IDs and links. Run restart/persistence check.

## Reviewer access and cost

- Seed reviewer account; password is intentionally shared for demo access only after release. This is distinct from provider keys or admin credentials. Document how to obtain/reuse it and the quota limits.
- Shared accounts share history and usage. Use synthetic tickets only and disclose this limitation. Do not send company/customer personal data.
- Initial safety caps: 10 AI operations/minute/user, 100/day/user, 300/day gateway, up to3 attempts per admitted operation. These are conservative defaults pending budget and reviewer concurrency, not a promise that100 reviewers can all call the same demo account unrestricted.
- Account/provider spend limits provide additional control; operation caps alone cannot guarantee an exact dollar ceiling. Check actual billing settings instead of inventing a price estimate.
- Keep API and video accessible at least through **08/10/2026**, then until any actual review window completes. Check that the chosen host's storage/service policy will not expire earlier.
- Healthchecks must not call the LLM. Never auto-seed a paid provider call on every deploy or heartbeat.

## Rollback / provider failure

Record the last verified deploy before a release. If regression appears, revert web service to that version after confirming migration compatibility; do not blindly downgrade a destructive migration. Prefer additive migrations in the challenge period. If provider credit runs out, restore access or clearly report unavailability; never replace live inference with canned responses and call it working integration.

Video is evidence and a fallback for temporary review connectivity, not a substitute for the required deployed API. Re-run production smoke after any fix affecting provider/auth/database/limits.

## Final operational checklist

- [ ] Dependency versions/lockfile and Python version verified in deploy.
- [ ] DB persistent, migrations applied once, credentials not logged.
- [ ] JWT expires and owner checks enforced on live API.
- [ ] Actual supported model/schema smoke passed; provider retry disabled in SDK.
- [ ] Deadline/limits and safe errors checked.
- [ ] HTTPS URL and docs externally accessible.
- [ ] Reviewer account access and budget caps appropriate.
- [ ] Review-period availability confirmed; links published only when ready.
