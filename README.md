# AI Gateway

**Status: Phase01 verified —8/8 tasks, 28/09/2026.** FastAPI health/docs, config, request correlation, error handling, JSON logging and body limits run locally and on Vercel;20 foundation tests pass. Real Supabase SELECT1 and OpenAI structured probes pass. Database integration/auth/LLM business endpoints are not implemented yet.

Planned product: a central authenticated API for chat and structured support-ticket analysis, with stored conversations and reliable usage metrics. Selected services: OpenAI, Supabase PostgreSQL and Vercel. Cloud currently runs a development skeleton without provider/DB credentials; production integration remains later work. Deploy uses CLI; automatic Git deploy is not connected.

Start with [PHASE_TASKS.md](PHASE_TASKS.md) for the current project assessment and execution checklist; [PLAN.md](PLAN.md) covers overall scope and requirements. **Selected stack: Python + FastAPI + PostgreSQL**, confirmed by the user during preparation. The earlier FastAPI/NestJS comparison is retained as decision context.

| Artifact | Purpose | Current status |
|---|---|---|
| [PHASE_TASKS.md](PHASE_TASKS.md) | Current assessment, phase task IDs, dependencies and acceptance gates | Phase01 complete8/8 |
| [Getting started](docs/GETTING_STARTED.md) | Local commands and OpenAI/Supabase/Vercel account setup | Prepared for selected services |
| [PLAN.md](PLAN.md) | Scope, time budget, milestones, backlog, requirement coverage | Prepared |
| [Stack comparison](docs/STACK_OPTIONS.md) | Tradeoffs, dependencies, proposed layouts | FastAPI selected |
| [Architecture](docs/ARCHITECTURE.md) | Diagrams, workflow, security and reliability decisions | Design |
| [Database](docs/DATABASE.md) and [schema.sql](db/schema.sql) | Data model, constraints, usage calculations | Design, not applied to a database |
| [API contract](docs/API.md) and [OpenAPI](docs/openapi.json) | Endpoints, schemas, error contract | Design, not a live API specification |
| [Postman collection](examples/ai-gateway.postman_collection.json) | Importable happy-path and authorization examples | Prepared; not exercised against a server |
| [Verification](docs/VERIFICATION.md) | Full acceptance plan |20 foundation tests pass; full T01–T24 still pending |
| [Deployment](docs/DEPLOYMENT.md) | Environment readiness, deployment and rollback runbook | Skeleton Vercel build/public smoke PASS; full release pending |
| [Submission](docs/SUBMISSION.md) | Demo script, form copy, README completion checklist | Draft with explicit placeholders |
| [Prompts](docs/PROMPTS.md) | Implementation/review prompts with clear outputs | Prepared; future prompts not yet used |
| [AI_WORKLOG.md](AI_WORKLOG.md) | Actual AI use, verification, corrections and evidence | Preparation + Phase01 evidence |
| [.env.example](.env.example) | Shared configuration inventory | Empty secret/model placeholders |

## Planned behavior

- `POST /v1/auth`: JSON username/password login for seeded users; short-lived bearer JWT.
- `POST /v1/ai/chat`: real provider call, server-owned conversation context, saved successful turns.
- `POST /v1/ai/analyze`: support ticket converted to validated structured JSON.
- `GET /v1/conversations` and `GET /v1/conversations/{id}`: data scoped to the authenticated owner.
- `GET /v1/usage`: request counts, known provider tokens, average latency, error rate and usage completeness.
- `/docs`, `/openapi.json`, `/health/live`, `/health/ready`: documentation and deployment checks.

## Submission links

Not available yet. Fill only after successful verification:

- Live skeleton/docs: [Swagger on Vercel](https://ai-gateway-challenge.vercel.app/docs) — Phase01 foundation only
- Source repository: [Build an AI Gateway API](https://github.com/KhanhNguyen130804/Build-an-AI-Gateway-API)
- Demo video, under five minutes: `[TODO_VIDEO_URL]`
- Verification evidence: `[TODO_EVIDENCE_PATH]`

## Running the product

Use Python3.12. In this workspace `.venv` and private `.env` already exist. From a new checkout, create a venv first, then:

```powershell
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
& .\.venv\Scripts\python.exe scripts/bootstrap_env.py
& .\.venv\Scripts\python.exe -m app
```

Open [local Swagger](http://127.0.0.1:8000/docs). Liveness returns200; readiness intentionally returns503 until Phase02 attaches a verified database probe. Business endpoints currently return404. Development may start without DB/provider access; production requires complete configuration.

```powershell
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe scripts/preflight.py
```

Verified on Windows/Python3.12.14:20 tests, Ruff, imports/pip check, local HTTP and wheel build. [Local evidence](artifacts/evidence/phase01.json), [Supabase probe](artifacts/evidence/preflight-20260928.json), [OpenAI probe](artifacts/evidence/provider-20260928.json), [Vercel Python3.12 build/public smoke](artifacts/evidence/vercel-phase01.json). Full clean-checkout/container/business integration verification is pending. Lock inputs are `requirements.in`/`requirements-dev.in`; pinned files are `requirements.txt`/`requirements-dev.txt`.

For conventional Uvicorn CLI use `uvicorn app.main:create_app --factory`; the local runner additionally sets JSON logging and a Windows-compatible asyncio policy. Vercel uses the separate `app.vercel:app` entrypoint.

The final README must explain the problem, architecture/workflow, database, API, AI usage, metrics, reliability, completed work and limitations. Use the checklist in `docs/SUBMISSION.md`; remove planning-only claims when their corresponding functionality is verified.
