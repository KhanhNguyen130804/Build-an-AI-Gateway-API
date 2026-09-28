# Nhật ký toàn bộ thay đổi — Phase 02

Ngày thực hiện: **28/09/2026**. Yêu cầu: “Ok, hãy thực hiện pharse 2 nhé”.
Trạng thái nghiệm thu: **6/6 mục P02.01–P02.06 hoàn thành**.

Commit triển khai: [`25e67c3`](https://github.com/KhanhNguyen130804/Build-an-AI-Gateway-API/commit/25e67c3).
So với bản trước `e50d32c`: **26 file thay đổi, 1.138 dòng thêm, 30 dòng xóa**.
Đây là thống kê của commit triển khai; file nhật ký này được bổ sung sau commit đó.

## 1. Trước và sau Phase 02

| Thành phần | Trước | Sau |
|---|---|---|
| Database | Supabase `SELECT 1` đã PASS; chưa có schema ứng dụng | Migration áp dụng sáu bảng trong `gateway` |
| Models | Chưa có ORM | Sáu model SQLAlchemy với UUID, constraints và indexes |
| Migration | SQL thiết kế, chưa có Alembic | Alembic revision `0001_gateway`, upgrade/drift check PASS |
| User demo | Chưa seed | Hai user với password hash Argon2id; seed idempotent |
| Readiness local | Chưa gắn DB, trả503 | Kiểm tra DB/schema revision và trả200 khi sẵn sàng |
| Persistence | Chưa kiểm chứng qua app restart | Hai process mới vẫn thấy hai user đã lưu |
| Kiểm thử local | 20 tests nền tảng | 22 tests; thêm hai ca kiểm tra seed input |
| Public Vercel | Skeleton Phase01 | Vẫn là skeleton Phase01; chưa deploy code/credentials Phase02 |

## 2. Các file code/config được tạo hoặc sửa

| File | Thay đổi và mục đích |
|---|---|
| [app/db/models.py](../app/db/models.py) | Thêm Base metadata schema `gateway` và sáu ORM model; column defaults, FKs, checks, unique constraints, indexes |
| [app/db/session.py](../app/db/session.py) | Thêm chuẩn hóa URL psycopg, async engine/session factory, NullPool, transaction settings, DB probe, dispose và FastAPI session dependency |
| [app/db/seed.py](../app/db/seed.py) | Thêm Argon2id hashing và seed hai user; kiểm tra đầu vào, giữ nguyên account đã có, xử lý insert trùng bằng ON CONFLICT |
| [app/main.py](../app/main.py) | Tạo Database khi có URL, gắn probe vào app state, dispose khi shutdown; cập nhật mô tả Phase02 |
| [app/api/health.py](../app/api/health.py) | Readiness dùng probe thật; ghi loại lỗi an toàn khi DB không ready, không log exception chứa thông tin kết nối |
| [app/__main__.py](../app/__main__.py) | Windows chọn trực tiếp `asyncio:SelectorEventLoop` trong Uvicorn; Linux giữ auto |
| [app/core/config.py](../app/core/config.py) | Default `database_check_timeout_seconds` tăng2→5s; vẫn giới hạn tối đa10s |
| [.env.example](../.env.example) | `DATABASE_CHECK_TIMEOUT_SECONDS` tăng2→5; secret placeholders vẫn trống |
| [alembic.ini](../alembic.ini) | Thêm đường dẫn migrations và import root; không chứa DB URL/password |
| [migrations/env.py](../migrations/env.py) | Đọc settings riêng; hỗ trợ online/offline migration; version table trong gateway; include schema và drift comparison; transaction timeout |
| [migrations/script.py.mako](../migrations/script.py.mako) | Template tạo revision Alembic sau này |
| [migrations/versions/0001_gateway.py](../migrations/versions/0001_gateway.py) | Snapshot DDL ban đầu, cyclic FK đúng thứ tự, schema permissions và RLS; không đọc SQL thiết kế động khi chạy |
| [scripts/migrate.py](../scripts/migrate.py) | Lệnh upgrade/check/current; lỗi chỉ trả loại exception, không xuất connection diagnostics |
| [scripts/seed.py](../scripts/seed.py) | Runner seed riêng, Windows selector policy; chỉ in username và CREATED/PRESERVED |
| [scripts/verify_database.py](../scripts/verify_database.py) | Kiểm chứng Supabase thật: schema/constraints/grants/RLS, Argon2id, seed lặp lại và fresh app instances; fixtures rollback |
| [scripts/verify_restart.py](../scripts/verify_restart.py) | Khởi động/dừng hai process runner do script sở hữu; readiness HTTP thật, đọc lại user và ghi evidence |
| [tests/test_seed_validation.py](../tests/test_seed_validation.py) | Hai ca từ chối password ngắn và username trùng trước khi truy cập DB |

Không thêm dependency mới trong Phase02; dùng các lockfiles đã tạo ở Phase01.

## 3. Database thực đã thay đổi

Trước migration, query inventory xác nhận `gateway` chưa có bảng.
Migration chạy trên Supabase đã được cấu hình; không chạy vào database giả hoặc SQLite.

| Model / bảng | Dữ liệu và ràng buộc chính |
|---|---|
| `User` / `gateway.users` | UUID, username unique, password_hash, is_active, created_at |
| `Conversation` / `gateway.conversations` | Owner user_id, title, timestamps, in_flight_request_id; unique(id,user_id) |
| `AIRequest` / `gateway.ai_requests` | Owner/conversation, operation/route, requested/final provider-model, status/timing, tokens/completeness, attempts, error, structured JSON/schema version |
| `Message` / `gateway.messages` | Owner/conversation/request, sequence, role, content, timestamp; sequence và request-role unique |
| `ProviderAttempt` / `gateway.provider_attempts` | Request/attempt number, provider/model, status/timing, provider IDs, error, tokens/usage-known; attempt number unique theo request |
| `RateLimitBucket` / `gateway.rate_limit_buckets` | Composite PK scope/subject_hash/window_start/window_seconds; request_count |

Thêm bảng quản lý migration `gateway.alembic_version`, revision `0001_gateway`.
Đây là **sáu bảng ứng dụng + một bảng migration**, không phải bảy tính năng nghiệp vụ.

Các invariants được triển khai:

- Composite FKs giữ request/message thuộc đúng conversation và owner.
- Conversation claim chỉ trỏ tới request cùng conversation/user; FK vòng tạo sau bảng requests.
- Chat bắt buộc có conversation; analyze không có conversation.
- Sequence >0, token/latency/attempt count không âm, HTTP status100–599.
- Pending/started chưa có thời gian kết thúc; terminal phải có finished_at và latency.
- Role message chỉ user/assistant; unique conversation-sequence và request-role.
- Known attempt usage phải có cả input/output tokens; structured_output chỉ dành cho analyze.

Indexes: conversations owner/order, requests owner/time, pending requests partial index,
provider attempts theo request và rate-limit window expiry. UUID sinh ở application;
timestamps dùng timestamptz, transaction timezone UTC.

Security DDL: thu hồi schema/table grants của PUBLIC/anon/authenticated, thu hồi sequence
grants của hai client roles, cấu hình default table privileges và bật RLS ở sáu bảng.
Không thêm policy cho client đọc trực tiếp. Grants/RLS đã kiểm chứng bằng query thật.
Dashboard exposed-schema settings chưa được đọc độc lập; vẫn phải giữ `gateway` ngoài
exposed schemas. Backend credential hiện có quyền cao và có thể bypass RLS.

Upgrade chạy trong transaction, lặp lại không tạo bảng trùng. Drift check không phát hiện
upgrade mới. Downgrade ban đầu chủ động từ chối tự xóa dữ liệu; cần kế hoạch backup/removal riêng.

## 4. Cấu hình và dữ liệu riêng ngoài Git

`.env` được chỉnh tại máy, không commit:

- `DATABASE_CHECK_TIMEOUT_SECONDS`:2→5s.
- `DEMO_PASSWORD`, `SECOND_TEST_PASSWORD`: chỉ sinh ngẫu nhiên khi còn trống; lưu riêng.
- OpenAI key/model, database URL và JWT/hash secrets được giữ nguyên.

Không ghi giá trị mật khẩu, hash, API key hoặc URL đầy đủ vào nhật ký này.
Hai user mặc định là `reviewer` và `other-reviewer`; password Argon2id lưu ở PostgreSQL.
Seed chạy lần đầu CREATED, lần sau PRESERVED. Đổi input password trong `.env` không
reset password của account đã có. Password seed yêu cầu tối thiểu16 ký tự, hai username khác nhau.

Connection policy thực:

| Cấu hình | Giá trị / phạm vi |
|---|---|
| Driver | `postgresql+psycopg` |
| Application pool | NullPool; external pool do Supabase cung cấp |
| Prepared statements | Disabled (`prepare_threshold=None`) |
| Connect timeout | 5s |
| App transaction statement / lock timeout | 10s / 3s |
| Migration statement / lock timeout | 30s / 5s |
| Timezone application transaction | UTC |
| Total readiness budget | 5s |

App settings dùng transaction-local set_config, không phụ thuộc session state qua nhiều
transactions. SQL parameters bị ẩn, echo tắt. Không migrate/seed/gọi LLM trong startup hoặc healthcheck.

## 5. Thay đổi API và lifecycle

Không thêm endpoint nghiệp vụ mới. `/health/live`, `/docs`, `/openapi.json` tiếp tục hoạt động.
`/health/ready` giờ kiểm tra truy cập DB, revision `0001_gateway` và quyền truy cập users;
trả200 `{"status":"ready"}` khi thành công, safe503 khi thiếu cấu hình/lỗi/timeout.
Request ID tiếp tục khớp response/log. Database engine được dispose khi lifespan shutdown.
Login/JWT và owner queries ở tầng API chưa có; đó là Phase03.

## 6. Lỗi thực tế đã phát hiện và sửa

| Hiện tượng | Nguyên nhân / sửa | Kiểm chứng sau sửa |
|---|---|---|
| Readiness đầu tiên503 với DB kết nối được | Budget2s không đủ cho cold connection và nhiều lượt query; gom transaction settings, giảm probe queries, tăng lên5s | Hai fresh app instances200 |
| Uvicorn thật503 trong khi direct async checks PASS | Uvicorn0.54 chọn Proactor trên Windows, ghi đè policy; psycopg async cần Selector; truyền explicit loop factory | Hai process restart đều200 |
| Lint báo dòng dài/import ordering | Định dạng lại code và chuỗi DDL/SQL | Ruff PASS |

Các kết quả FAIL ban đầu không được dùng như bằng chứng nghiệm thu; chỉ kết quả cuối được ghi PASS.

## 7. Kiểm tra và evidence

[phase02.json](../artifacts/evidence/phase02.json) ghi kết quả cuối lúc
**18:54:34 ngày28/09/2026 UTC+7** (11:54:34 UTC).

- 22 pytest tests PASS:20 foundation tests có sẵn và2 seed validation tests mới.
- Ruff và pip check PASS.
- Upgrade lặp lại và Alembic drift check PASS.
- 14 live checks: schema/revision; denied anon/authenticated/RLS; request owner FK;
  claim owner FK; unique sequence; unique request-role; message owner FK;
  message request-owner FK; positive sequence; nonnegative tokens; terminal timing;
  known usage requires tokens; UTC; rolled-back fixtures.
- Verify Argon2id với hai password cấu hình PASS; seed lặp lại giữ nguyên UUID/hash,
  kể cả khi một password input bị thay trong bài kiểm tra.
- Hai app instances mới và hai process runner mới readiness200, vẫn thấy hai seed users.
- Server local sau triển khai trả readiness200. Không phát sinh LLM inference trong Phase02 checks.

Không để lại test users/conversations/requests/messages từ constraint fixtures: transaction rollback.
Seed users là dữ liệu chủ động giữ lại để dùng ở Phase03.

## 8. Toàn bộ thay đổi tài liệu/evidence trong commit

| File | Nội dung cập nhật |
|---|---|
| [AI_WORKLOG.md](../AI_WORKLOG.md) | Session008: prompt thật, AI contribution, lỗi/sửa, evidence và limits |
| [PHASE_TASKS.md](../PHASE_TASKS.md) | Tick P02.01–06, bảng nghiệm thu và bước tiếp theo Phase03 |
| [PLAN.md](../PLAN.md) | Trạng thái Phase01/02 thực, tránh claim business APIs đã xong |
| [README.md](../README.md) |22 tests, database đã áp dụng, local readiness và cloud boundary |
| [docs/DATABASE.md](DATABASE.md) | Models/migration đã chạy, liên kết runbook/evidence; metrics vẫn là thiết kế |
| [docs/DEPLOYMENT.md](DEPLOYMENT.md) | Vercel skeleton hiện tại, cloud DB integration chưa deploy |
| [docs/VERIFICATION.md](VERIFICATION.md) | Phân biệt22 tests local, live DB evidence và full acceptance chưa chạy |
| [docs/PHASE02_DATABASE.md](PHASE02_DATABASE.md) | Runbook migration/seed/live checks, connection/security limits |
| [artifacts/evidence/phase02.json](../artifacts/evidence/phase02.json) | Kết quả DB/security/hash/idempotency/restart/tests thật |

Secret scan trên staged diff PASS, kiểm tra `.env`/`.venv`/`.vercel` không được track PASS.
Commit25e67c3 đã push lên GitHub nhánh `main`; không force push.

## 9. Lệnh tái kiểm tra

```powershell
Set-Location "D:\Documents\126\HocKyDoanhNghiep\Build an AI Gateway API"
& .\.venv\Scripts\python.exe scripts/migrate.py upgrade
& .\.venv\Scripts\python.exe scripts/migrate.py check
& .\.venv\Scripts\python.exe scripts/seed.py
& .\.venv\Scripts\python.exe scripts/verify_database.py
& .\.venv\Scripts\python.exe scripts/verify_restart.py
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m ruff check app tests scripts/*.py migrations
& .\.venv\Scripts\python.exe -m pip check
```

Live scripts truy cập Supabase thật. verify_database ghi lại evidence hiện tại; verify_restart
khởi động/dừng process riêng trên port tạm, không dừng server của người dùng.
Để chạy server local: `& .\.venv\Scripts\python.exe -m app`.

## 10. Việc chưa triển khai và bước tiếp theo

- Public Vercel chưa nhận code/DB credentials Phase02; vẫn dùng bản Phase01, readiness503.
- Chưa có login/JWT/owner API checks; chưa có chat/analyze/history/usage/ledger/retry/limiter.
- Chưa tạo backend DB role least-privilege; quyền privileged hiện tại là giới hạn đã ghi nhận.
- Chưa có full release/security/load/backup-restore nghiệm thu; không tuyên bố production-ready.
- Git auto-deploy Vercel chưa kết nối; source GitHub đã push, deploy skeleton dùng CLI.

Bước tiếp theo: Phase03 authentication, verify Argon2id, JWT claims và bearer/owner boundary.
