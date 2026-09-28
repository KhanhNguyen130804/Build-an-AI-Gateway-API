# AI worklog

This is an evidence log, not a list of planned accomplishments. Status labels: PREPARED, VERIFIED, NOT RUN, BLOCKED. Update after each real development session. Do not invent incorrect AI outputs or hours saved to satisfy the rubric.

## Session 001 — preparation, 28/09/2026 (Asia/Saigon)

**Tool used:** Codex in the desktop app, with official documentation browsing and local file/preflight tools. OpenAI Docs skill was used to check API guidance. No provider inference was invoked from this project.

**Actual user prompt/context:** detailed planning/readiness request for the AI Gateway challenge, with complete requirements and two submission screenshots. User subsequently asked for FastAPI/NestJS comparison and chose **Python + FastAPI**. The concise prompt description is P00 in `docs/PROMPTS.md`; retain the actual user prompt when filling the submission field.

**How AI helped:** mapped requirements to backlog/evidence, compared stacks, designed request-vs-attempt telemetry, bounded retry/timeout, ownership, rate limiting and metrics; prepared architecture/schema/API/examples/verification/deployment/submission documents.

**Verification performed so far:** checked workspace and instruction files; workspace had no existing project files or local `.git`. Git and Node/npm available in PATH. Python/Docker/uv/gh not found in PATH. Bundled artifact-support Python3.12.14 exists by absolute path. No relevant LLM/DB credential variable names were present in the inspected shell; values were not printed. Opened official OpenAI structured-output/rate-limit/error docs, FastAPI and NestJS docs, and Railway deployment/DB docs. API/model account access, database connectivity and deployment remain **NOT RUN**.

**Incorrect outputs / corrections:** the first backlog draft labeled its total26h although its task estimates summed to24.5h. Review caught this planning error; the estimates for integration/security verification and deployment were increased from2.5/2h to3.5/2.5h to allocate the intended26h realistically. A subsequent arithmetic check confirmed26h. This is an actual planning correction, not an application bug. No application code has been generated or verified yet. The initial proposed stack was tentative; runtime readiness needed additional investigation and the framework was finalized only after the user's choice. Suspected risks (duplicate retries, fake0 token usage, insecure owner queries) are review targets, not invented incidents.

**Artifact checks — VERIFIED for preparation only:** ran `node scripts/build_planning_artifacts.mjs`; generated8 API operations and10 Postman examples, with local references and endpoint mapping checked. Python checks confirmed JSON parsing, Markdown file links, blank exported secret/session variables, three labeled synthetic tickets,26h backlog arithmetic, usage fixture arithmetic, schema required-field references, input limits/enums, protected/public declarations, correlation headers and six-table design. Full OpenAPI/SQL conformance validation was not run; database/application/provider/deployment tests remain NOT RUN. No project dependency installation, account provisioning, commit/push, deployment or submission occurred.

**Implementation completed:** none. **Prepared:** planning and design artifacts. **Limitations:** no app, provider call, schema migration, test suite, repository push, deployed link or demo yet.

## Session 002 — project assessment and phase checklist, 28/09/2026

**Actual request:** review the current project state and create one detailed file of work organized by phase.

**Tool used:** Codex, local filesystem/runtime inspection and file editing. No new provider integration or paid inference was run.

**Observed state:**18 preparation files at the start of this session. `app/`, `.venv`, `tests/`, `migrations/`, `alembic.ini`, dependency files, `Dockerfile`, `.env` and workspace `.git` were absent. Bundled artifact-support Python3.12.14 was checked again. DB/provider/deployment connectivity remains NOT RUN.

**Output:** `PHASE_TASKS.md`, with an assessed baseline, completed assessment phase00, pending implementation phases01–13, task IDs, dependencies, outputs, acceptance criteria, external inputs and release milestones. Effort remains26h plus4h contingency; available working hours still need confirmation. README now links to this checklist.

**Preparation verification:** checked92 unique checkbox tasks, with4 completed assessment tasks and88 pending implementation tasks. All local file links resolve; the13 implementation phase estimates sum to26h. These are document checks, not application test results.

**Limit:** task checkboxes describe future work, not verified application behavior. No runtime setup, backend implementation, repository creation, deployment or submission happened in this session.

## Session 003 — Phase01 local implementation, 28/09/2026

**Actual prompt:** “bắt đầu thực hiện pharse”. User confirmed OpenAI (key not created), Supabase PostgreSQL and Vercel, with no previous experience configuring the latter services.

**Tool used:** Codex, PowerShell/Python local tools, pip and official OpenAI/FastAPI/Pydantic/SQLAlchemy/psycopg/Supabase/Vercel documentation. No project LLM inference was made.

**AI contribution accepted:** Python3.12 venv, pinned runtime/dev dependencies, FastAPI factory and local/Vercel entrypoints, safe configuration, request correlation, bounded body handling, structured error responses, JSON logs with redaction, live/readiness endpoints, explicit opt-in provider/DB probes and beginner setup guide. Git initialized locally; no commit/push/deploy/submission.

**Actual errors and corrections:** `SDK_MAX_RETRIES=0` from a dotenv file is a string; the original `Literal[0]` validator rejected it. Replaced it with a constrained integer accepting only0 and added a regression test reading `.env.example`. The initial dependency set omitted greenlet needed for SQLAlchemy async usage; switched to `sqlalchemy[asyncio]`, regenerated both locks, and verified imports/dependency consistency. Windows psycopg async requires the selector event loop; the local runner/probe now configure it following official documentation.

**VERIFIED:**20 local foundation tests pass, including controlled readiness success/failure/timeout, malformed/invalid inputs,413 limits, safe500 errors, concurrent request IDs, logs and configuration. Ruff passes; imports and pip check pass; the project wheel builds/installs. Actual localhost HTTP: live/docs/OpenAPI200, readiness503, missing business route404, correlated response headers. [Evidence](artifacts/evidence/phase01.json). Tests use controlled probes and prove foundation behavior only.

**Remaining work:** actual OpenAI inference, Supabase connection/migrations, auth/chat/analyze/history/usage/ledger/retry/rate limiting, Vercel build/deploy and full challenge acceptance remain NOT RUN. Dockerfile is prepared; no container build was performed. `.env` is private and ignored; no secret values appear in this log. Phase01 P01.01–06 verified, P01.07–08 pending external configuration. No defensible hours-saved measurement recorded.

## Session 004 — requested live preflight, 28/09/2026

**Actual request:** run the configuration, Supabase and OpenAI preflight commands on the user's behalf.

**VERIFIED:** imports/configuration PASS; actual Supabase `SELECT 1` PASS. No schema or data changes. Provider probe returned NOT_CONFIGURED without dispatching inference. A safe presence-only settings check confirmed OpenAI key present and model absent; no credential values printed. [Evidence](artifacts/evidence/preflight-20260928.json). Provider access/billing/structured output remains unverified until `OPENAI_MODEL` is configured and the probe succeeds.

## Session 005 — successful real OpenAI probe, 28/09/2026

**Actual user update:** “đã lưu model”, following the authorized request to execute the provider check.

**VERIFIED:** `python scripts/preflight.py --provider` exited0. Imports/configuration PASS; a real Responses API call returned the validated structured object with `ok=true`. Returned model was `gpt-6-luna`, input43/output12 tokens, request ID recorded in [evidence](artifacts/evidence/provider-20260928.json). The configured model was not changed by the assistant. This verifies provider access for this probe, not gateway endpoints, ledger, retries or deployment. Earlier NOT_CONFIGURED results remain historical evidence.

## Session 006 — GitHub publication and Vercel setup, 28/09/2026

**Actual request:** complete Phase01 before Phase02; user supplied the GitHub repository URL.

**VERIFIED:** remote repository had no refs. Staged51 files, scanned staged diff against configured secret values and checked `.env`/venv exclusion: PASS. Re-ran20 tests and Ruff: PASS. Created initial commit `24bcec4` and pushed branch `main` to the supplied GitHub repository without force. Local commit used a generic project author for the challenge. Installed/invoked Vercel CLI60.1.3 through npx; account/deployment still being checked. Browser automation failed to initialize (sandbox helper error); no browser account actions were performed. Secret values were not printed or pushed. Vercel actual deployment remains pending; Phase02 not started.

## Session 007 — Phase01 Vercel acceptance, 28/09/2026

**Actual user context:** completed device authorization, showed Authorization Successful and asked the next step. CLI confirmed signed in.

**Execution/corrections:** first deploy failed because workspace folder name was not a valid Vercel project name. Retried with project `ai-gateway-challenge`; build and deploy succeeded. Automatic GitHub repository connection failed; source upload/CLI deploy succeeded independently. This is explicitly recorded, not treated as working auto-deploy.

**VERIFIED:** Vercel Python3.12 build succeeded; public alias `https://ai-gateway-challenge.vercel.app`. Unauthenticated HTTP smoke: live/docs/OpenAPI200, readiness503, missing business endpoint404; every response had UUID request correlation and errors matched body/header IDs. Runtime OpenAPI contains only two health endpoints. [Evidence](artifacts/evidence/vercel-phase01.json). Deployed source matches GitHub commit471a653 except harmless CLI-added ignore metadata. Cloud uses default development settings; private local `.env` was excluded and cloud provider/database credentials were not configured. Full release belongs to later phases. Phase01 P01.01–08 accepted, not full challenge completion.

## Development session template

Copy this section for each real session:

```text
Date/time:
Tool/model actually used:
Prompt ID + actual prompt or link:
Task and constraints:
AI output summary:
What was accepted and why:
Incorrect output actually observed:
Evidence of the mistake (file, log, test, official source):
How it was corrected:
Verification run + actual result:
Commit/version/evidence link:
Remaining limitations:
Time spent (actual):
Estimated manual baseline and basis (if measured):
```

## Time-savings measurement

No estimate recorded yet. Track actual session time. Compare a bounded task, such as adding a client integration against the gateway contract, with an explicitly stated manual baseline. Record hours saved as an estimate with assumptions, not as a measured result if no comparison exists. The submission field may remain blank if there is no defensible number.

## What to improve with seven more days — proposed, not completed

| Extra day | Proposed improvement | Evidence to seek |
|---|---|---|
| 1 | Review API keys per application, JWT revocation/rotation and tenant isolation | Key/tenant boundary tests and threat review |
| 2 | Second provider adapter and safe route/fallback policies | Provider outage tests; per-attempt model/cost accounting |
| 3 | Durable job queue for slow analysis with cancel/status API | Worker crash/restart tests, no duplicate committed jobs |
| 4 | Opt-in cache with user/prompt/model/schema scoping | Isolation and invalidation tests; measured latency savings |
| 5 | Distributed tracing, operational metrics and alerts | Request-to-provider traces; meaningful error/latency thresholds |
| 6 | Load tests and resilience drills | Measured capacity, p95 latency, quota and DB contention results |
| 7 | Data retention/deletion, reviewer UX and deployment hardening | Verified deletion, backup/restore and clean setup docs |

Revise this list to reflect gaps actually left in the submitted version.
