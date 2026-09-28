# AI Gateway — công việc triển khai theo phase

**Cập nhật trạng thái: sau triển khai Phase01 local ngày 28/09/2026, Asia/Saigon (UTC+7).**

Đây là checklist thực hiện dựa trên kiểm tra workspace hiện tại. Stack người dùng đã chọn: **Python + FastAPI + PostgreSQL**. Mục tiêu là API chạy thật, đủ yêu cầu bắt buộc và có hồ sơ kiểm chứng để nộp challenge.

Hạn theo đề bài: **23:59 ngày 01/10/2026**; mốc nộp nội bộ: **21:00 cùng ngày**. Tại thời điểm kiểm tra còn khoảng **79 giờ 54 phút theo đồng hồ**, theo giả định deadline dùng UTC+7. Giờ rảnh thực tế và timezone của cổng thi chưa được xác nhận riêng.

## 1. Đánh giá hiện trạng

| Thành phần | Trạng thái đã kiểm tra | Ý nghĩa / việc còn thiếu |
|---|---|---|
| Stack | Đã chọn Python + FastAPI | Không cần quyết định lại framework |
| Kế hoạch | Có [PLAN.md](PLAN.md) | Phạm vi/backlog đã chuẩn bị; chưa thực hiện |
| Kiến trúc | Có [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Có thiết kế auth, ledger, deadline, retry, persistence |
| Database | Có [DATABASE.md](docs/DATABASE.md), [schema.sql](db/schema.sql) với 6 bảng | SQL thiết kế chưa chạy; chưa có model ORM/Alembic |
| API | Có [API.md](docs/API.md), [openapi.json](docs/openapi.json) | 8 operation thiết kế; chưa có router/server |
| Ví dụ | Có [Postman collection](examples/ai-gateway.postman_collection.json), [tickets.json](examples/tickets.json) | 10 request mẫu; chưa chạy với API thật |
| Kiểm thử | Có [VERIFICATION.md](docs/VERIFICATION.md) | 24 ca nghiệm thu đã mô tả; chưa có test code hoặc kết quả runtime |
| Config | Có [.env.example](.env.example), chưa có `.env` | Key/model/DB/JWT secret chưa được cấu hình trong dự án |
| Python | Có Python 3.12.14 đi kèm Codex qua đường dẫn tuyệt đối; chưa thấy `python`/`py` trong PATH | Chưa có runtime/virtual environment riêng cho dự án |
| Git | Có executable; chưa có `.git` tại workspace | Chưa init, commit, remote hoặc push từ dự án này |
| Backend | Chưa có `app/`, dependency files hoặc entrypoint | Chưa có tính năng backend được triển khai |
| Migration/test/build | Chưa có `migrations/`, `alembic.ini`, `tests/`, `Dockerfile` | Cần tạo và chạy thật |
| PostgreSQL | Chưa có kết nối được kiểm tra | Không suy ra đã có DB chỉ vì có schema.sql |
| LLM | Chưa có call thật từ dự án | Quyền truy cập model, credit, structured output chưa xác minh |
| Deploy/demo | Chưa có URL API, GitHub repo được ghi nhận hoặc video | Các deliverable sản phẩm còn thiếu |
| AI worklog | Có [AI_WORKLOG.md](AI_WORKLOG.md) | Đã ghi công việc chuẩn bị; cần cập nhật từng phiên thực hiện |

Kiểm tra lại shell chưa thấy tên biến key LLM/DB/deploy liên quan. Điều đó chỉ phản ánh shell hiện tại, không chứng minh người dùng chưa có tài khoản hoặc key ở nơi khác. Docker và uv chưa thấy trong PATH; Docker local không phải điều kiện bắt buộc nếu dùng PostgreSQL managed.

**Cập nhật sau implementation:** bảng trên là baseline lúc16:05, trước triển khai. Hiện đã có `.venv`, Git local, dependency lockfiles, `app/`, `tests/`, private `.env`, Dockerfile và Vercel entrypoint. FastAPI local chạy được;20 foundation tests, Ruff, imports/pip check, wheel build và HTTP smoke đã PASS. Chưa có ORM/migration/auth/business endpoints. OpenAI key chưa tạo; Supabase và Vercel đã chọn nhưng chưa kết nối/deploy. Xem [evidence](artifacts/evidence/phase01.json) và [hướng dẫn cấu hình](docs/GETTING_STARTED.md).

## 2. Cách sử dụng và cập nhật file

- `[x]` chỉ khi công việc đã thực hiện và có bằng chứng. `[ ]` là còn phải làm; có file nháp không đủ để tick tính năng.
- Trạng thái phase: `CHƯA BẮT ĐẦU`, `ĐANG LÀM`, `CẦN ĐẦU VÀO`, `ĐÃ NGHIỆM THU`. Chuẩn bị độc lập vẫn tiếp tục khi một việc cần đầu vào.
- Mỗi task có ID `Pxx.yy`. Ghi ID này trong commit/worklog và record kiểm tra để truy vết.
- Khi hoàn thành phase: ghi kết quả thực, phiên bản code, test/lệnh đã chạy và lỗi còn lại. Không mặc định PASS.
- Mỗi task triển khai bao gồm kiểm tra nhỏ ngay tại bước đó; phase kiểm thử cuối tập trung vào integration/regression và bằng chứng.
- Thay đổi API/schema/chính sách cần cập nhật tài liệu tương ứng, Postman và runtime OpenAPI.
- File này quản lý công việc và trạng thái; [PLAN.md](PLAN.md) quản lý phạm vi/rubric; docs chuyên đề quản lý thiết kế chi tiết.

**P0** là yêu cầu bắt buộc. **P1** là bonus có điều kiện. Trước khi P0 được nghiệm thu, chưa đưa P1 vào tiến độ chính.

## 3. Tổng quan phase và effort

Effort là giờ thực hiện dự kiến, không phải thời gian chờ tài khoản/build/provider. Ngân sách hiện tại: **26 giờ P0 + 4 giờ dự phòng**; cần điều chỉnh khi biết giờ rảnh thực tế. Ước lượng giả định không phát sinh lỗi môi trường lớn.

| Phase | Mục tiêu | Phụ thuộc chính | Giờ | Trạng thái hiện tại |
|---|---|---|---:|---|
| 00 | Kiểm tra hiện trạng, thống nhất đầu vào thiết kế | Không | Đã thực hiện kiểm tra | ĐÃ HOÀN THÀNH ĐÁNH GIÁ |
| 01 | Môi trường, skeleton, config, health, preflight provider/host | 00 | 2.0 | ĐÃ NGHIỆM THU — 8/8 mục |
| 02 | PostgreSQL, ORM, migration, seed | 01; DB truy cập được | 1.5 | ĐÃ NGHIỆM THU — 6/6 mục |
| 03 | Authentication và phân quyền cơ bản | 02 | 1.5 | CHƯA BẮT ĐẦU |
| 04 | Adapter LLM thật và request/attempt ledger | 01–03; model/key đã xác minh | 2.0 | CHƯA BẮT ĐẦU |
| 05 | Chat, context và lưu hội thoại | 04 | 2.0 | CHƯA BẮT ĐẦU |
| 06 | Structured ticket analysis | 04 | 1.5 | CHƯA BẮT ĐẦU |
| 07 | Error handling, retry, timeout, recovery, logging | Ledger ở 04; hoàn thiện 05–06 | 2.0 | CHƯA BẮT ĐẦU |
| 08 | Rate limit và quota demo | 02–03; tích hợp vào gateway | 1.5 | CHƯA BẮT ĐẦU |
| 09 | Usage API và tính đúng metrics | 04; chốt semantics ở 07–08 | 1.5 | CHƯA BẮT ĐẦU |
| 10 | Integration/security/regression và evidence | 03–09 | 3.5 | CHƯA BẮT ĐẦU |
| 11 | Deploy: skeleton sớm + release cuối | Bắt đầu từ 01; chốt sau 10 | 2.5 | CHƯA BẮT ĐẦU |
| 12 | Hoàn thiện docs, README, AI_WORKLOG | Làm dần; chốt sau 10–11 | 2.5 | CHƯA BẮT ĐẦU |
| 13 | Video, kiểm tra links, hồ sơ nộp | 12 + API deploy ổn định | 2.0 | CHƯA BẮT ĐẦU |
| **Tổng implementation P0** |  |  | **26.0** |  |
| Dự phòng | Môi trường/provider/deploy, sửa lỗi hoặc quay lại demo |  | **4.0** | Chưa sử dụng |

Đối chiếu backlog cũ: P01=B00+B01; P02=B02; P03=B03; P04=B04; P05=B05; P06=B06; P07=B08; P08=B09; P09=B07; P10=B10; P11=B11; P12=B12; P13=B13.

Thứ tự chính: **01 → 02 → 03 → 04 → 05/06 → 07/08 → 09 → 10 → 11 hoàn thiện → 12 → 13**. Hai nhánh 05/06 có thể thực hiện độc lập sau 04. Deploy skeleton ở P11.01 bắt đầu sớm, không chờ đến cuối tất cả phase. Deadline và SDK retry settings có bản tối thiểu ngay P04; P07 hoàn thiện các nhánh lỗi.

## 4. Đầu vào cần chốt sớm

| ID | Đầu vào | Tình trạng | Ảnh hưởng nếu thiếu |
|---|---|---|---|
| I01 | Số giờ rảnh mỗi ngày đến 01/10 | Chưa được cung cấp | Chưa xác nhận kế hoạch26h có khả thi theo lịch cá nhân |
| I02 | Dịch vụ LLM đang có, key cấu hình riêng, credit/quyền model | Chọn OpenAI; chưa tạo key, chưa xác minh model/credit | Chưa chạy preflight và adapter thật |
| I03 | PostgreSQL local/managed và thông tin kết nối riêng | Chọn Supabase; project/connection chưa xác minh | Chưa migrate và test persistence |
| I04 | Nơi deploy có thể dùng và ngân sách cho host/provider | Chọn Vercel; chưa deploy, budget chưa xác minh | Chưa provisioning/release API online |
| I05 | Tài khoản/remote GitHub và quyền reviewer truy cập | Repo người dùng đã cung cấp; main đã push, commit24bcec4 | Quyền reviewer truy cập cần kiểm tra trước nộp; lưu ý ẩn danh |
| I06 | Hạn mức demo phù hợp budget và reviewer | Có default trong `.env.example`, chưa chốt | Có thể quá thấp để review hoặc quá cao cho budget |

Nếu I02–I04 chưa có, vẫn có thể dựng runtime, skeleton, schema/model, error foundation và fake adapter cho test. Ghi rõ call thật/deploy đang cần đầu vào; chưa nghiệm thu các phase phụ thuộc. Không gửi giá trị key/password vào tài liệu này.

## 5. Phase 00 — đánh giá hiện trạng

**Kết quả:** hoàn thành kiểm tra workspace cho phiên cập nhật này; không phải hoàn thành application.

- [x] P00.01 — Liệt kê file; xác nhận18 file chuẩn bị trước phiên này.
- [x] P00.02 — Đọc kế hoạch, README, schema/config và ca nghiệm thu; xác nhận stack FastAPI đã được chọn.
- [x] P00.03 — Kiểm tra thiếu backend/venv/migration/tests/build files và `.git`.
- [x] P00.04 — Kiểm tra Python bundled3.12.14; Git có trong PATH; ghi các kết nối/tài khoản chưa xác minh.

**Gate:** hiện trạng được ghi đúng, việc đã chuẩn bị và việc chưa triển khai được tách rõ.

## 6. Phase 01 — môi trường và skeleton

**Mục tiêu:** chạy được web service tối thiểu; phát hiện vấn đề key/model/host trước khi đầu tư phần lớn effort.

**Đầu vào:** I01–I04 cho các bước tương ứng. **Effort:**2h. **Tham khảo:** [DEPLOYMENT.md](docs/DEPLOYMENT.md), [.env.example](.env.example).

- [x] P01.01 — Python3.12.14, `.venv` và pip hoạt động; runtime bundled không bị sửa.
- [x] P01.02 — Cài dependencies; pin runtime/dev bằng pip-tools; imports và pip check PASS.
- [x] P01.03 — Tạo app factory/router/service/provider/schema, lockfiles và Git local; chưa commit/remote/push.
- [x] P01.04 — Config validation và private `.env`; secret local sinh ngẫu nhiên; production từ chối thiếu cấu hình bằng lỗi an toàn.
- [x] P01.05 — Request UUID, JSON logging/redaction, error envelope, validation/malformed JSON và body limits; kiểm chứng bằng tests.
- [x] P01.06 — Local live/docs/OpenAPI200; readiness503 khi chưa gắn DB; HTTP smoke PASS.
- [x] P01.07 — Probe LLM thật và structured output PASS; returned model `gpt-6-luna`, input43/output12 tokens. [Evidence](artifacts/evidence/provider-20260928.json). Chưa chứng minh ledger hay business endpoint đã chạy.
- [x] P01.08 — Vercel build/deploy skeleton PASS, Python3.12; public live/docs/OpenAPI200, readiness503 đúng Phase01 và lỗi404 có request ID. [URL](https://ai-gateway-challenge.vercel.app/docs), [evidence](artifacts/evidence/vercel-phase01.json).

**Nghiệm thu Phase01:**8/8 mục hoàn thành. Probe Supabase/OpenAI thật và Vercel build/public HTTP smoke PASS. Bản cloud là skeleton development, chưa cấu hình cloud DB/LLM; thuộc tích hợp/release các phase sau. GitHub auto-deploy chưa kết nối, hiện dùng CLI. Container không phải host đã chọn và chưa build. Các ghi nhận thiếu cấu hình trước đó là lịch sử.

**Đầu ra dự kiến:** `.venv`, skeleton `app/`, dependency files, config/error/log foundation, health/docs local; probe provider và host nếu đầu vào có.

**Gate:** service khởi động từ command rõ ràng; không lộ secret; Python và import được xác minh. Provider/host chưa xác minh phải ghi riêng, không đánh dấu đã sẵn sàng chỉ vì server local chạy.

## 7. Phase 02 — database và migration

**Mục tiêu:** có PostgreSQL thật và schema dùng được. **Phụ thuộc:**01 + I03. **Effort:**1.5h. **Tham khảo:** [DATABASE.md](docs/DATABASE.md), [schema.sql](db/schema.sql).

- [x] P02.01 — Runtime psycopg/SQLAlchemy kết nối Supabase; NullPool, disabled prepared statements, transaction-local timeouts và UTC được cấu hình/kiểm tra.
- [x] P02.02 — ORM models đủ sáu bảng, schema-qualified `gateway`.
- [x] P02.03 — Alembic revision0001_gateway áp dụng DB trống; rerun upgrade và drift check PASS.
- [x] P02.04 — FK vòng đúng thứ tự; live owner/claim/message/sequence/token/timing constraints PASS; fixtures rollback.
- [x] P02.05 — Seed hai user Argon2id; rerun giữ nguyên UUID/hash, kể cả khi đổi input password. Mật khẩu riêng trong `.env`.
- [x] P02.06 — Readiness200 với DB/migration thật; fresh app instances và hai process restart vẫn đọc được hai user.

**Evidence:** [phase02.json](artifacts/evidence/phase02.json), [runbook](docs/PHASE02_DATABASE.md). RLS/grants của anon/authenticated được kiểm chứng. Backend credential hiện privileged; dedicated least-privilege role và cloud DB deployment chưa thực hiện. Public Vercel vẫn là Phase01 skeleton; việc này thuộc release sau.

**Đầu ra dự kiến:** `app/db/`, `migrations/`, `alembic.ini`, seed command, readiness đúng trạng thái.

**Gate:** migrate từ DB sạch thành công; constraints owner/sequence hoạt động; password không plaintext; readiness không gọi provider trả phí. Liên quan T01/T18.

## 8. Phase 03 — authentication và owner boundary

**Mục tiêu:** client xác thực và dữ liệu được cách ly theo user. **Phụ thuộc:**02. **Effort:**1.5h. **Tham khảo:** [API.md](docs/API.md).

- [ ] P03.01 — Tạo `POST /v1/auth` nhận JSON username/password; lỗi đăng nhập không tiết lộ tài khoản có tồn tại hay không.
- [ ] P03.02 — Verify password hash; sinh JWT với sub UUID, iat/exp/iss/aud và thời hạn cấu hình.
- [ ] P03.03 — Dependency xác thực: algorithm allowlist, chữ ký/expiry/issuer/audience, user tồn tại và active.
- [ ] P03.04 — Khai báo HTTP bearer cho Swagger; thử login rồi authorize, không giả định đây là OAuth2 server.
- [ ] P03.05 — Tạo owner-query primitive dùng user_id từ token; resource không tồn tại hoặc ngoài quyền cùng trả404.
- [ ] P03.06 — Kiểm tra valid/invalid/missing/expired/tampered token; định dạng lỗi và WWW-Authenticate khi áp dụng.

**Gate:** login200; protected call401 khi thiếu/sai token; không nhận user_id từ client để quyết định quyền. T02 phải có kết quả; T03 kiểm tra đầy đủ khi có conversation ở05. Login limiter được gắn ở08.

## 9. Phase 04 — LLM adapter thật và ledger

**Mục tiêu:** một call thật đi qua gateway và được ghi nhận đầy đủ. **Phụ thuộc:**01–03, probe model/key thành công. **Effort:**2h.

- [ ] P04.01 — Interface provider tối giản cho chat/analyze và metadata; implement adapter thật; fake adapter chỉ cho test.
- [ ] P04.02 — Model/route lấy từ server allowlist; P0 chỉ route `standard`; không nhận arbitrary model/base URL/key từ request.
- [ ] P04.03 — Tắt retry SDK; đặt per-attempt timeout và total deadline nền tảng ngay bước này.
- [ ] P04.04 — Tạo request pending sau auth/validation/owner checks; commit trước dispatch; ghi started_at/user/requested model.
- [ ] P04.05 — Tạo attempt trước mỗi dispatch; lưu provider IDs, actual model nếu có, latency, token metadata và status.
- [ ] P04.06 — Finalize success/failure; summary tokens/attempt_count tính từ attempt rows; unknown/partial usage có cờ riêng, không điền0 giả.
- [ ] P04.07 — Đo latency bằng monotonic clock; timestamp lưu UTC; request_id thống nhất response/log/DB.
- [ ] P04.08 — Chạy vertical slice auth→provider→persist, kiểm tra SQL row và log đã redact.

**Gate:** call provider thật có row request/attempt, output và metadata thực; không báo success trước khi persist. Lỗi trước và sau dispatch có trạng thái rõ. Chính sách retry/error đầy đủ hoàn thiện ở07.

## 10. Phase 05 — chat và conversation storage

**Mục tiêu:** chat hai lượt có context và history còn sau restart. **Phụ thuộc:**04. **Effort:**2h.

- [ ] P05.01 — Implement `POST /v1/ai/chat`: message, optional conversation_id, route; validate input/unknown fields.
- [ ] P05.02 — Tạo conversation cho lượt đầu; lượt sau kiểm tra owner; đọc recent successful turns từ DB.
- [ ] P05.03 — Dựng trusted server prompt và bounded context: tối đa20 messages/40.000 chars theo thiết kế; bỏ oldest complete turns, giữ input mới nhất.
- [ ] P05.04 — Claim một active turn/conversation trong transaction ngắn; conflict409; không giữ lock/transaction trong lúc chờ LLM.
- [ ] P05.05 — Thành công: commit user+assistant messages, sequence, terminal request và release claim atomically; thất bại không thêm turn vào context.
- [ ] P05.06 — Implement GET list/detail conversation với pagination, owner filtering và thứ tự ổn định.
- [ ] P05.07 — Kiểm tra hai lượt cùng conversation, restart persistence, user B không đọc/gửi vào hội thoại A và concurrent chat không trộn turn.

**Gate:** chat/history đầy đủ và owner boundary thực hoạt động. T03–T05/T22 có kiểm tra tại bước này; bổ sung integration regression ở10.

## 11. Phase 06 — structured analysis

**Mục tiêu:** phân loại ticket bằng structured output thật. **Phụ thuộc:**04. **Effort:**1.5h.

- [ ] P06.01 — Tạo schema TicketAnalysis v1: summary/category/priority/sentiment/requires_human/suggested_reply theo contract.
- [ ] P06.02 — Implement `POST /v1/ai/analyze`; giới hạn input; trusted instructions và ticket data truyền riêng.
- [ ] P06.03 — Dùng schema-supported output của provider; Pydantic kiểm tra structure/business limits sau parsing.
- [ ] P06.04 — Enforce human review cho billing/account; reply không tuyên bố đã refund/sửa tài khoản/thực hiện hành động.
- [ ] P06.05 — Phân biệt refusal, incomplete, parse/schema failure; không sửa JSON tùy tiện rồi trả200.
- [ ] P06.06 — Lưu validated JSON/schema_version và available usage; chạy ticket mẫu và case chứa chỉ dẫn không đáng tin.

**Gate:** output schema v1 hợp lệ trên provider thật; invalid/refused/incomplete có HTTP/status theo thiết kế, metadata đã biết vẫn được lưu. T06–T07.

## 12. Phase 07 — reliability, errors, recovery và logging

**Mục tiêu:** fail đúng, giới hạn số call/thời gian, truy vết được. **Phụ thuộc:**04; hoàn thiện trên05–06. **Effort:**2h. **Tham khảo:** [ARCHITECTURE.md](docs/ARCHITECTURE.md).

- [ ] P07.01 — Chốt error mapping: token gateway401; lỗi key/model/quota provider là dependency error; local429 khác upstream throttling.
- [ ] P07.02 — Retry eligible transient errors: max3 attempts toàn operation, exponential backoff+jitter, respect Retry-After; không retry quota/billing/auth/refusal/schema error.
- [ ] P07.03 — Chặn retry lồng: kiểm tra SDK max_retries=0; attempt ledger khớp số dispatch thực.
- [ ] P07.04 — Dùng một total deadline30s, LLM budget≤27s, attempt≤10s theo remaining time; giữ budget finalize DB; bound pool/statement waits.
- [ ] P07.05 — Không tự replay ambiguous read-timeout; finalize timeout/partial metadata; không claim exactly-once hoặc chắc chắn hủy billing provider.
- [ ] P07.06 — Cleanup claim và terminalize request/attempt khi lỗi/cancel; startup reconciliation cho stale pending, không tự gửi lại provider.
- [ ] P07.07 — Khi persist thất bại sau provider response: lỗi503 an toàn và correlation log; không trả success chưa lưu, không tự gọi lần nữa.
- [ ] P07.08 — JSON logs request/attempt/finish; redact key/token/password/DB URL; không log raw prompt/ticket/output; kiểm tra error handler không lộ stack trace.

**Gate:** 503→success cho1 logical request/2 attempts; retry cap, quota-no-retry, deadline và interrupted recovery có evidence. Đối chiếu T08–T13/T18–T20.

## 13. Phase 08 — rate limiting và daily quota

**Mục tiêu:** giới hạn request đúng khi concurrent/restart, kiểm soát demo trong budget. **Phụ thuộc:**02–03 + gateway04. **Effort:**1.5h.

- [ ] P08.01 — Counter fixed-window trong PostgreSQL, atomic upsert; scope user-minute/user-day/global-day và login-IP riêng.
- [ ] P08.02 — Reserve các quota AI theo thứ tự cố định trong transaction ngắn; rollback tất cả reservation nếu một quota từ chối.
- [ ] P08.03 — Gắn limiter trước provider dispatch; local rejection finalize request rate_limited, zero attempts và known0 tokens.
- [ ] P08.04 — Default10 AI operations/min/user; daily caps từ cấu hình; chốt lại giá trị theo I06. Downstream failure vẫn tiêu thụ quota đã admit.
- [ ] P08.05 — Login5/min theo hashed trusted client IP; cấu hình proxy trust; trả429/Retry-After và safe error code.
- [ ] P08.06 — Cleanup expired buckets có giới hạn; test20 operations song song trên fresh window: đúng10 upstream admissions/10 local rejections; state còn sau restart.

**Gate:** concurrency không bypass cap; tất cả worker dùng chung counter; quota rejection không gọi LLM. T14–T15/T23. Public demo chỉ mở khi limiter và caps đã kiểm tra.

## 14. Phase 09 — usage API

**Mục tiêu:** metrics giải thích và đối chiếu được. **Phụ thuộc:**04, semantics07–08. **Effort:**1.5h. **Tham khảo:** [DATABASE.md](docs/DATABASE.md).

- [ ] P09.01 — Implement `GET /v1/usage`, scoped user; UTC window `[from,to)` theo request started_at; default24h, max31 ngày.
- [ ] P09.02 — Aggregate request và attempt riêng, tránh JOIN messages/attempts nhân số lượng.
- [ ] P09.03 — Phân biệt terminal/admitted/success/failed/refused/rate_limited/pending; tính latency và denominator error_rate đúng contract.
- [ ] P09.04 — Tổng token đã biết trên mọi attempts; thêm completeness/partial counts; không suy ra token không báo cáo.
- [ ] P09.05 — Chạy fixture A–E: requests5/admitted4/attempts5/retry1/tokens420/average1625ms/error_rate0.5/partial2.
- [ ] P09.06 — Kiểm tra empty window trả average/error null; time boundary, timezone, malformed dates và user isolation.

**Gate:** SQL và API fixture cho cùng kết quả; retry không nhân logical requests; phần usage không biết được trình bày rõ. T16–T17.

## 15. Phase 10 — kiểm thử tích hợp và evidence

**Mục tiêu:** các requirement được chứng minh bằng behavior thật. **Phụ thuộc:**03–09. **Effort:**3.5h.

- [ ] P10.01 — Tổ chức test DB PostgreSQL riêng và fake provider deterministic; không chạy toàn bộ suite bằng API trả phí.
- [ ] P10.02 — Đối chiếu đủ T01–T24 trong [VERIFICATION.md](docs/VERIFICATION.md); tái dùng test đã viết ở các phase trước.
- [ ] P10.03 — Chạy ownership/JWT/input/error/redaction tests; sửa và rerun ca liên quan khi có lỗi.
- [ ] P10.04 — Chạy concurrency/limiter/claim, retry/deadline/cancellation/recovery, DB failure và metrics tests.
- [ ] P10.05 — Chạy bounded live smoke: hai lượt chat và một analyze; ghi sanitized provider/request IDs, model và usage thực.
- [ ] P10.06 — Thử setup từ checkout/DB sạch bằng hướng dẫn dự kiến; test Linux build/dependency imports, không chỉ máy Windows.
- [ ] P10.07 — Lưu kết quả PASS/FAIL/NOT RUN, phiên bản, command và evidence; fix P0 còn lỗi trước khi release.

**Gate:** P0 có test liên quan và kết quả PASS thực; mọi NOT RUN được xử lý hoặc ghi rõ là requirement chưa đạt. Không dùng số lượng test hoặc file tồn tại làm bằng chứng chức năng.

## 16. Phase 11 — deploy sớm và release cuối

**Mục tiêu:** reviewer truy cập được API thật. **Effort:**2.5h, tách khoảng0.5h skeleton sớm và2h migration/release/smoke cuối. **Đầu vào:** I03–I05. **Tham khảo:** [DEPLOYMENT.md](docs/DEPLOYMENT.md).

- [ ] P11.01 — Ngay khi P01 có skeleton: thử build/start trên host đã chốt, kiểm tra health/docs URL; ghi blocker nếu chưa có account/budget. Việc này không đợi P10.
- [ ] P11.02 — Hoàn thiện Docker/build config và start command theo PORT; dependency pin; verify psycopg/password-hash imports trên môi trường deploy.
- [ ] P11.03 — Thiết lập persistent DB/secret env/HTTPS; migration chạy một lần trong release step; seed reviewer account bằng lệnh riêng.
- [ ] P11.04 — Chốt provider access, output/operation caps, proxy/timeout config và credentials reviewer; production chỉ mở demo sau P08 và regression cần thiết.
- [ ] P11.05 — Sau P10: deploy bản đã kiểm tra; chạy auth→chat2 lượt→analyze→history→usage; restart kiểm tra persistence.
- [ ] P11.06 — Ghi URL/version và smoke evidence; xác định bản rollback/migration compatibility; API/link tồn tại đến ít nhất08/10 và hết review thực tế.

**Gate:** deployed API/docs qua HTTPS dùng được, LLM thật và dữ liệu persist; không còn URL placeholder trong deliverable cuối. T24; healthcheck không phát sinh inference trả phí.

## 17. Phase 12 — docs, README và AI_WORKLOG

**Mục tiêu:** người khác hiểu, thử và tái lập được sản phẩm. **Phụ thuộc:** ghi dần từ01; chốt sau10–11. **Effort:**2.5h.

- [ ] P12.01 — Thay README planning-only bằng trạng thái thực: problem/solution, setup đã thử, API/repo/video links, demo access và limits.
- [ ] P12.02 — Đồng bộ diagram/database docs với code/migration thực; xuất ảnh sơ đồ nếu nơi nộp không render Mermaid.
- [ ] P12.03 — Export runtime OpenAPI từ FastAPI; đối chiếu schema/status/headers với contract; cập nhật Postman và chạy examples trên deploy.
- [ ] P12.04 — Không chạy generator thiết kế để ghi đè runtime OpenAPI sau khi contract implementation đã thay đổi.
- [ ] P12.05 — AI_WORKLOG ghi prompts/tools thực, sai/sửa thực, verification và proposed improvements thêm7 ngày; phân biệt test fake với live evidence.
- [ ] P12.06 — Ghi completed work/limitations trung thực; chưa claim multi-provider/cache/production scale nếu chưa làm và test.
- [ ] P12.07 — Soát placeholders, secret/session values, tên/avatar/logo cá nhân và quyền xem; giữ exports sạch.

**Gate:** tài liệu khớp deployed behavior; clean setup lặp lại được; metrics và error policy giải thích rõ; worklog có evidence thực.

## 18. Phase 13 — video và nộp bài

**Mục tiêu:** hồ sơ đúng yêu cầu và được nộp đúng hạn. **Phụ thuộc:**12, API release pass. **Effort:**2h. **Tham khảo:** [SUBMISSION.md](docs/SUBMISSION.md).

- [ ] P13.01 — Quay theo script4 phút40 giây: architecture→auth→chat/history→analyze→usage→reliability evidence→AI worklog/limitations.
- [ ] P13.02 — Dùng ticket giả; ẩn secrets/profile; test với fake upstream phải có nhãn; đo thời lượng video thực≤5 phút.
- [ ] P13.03 — Upload/đặt quyền xem video phù hợp; mở API/repo/video bằng phiên không có quyền owner.
- [ ] P13.04 — Điền ít nhất1 prompt thực và process≥30 ký tự; hours saved chỉ ghi khi có cơ sở, không tự bịa số.
- [ ] P13.05 — Kiểm tra ẩn danh; lựa chọn showcase/prompt sharing theo quyết định người dùng.
- [ ] P13.06 — Người dùng nộp hoặc yêu cầu thao tác nộp rõ ràng; xác nhận receipt/trạng thái thành công thật trước21:00 ngày01/10.
- [ ] P13.07 — Lưu bản nộp/link/receipt; duy trì dịch vụ đến hết review thực tế.

**Gate:** sản phẩm/source/docs/schema/examples/README/video/worklog truy cập được; prompt/process hợp lệ; receipt nộp bài thực đã ghi nhận. Việc tạo checklist này không phải thao tác gửi bài.

## 19. Bonus có điều kiện — ngoài26h P0

Chỉ bắt đầu khi phase03–11 được nghiệm thu và vẫn đủ thời gian hoàn thiện hồ sơ. **Không bắt đầu bonus mới sau21:00 ngày30/09.**

| Việc | Estimate | Điều kiện nghiệm thu |
|---|---:|---|
| Cost estimation | 0.5–1h | Giá model thực có nguồn/ngày; token unknown được phản ánh; ghi estimate, không gọi invoice |
| Multi-model cùng provider | 1–1.5h | Hai model có quyền truy cập; route allowlist; usage theo actual model |
| Fallback model | 1–1.5h | Shared deadline/attempt cap; test fallback; không claim chống outage toàn provider |

Provider thứ hai, queue, cache, frontend/dashboard, RAG và load/observability platform toàn diện để sau bản nộp nếu thiếu thời gian. Logging cơ bản vẫn là P0 và phải hoàn thành.

## 20. Mốc điều phối và xử lý trễ

| Mốc đích | Ưu tiên | Nếu chưa đạt |
|---|---|---|
| Tối28/09 | Runtime/skeleton/DB/auth; probe model thật; thử deploy sớm | Xử lý blocker đầu29/09, giảm cơ hội làm bonus |
| Cuối29/09 | Chat/history/analyze/ledger/usage bước đầu | Dừng mở rộng UX/customization; hoàn thiện luồng tối thiểu |
| Tối30/09 | Reliability/limiter/metrics và test P0 | Sửa lỗi bắt buộc; không bổ sung bonus sau21:00 |
| 01/10 trước14:00 | Release regression và production smoke | Chỉ fix requirement/blocker; sửa xong chạy lại test liên quan |
| 01/10 trước18:00 | README/docs/worklog hoàn chỉnh, link reviewer dùng được | Tập trung hồ sơ/evidence, giữ claims đúng thực tế |
| 01/10 trước21:00 | Video, form và receipt | Dùng khoảng đệm đến deadline cho lỗi truy cập/upload/nộp |

Các mốc là đích điều phối, chưa phải lịch cá nhân đã xác nhận. Nếu effort vượt26h: dùng4h dự phòng cho lỗi; bỏ toàn bộ bonus trước, không bỏ auth/persistence/schema/retry/timeout/logging/limiter hoặc thay LLM thật bằng mock.

## 21. Việc bắt đầu ngay ở phiên implementation tiếp theo

1. Phase03: JSON login, verify Argon2id và JWT claims/expiry/signature.
2. Thêm bearer dependency và owner-query primitive; chạy auth/security tests.
3. Phase04: adapter LLM thật và request/attempt ledger trước chat/analyze.
4. Hoàn thiện cloud DB credentials/release ở phase deploy; public skeleton vẫn chưa phải sản phẩm cuối.

P01.01–P01.08 và P02.01–P02.06 đã nghiệm thu. Tiếp theo Phase03 authentication. Cloud credentials và full release vẫn thuộc các phase tương ứng.

## 22. Nhật ký nghiệm thu phase — điền khi thực hiện

| Phase | Task IDs hoàn thành | Code version/commit | Command/test + kết quả | Evidence | Blocker/việc còn lại | Thời điểm |
|---|---|---|---|---|---|---|
| 00 | P00.01–P00.04 | Workspace chưa init Git | Inventory + đọc docs + path/runtime checks | Hiện trạng ở mục1 | I01–I06 chưa xác minh đầy đủ; chưa có implementation | 28/09/2026 16:05 UTC+7 |
| 01 | P01.01–P01.08 | GitHub main; deployed source471a653 | pytest20 PASS; Ruff/imports/pip check/wheel/HTTP PASS; Supabase/OpenAI probes PASS; Vercel build/public smoke PASS | [local](artifacts/evidence/phase01.json), [provider](artifacts/evidence/provider-20260928.json), [DB](artifacts/evidence/preflight-20260928.json), [Vercel](artifacts/evidence/vercel-phase01.json) | Không còn blocker Phase01; full integration/release và Git auto-deploy vẫn chưa thực hiện | 28/09/2026 |
| 02 | P02.01–P02.06 | Phase02 working tree | migrate upgrade/check PASS; seed repeat PASS;14 live DB checks, hashes/app/process restart PASS;22 local tests PASS | [phase02](artifacts/evidence/phase02.json) | Cloud Phase02 chưa release; Phase03 auth chưa làm | 28/09/2026 |
| 03–13 | Chưa có | Chưa có | NOT RUN | Chưa có | Chưa bắt đầu | — |

Tạo một dòng riêng cho từng phase khi làm; cập nhật checkbox, bảng trạng thái ở mục3 và AI_WORKLOG cùng lúc. Không dùng bảng này như bằng chứng PASS cho backend khi chỉ mới đọc tài liệu.
