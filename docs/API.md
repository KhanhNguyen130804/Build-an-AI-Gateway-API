# API contract — planned version 1

**Current runtime:** `/health/live`, database-backed `/health/ready`, seeded-user login, and bearer-protected `GET /v1/auth/me` are implemented. Chat, analysis, conversations, and usage below are planned contracts. [OpenAPI](openapi.json) and [Postman examples](../examples/ai-gateway.postman_collection.json) distinguish the implemented auth slice from those planned routes; FastAPI's runtime schema is authoritative for implemented behavior.

Base paths: `/v1` for business APIs; `/health/live`, `/health/ready`, `/docs`, `/openapi.json` outside versioned routes. All JSON fields use snake_case. Every response has an `X-Request-ID` header; AI results/errors also include body request_id, correlated to logs/DB. Generate a server UUID; do not accept an unvalidated client ID as the ledger primary key.

## Endpoints

| Method/path | Auth | Input / behavior | Success |
|---|---|---|---|
| POST `/v1/auth` | Public | JSON username/password; seeded active users only; same error for unknown, wrong-password, and inactive users | 200 bearer JWT + expiry seconds |
| GET `/v1/auth/me` | Bearer | Returns the active user identified by the validated JWT; useful for Swagger authorization | 200 UUID + username |
| POST `/v1/ai/chat` | Bearer | Planned: message, optional conversation_id, route standard | Planned: reply + conversation_id + model + usage |
| POST `/v1/ai/analyze` | Bearer | Planned: ticket text, route standard | Planned: schema v1 + analysis + usage |
| GET `/v1/conversations` | Bearer | Planned: limit 1–50, offset ≥0; stable descending updated_at/id | Planned: items + total/limit/offset |
| GET `/v1/conversations/{id}` | Bearer | Planned: owner only; messages ordered by sequence; limit 1–50/offset | Planned: conversation + message page |
| GET `/v1/usage` | Bearer | Planned: timezone-aware from/to; default prior 24h; max31d | Planned: user-scoped metrics |
| GET `/health/live` | Public | No paid network calls | 200 alive |
| GET `/health/ready` | Public | Bounded DB check; no secrets/provider call | 200 ready, 503 dependency failure |

`/v1/auth` is an implemented JSON login API, not OAuth2 password-flow form data. Use HTTP bearer authorization in Swagger; `GET /v1/auth/me` confirms the token identity. Never pass a password in query parameters. Public user registration and JWT refresh/revocation are out of scope. Login rate limiting is planned for Phase08 and is not yet active.

## Chat example

```json
{
  "message": "Tôi muốn tích hợp gateway vào ứng dụng hỗ trợ khách hàng.",
  "route": "standard"
}
```

The first successful response supplies `conversation_id`. Submit it with the next message. Server loads recent successful history; client cannot supply a system message, user_id, provider key, base URL or arbitrary model.

Success shape (values below are illustrative, not live evidence):

```json
{
  "request_id": "11111111-1111-4111-8111-111111111111",
  "conversation_id": "22222222-2222-4222-8222-222222222222",
  "reply": "Bạn có thể gọi endpoint chat sau khi nhận bearer token.",
  "provider": "openai",
  "model": "ACTUAL_MODEL_FROM_PROVIDER",
  "latency_ms": 1200,
  "usage": {"input_tokens": 100, "output_tokens": 25, "complete": true}
}
```

Usage sums all known attempts for that operation. Partial token values may be numbers with `complete=false`; all-unknown dispatches use nulls. A failed/new conversation can remain empty and can be retrieved if its ID was communicated in a failure detail; do not append failed turns to context.

## Analyze use case and schema

Input:

```json
{
  "text": "Tôi đã thanh toán nhưng tài khoản vẫn chưa được kích hoạt. Nhờ hỗ trợ kiểm tra.",
  "route": "standard"
}
```

Analysis fields (business validations after provider parsing):

| Field | Allowed value |
|---|---|
| summary | Nonempty string, max500 chars |
| category | billing, technical, account, other |
| priority | low, medium, high |
| sentiment | negative, neutral, positive |
| requires_human | Boolean |
| suggested_reply | Nonempty string, max1500 chars |

Response has request_id, provider, actual model, latency_ms, schema_version `1`, analysis object and usage. For billing/account changes, a fixed server rule forces human review; gateway never performs refunds, account actions or tools. Category/priority are suggestions. Do not present AI classification as verified fact.

## Error envelope and mapping

```json
{
  "error": {
    "code": "UPSTREAM_TIMEOUT",
    "message": "The AI provider did not complete within the request deadline.",
    "request_id": "11111111-1111-4111-8111-111111111111",
    "details": {}
  }
}
```

Details contain only safe field names or retry/context information; never raw provider body, stack trace, key, password or DB URL. Override FastAPI validation/exception handlers to keep the same envelope, including malformed JSON. Distinguish client's token from server's provider credentials.

| HTTP | Code | Retry behavior |
|---:|---|---|
| 401 | UNAUTHORIZED / INVALID_CREDENTIALS | No; acquire valid gateway token; WWW-Authenticate: Bearer where applicable |
| 404 | CONVERSATION_NOT_FOUND | No; same response for missing and unowned UUID |
| 409 | CONVERSATION_BUSY | No automatic POST replay; wait for active turn |
| 413 | PAYLOAD_TOO_LARGE | No; reduce payload |
| 422 | VALIDATION_ERROR / MODEL_REFUSAL | No; correct input or respect refusal |
| 429 | RATE_LIMITED / DAILY_QUOTA_EXCEEDED | Local rejection; Retry-After; zero upstream calls |
| 502 | UPSTREAM_ERROR / INVALID_MODEL_OUTPUT / INCOMPLETE_MODEL_OUTPUT | Internal bounded retries only for eligible transient errors |
| 503 | PROVIDER_UNAVAILABLE / UPSTREAM_RATE_LIMITED / PERSISTENCE_ERROR | No silent success; safe Retry-After where known |
| 504 | UPSTREAM_TIMEOUT | No automatic ambiguous read-timeout replay |
| 500 | INTERNAL_ERROR | Redacted detail; request ID for diagnosis |

Provider invalid credentials, quota exhausted or unsupported model are gateway dependency/configuration errors →503, not a 401 blaming the client. Provider temporary 429 is retried according to the shared deadline; on exhaustion →503 `UPSTREAM_RATE_LIMITED`. Local limiter remains 429. Process interruption is recorded in DB and may have no HTTP response if connection is gone.

## Metrics

Use the definitions and SQL in [DATABASE.md](DATABASE.md). Example fixtures return requests5/tokens420/average1625/error0.5 and flag partial metadata. Dates in usage are UTC ISO strings. `to` defaults to now; `from` defaults to 24 hours before `to`. Never leak other users' metrics; there is no public all-user admin dashboard in P0.

## Known contract limits

Offset pagination can shift as conversations are updated; cursor pagination is a future improvement. No streaming. No idempotency guarantee for client retries; POST can incur another call if replayed after a lost response. Context is bounded, so older turns can be absent from inference while retained in DB. `/docs` documents the API and does not authorize protected calls by itself.
