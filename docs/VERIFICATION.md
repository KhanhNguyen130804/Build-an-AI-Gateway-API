# Acceptance and evidence plan

**Full T01–T24 acceptance is still pending.**35 local pytest tests pass in the Phase03 implementation run: the 22 previously recorded foundation/seed tests plus auth, JWT, bearer, owner-query, and seed-length boundary cases. The separate [read-only Phase03 auth probe](../artifacts/evidence/phase03.json) passed against the seeded Supabase account; it makes no DB writes and no LLM calls. Historical evidence also covers [Supabase schema/constraints/grants/RLS/seed/restart](../artifacts/evidence/phase02.json), [OpenAI structured probe](../artifacts/evidence/provider-20260928.json) and [Vercel skeleton](../artifacts/evidence/vercel-phase01.json). The auth unit tests use an in-process fake session and do not prove live cloud deployment; chat/analyze/retry/usage/limiter behavior remains unimplemented. See [Phase02 commands](PHASE02_DATABASE.md).

Run meaningful tests against PostgreSQL rather than relying on SQLite behavior. Fake the provider adapter for deterministic errors/concurrency; keep a small explicit live-provider smoke test. Fake responses are test fixtures, never the production backend or an unlabeled demo.

## P0 test cases

| ID | Scenario | Expected result / evidence |
|---|---|---|
| T01 | Migrate empty PostgreSQL, seed two users, restart | Schema works; hashes only; no lost data; migrations repeat safely |
| T02 | Valid/invalid login; absent/expired/tampered JWT; wrong issuer/audience | Valid200; invalid401; WWW-Authenticate where applicable; no provider call |
| T03 | User A creates chat; user B reads or posts to A's conversation | Both blocked404; usage scoped; no messages/metadata leak |
| T04 | Chat twice with returned conversation_id | Second fake-adapter input contains first saved turn; messages ordered; no client system/user_id allowed |
| T05 | Two concurrent turns to same conversation | One obtains claim, other409; no mixed context/sequence; one provider call; rejected row recorded |
| T06 | Analyze valid ticket | Real supported schema; app validates enums/length; no additional fields; stored schema_version1 |
| T07 | Invalid JSON/output enums, refusal, incomplete response | 502/422/502 respectively; terminal row; available usage preserved; no fake success |
| T08 | Provider503 then200 | Exactly two dispatched attempts; one logical request; capped backoff; known token metadata kept |
| T09 | Three retryable503 errors | Attempts≤3; final502/503 according to classification; no fourth dispatch |
| T10 | Temporary429 with Retry-After | Wait at least valid hint within deadline; if too long, stop503; date and invalid-header cases covered |
| T11 | Provider401, malformed400, unsupported model, quota exhausted429 | No retry; dependency error503 for config/quota; client not blamed as401 |
| T12 | Slow upstream / ambiguous read timeout | 504 within request budget+tolerance (target≤31s); no ambiguous replay; timeout status; usage incomplete |
| T13 | SDK spy + gateway retry enabled | SDK retries disabled; observed dispatch count matches attempt ledger |
| T14 | 20 parallel operations, cap10/minute, fresh window | Exactly10 admitted to provider and10 local429; quotas shared across worker instances; Retry-After present |
| T15 | Daily/global cap reached; restart limiter | 429 without provider; reservations rollback if any bucket rejects; DB state persists |
| T16 | Five-request fixture from DATABASE.md | Exact requests/admitted/tokens/latency/error/attempt values; pending and other user excluded |
| T17 | Usage empty window, timezones, start boundary, malformed dates | null averages/error for empty; from inclusive/to exclusive; invalid422; max31d |
| T18 | DB fails before provider and after provider response | No call when admission cannot persist; after-call503; no phantom success/automatic replay; traceable log |
| T19 | Process interrupted with pending request/claim | Startup marks stale cancelled, clears claim, does not resend; partial usage retained |
| T20 | Inspect logs and returned errors | Request correlation exists; no passwords/tokens/DB URL/raw ticket/stack trace |
| T21 | Payload oversized, empty strings, unknown fields, arbitrary model/base URL | 413 or422 as specified; no provider dispatch |
| T22 | Long conversation + newest input | Context bounded, complete oldest turns removed, latest input retained; DB history intact |
| T23 | Login hammering and forwarded-IP manipulation | Limit5/min; untrusted forwarded headers cannot bypass; no plaintext IP logging |
| T24 | Clean checkout and deployed smoke | Documented install/migrate/seed/start succeeds; HTTPS/auth/chat/analyze/history/usage all real |

Tests can combine cases in a small suite. Assert invariants and external behavior; do not mirror private implementation functions. Use injected clock/sleeper for fast retry/deadline unit tests plus one real elapsed-time integration check. Cancellation and DB transaction tests need integration coverage, not only mocks.

## Live smoke, bounded cost

1. Readiness confirms DB, with no provider charge.
2. Login with reviewer credentials.
3. Chat: “Hãy nhớ mã tham chiếu là BLUE-17.”
4. Second chat in same conversation: “Mã tham chiếu tôi vừa đưa là gì?” Check context and inspect input captured in controlled test; live answer may vary but should retain the code.
5. Analyze the payment/account ticket in examples. Confirm schema and forced human review for billing/account.
6. Fetch history and usage; record before/after delta of three logical requests and provider metadata.
7. Try missing-token access, confirm401. Cross-user and rate limit use controlled test credentials, not uncontrolled paid loops.
8. Restart deployed web service; fetch saved conversation again.

Three live calls are a starting smoke budget; further calls need a purpose. Do not run the full test suite against a paid provider. Never print secrets while collecting evidence.

## Evidence record template

Append actual runs to AI_WORKLOG or an evidence file; keep synthetic data labeled.

| Field | Record |
|---|---|
| Date/time + timezone | TODO |
| Commit or artifact version | TODO |
| Environment | Local/test/deploy; actual runtime/DB/model versions |
| Command/case | Exact command or Txx |
| Result | PASS/FAIL/BLOCKED; never default PASS |
| Observation | Actual status, count, elapsed time and sanitized IDs |
| Fix and rerun | What changed, related tests rerun |
| Evidence | Sanitized console log/screenshot/file path |

Keep private keys/credentials in ignored local files. Publish only sanitized evidence. If production smoke fails after a change, fix or rollback and retest before recording the deployment as usable.

## Release gates

- [ ] T01–T24 covered and meaningful checks pass; note any actual unmet cases.
- [ ] No secret in repository, exports, video or logs.
- [ ] Real LLM integration verified and model/account access recorded.
- [ ] Runtime OpenAPI matches documentation and examples.
- [ ] Migration matches database design; usage fixture matches SQL.
- [ ] API accessible during reviewer period; budget/limits disclosed.
- [ ] Known limitations in README match reality.
- [ ] Any P1 bonus has its own evidence; no bonus claim based solely on code presence.
