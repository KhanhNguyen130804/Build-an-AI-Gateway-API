# AI Gateway

**Status: Phase01–04 implemented locally, 29/09/2026.** Phase04 adds authenticated first-turn chat through an OpenAI Responses adapter with request/attempt ledger. The local suite reports 50 passing tests and Ruff passes; one controlled gateway smoke recorded a successful request/attempt in PostgreSQL. Continuation, message/history APIs, analysis, usage, retry policy and rate limiting remain future phases. Vercel was last evidenced as a Phase01 skeleton on 28/09; deployment was not rechecked or changed in this task.

Planned product: a central authenticated API for chat and structured support-ticket analysis, with stored conversations and reliable usage metrics. Selected services: OpenAI, Supabase PostgreSQL and Vercel. Current local runtime includes a one-turn chat; the full product and deployment remain incomplete. Historical Vercel evidence from 28/09 records a development skeleton without provider/DB credentials; current cloud state was not checked. Deploy previously used CLI; automatic Git deploy was not connected in that evidence.

Start with [PHASE_TASKS.md](PHASE_TASKS.md) for the current project assessment and execution checklist; [PLAN.md](PLAN.md) covers overall scope and requirements. **Selected stack: Python + FastAPI + PostgreSQL**, confirmed by the user during preparation. The earlier FastAPI/NestJS comparison is retained as decision context.

| Artifact | Purpose | Current status |
|---|---|---|
| [PHASE_TASKS.md](PHASE_TASKS.md) | Current assessment, phase task IDs, dependencies and acceptance gates | Phase01–04 local gates complete; Phase05 onward pending |
| [Getting started](docs/GETTING_STARTED.md) | Local commands and OpenAI/Supabase/Vercel account setup | Prepared for selected services |
| [PLAN.md](PLAN.md) | Scope, time budget, milestones, backlog, requirement coverage | Prepared |
| [Stack comparison](docs/STACK_OPTIONS.md) | Tradeoffs, dependencies, proposed layouts | FastAPI selected |
| [Architecture](docs/ARCHITECTURE.md) | Diagrams, workflow, security and reliability decisions | Design |
| [Phase03 auth guide](docs/PHASE03_AUTH.md) | Login, JWT, Swagger bearer, owner query and verification | Implemented locally; cloud release pending |
| [Database](docs/DATABASE.md), [Phase02 runbook](docs/PHASE02_DATABASE.md), [full changelog](docs/PHASE02_CHANGELOG.md) | ORM, migration, seed, constraints and verification | Applied and verified on Supabase; usage calculations still design |
| [API contract](docs/API.md) and [OpenAPI](docs/openapi.json) | Endpoints, schemas, error contract | Runtime has health, auth, and first-turn chat; remaining business routes are planned |
| [Postman collection](examples/ai-gateway.postman_collection.json) | Importable happy-path and authorization examples | First-turn chat is current; follow-up/examples remain planned; collection not run |
| [Verification](docs/VERIFICATION.md) | Full acceptance plan |50 local tests, Ruff, one Phase04 live gateway smoke PASS; full T01–T24 still pending |
| [Deployment](docs/DEPLOYMENT.md) | Environment readiness, deployment and rollback runbook | Skeleton Vercel build/public smoke PASS; full release pending |
| [Submission](docs/SUBMISSION.md) | Demo script, form copy, README completion checklist | Draft with explicit placeholders |
| [Prompts](docs/PROMPTS.md) | Implementation/review prompts with clear outputs | Prepared; future prompts not yet used |
| [AI_WORKLOG.md](AI_WORKLOG.md) | Actual AI use, verification, corrections and evidence | Preparation + Phase01–04 entries |
| [.env.example](.env.example) | Shared configuration inventory | Empty secret/model placeholders |

## Runtime and planned behavior

- `POST /v1/auth`: implemented JSON username/password login for seeded active users; short-lived bearer JWT.
- `GET /v1/auth/me`: implemented Bearer validation and current-user identity.
- `POST /v1/ai/chat`: implemented first-turn call to configured OpenAI model, creates a new conversation and writes request/attempt ledger. It does not accept a prior conversation or save messages yet.
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

Open [local Swagger](http://127.0.0.1:8000/docs). Liveness returns200; readiness returns200 when the configured DB and migration are accessible, otherwise503. `POST /v1/auth`, protected `GET /v1/auth/me`, and first-turn `POST /v1/ai/chat` are implemented. Chat requires bearer auth, PostgreSQL and provider configuration; continuation, message/history, analyze and usage endpoints remain planned. Development may start without DB/provider access; login needs DB and `JWT_SECRET`. Follow the [Phase02 runbook](docs/PHASE02_DATABASE.md) and [Phase03 auth guide](docs/PHASE03_AUTH.md).

```powershell
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe scripts/preflight.py
```

Phase01/03 results are historical. Current local verification on 29/09:50 pytest tests, Ruff, and one successful gateway-to-PostgreSQL/OpenAI smoke; see [AI_WORKLOG.md](AI_WORKLOG.md). Older [OpenAI probe](artifacts/evidence/provider-20260928.json) was a direct probe and did not prove gateway behavior. [Vercel evidence](artifacts/evidence/vercel-phase01.json) is from 28/09 and deployment was not rechecked. Full clean-checkout/container/T01–T24 verification is pending. Lock inputs are `requirements.in`/`requirements-dev.in`; pinned files are `requirements.txt`/`requirements-dev.txt`.

For conventional Uvicorn CLI use `uvicorn app.main:create_app --factory`; on Windows add `--loop asyncio:SelectorEventLoop` for psycopg async compatibility. The recommended `python -m app` runner sets the correct factory and JSON logging. Vercel uses `app.vercel:app`.

The final README must explain the problem, architecture/workflow, database, API, AI usage, metrics, reliability, completed work and limitations. Use the checklist in `docs/SUBMISSION.md`; remove planning-only claims when their corresponding functionality is verified.
