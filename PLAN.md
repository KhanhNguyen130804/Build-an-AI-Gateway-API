# Kế hoạch triển khai AI Gateway

Kế hoạch gốc:28/09/2026. Cập nhật: Phase01 và Phase02 nghiệm thu;22 tests local và kiểm tra Supabase/migration/seed/constraints/restart PASS. OpenAI live probe PASS; Vercel đang chạy skeleton Phase01. Business APIs, cloud DB integration và full release chưa hoàn thành. Xem PHASE_TASKS.md cho trạng thái từng mục.

## 1. Mục tiêu và thời gian

Xây một API trung tâm cho hai ứng dụng nội bộ: trợ lý hội thoại và công cụ phân loại ticket hỗ trợ. Ứng dụng chỉ gửi request tới gateway; gateway quản lý auth, context, provider, timeout/retry, lưu dữ liệu và thống kê.

Hạn theo nội dung người dùng cung cấp: **23:59 ngày 01/10/2026**. Kế hoạch dùng múi giờ **Asia/Saigon (UTC+7)**; timezone của cổng thi chưa được xác nhận riêng. Lúc kiểm tra 15:34 ngày 28/09 còn khoảng **80 giờ 25 phút theo đồng hồ**, không phải 80 giờ làm việc. Mốc nộp nội bộ: **21:00 ngày 01/10**, dành gần ba giờ đệm. Nếu cổng thi hiển thị timezone khác, dùng hạn sớm hơn.

Ngân sách dự kiến **26 giờ thực hiện + 4 giờ dự phòng**. Đây là ước lượng để phân bổ công việc, chưa xác nhận số giờ người dùng có thể dành. Nếu chỉ có 16–20 giờ, bỏ toàn bộ bonus và giữ API examples thay cho collection phức tạp; không cắt yêu cầu tối thiểu hoặc tuyên bố đã hoàn thành phần chưa chạy.

## 2. Quyết định đang mở và giả định

| Việc cần chốt | Phương án chuẩn bị | Điều kiện |
|---|---|---|
| Framework | **Python + FastAPI đã được người dùng chọn** | Python3.12, Pydantic, SQLAlchemy2 async + psycopg, Alembic |
| Database | Supabase PostgreSQL đã được người dùng chọn | Local/migration session pooler; serverless transaction pooler; schema nội bộ gateway |
| LLM | Một provider thật, mặc định thiết kế adapter OpenAI Responses | Key, credit, model và structured output phải qua smoke test |
| Model | `OPENAI_MODEL` từ cấu hình server | Không hard-code tên model hoặc giá chưa xác minh |
| Deployment | Vercel đã được người dùng chọn + Supabase PostgreSQL | Entry point/config đã chuẩn bị; cần kết nối/tài khoản/region/budget thực tế |
| UI | Swagger + Postman/API examples | Đủ demo backend, không cần frontend riêng |
| Người dùng | Seed tài khoản demo/reviewer; không public signup | Password từ secret khi seed; hạn mức chống lạm dụng |
| Budget | Hạn mức user/ngày và gateway/ngày, output cap | Giá trị cuối phụ thuộc ngân sách người dùng |

Preflight cập nhật: `.venv` Python3.12.14 đã tạo; runtime/dev dependencies đã pin, Git repo đã init, private `.env` có JWT/hash secrets ngẫu nhiên. Local health/docs và20 foundation tests pass. Docker chưa có trong PATH, DB/key/model chưa cấu hình hoặc probe thật. Người dùng có tài khoản OpenAI nhưng chưa tạo key, chọn Supabase/Vercel và chưa dùng hai dịch vụ này. Chưa có commit/remote/push hay deploy.

## 3. Phạm vi P0 bắt buộc

1. Login, hash password, JWT hết hạn và kiểm tra chủ sở hữu dữ liệu.
2. PostgreSQL, migration, seed hai user để kiểm tra cách ly.
3. Chat gọi LLM thật; history do server xây từ database, không nhận system role từ client.
4. Analyze dùng structured output thật, kiểm tra schema và xử lý refusal/incomplete.
5. Lưu conversation, message và trạng thái từng AI request, kể cả thất bại đã được tiếp nhận.
6. Ghi từng provider attempt để phân biệt request người dùng với retry.
7. Error envelope nhất quán; request ID xuyên suốt response/log/database.
8. Retry có giới hạn và total deadline; không retry lỗi cấu hình hoặc quota cạn.
9. Rate limit dùng counter atomically trong PostgreSQL; daily cap cho bản demo.
10. Usage API với công thức, mẫu đối chiếu SQL và token thiếu metadata được đánh dấu.
11. Test các lỗi và cách ly dữ liệu; LLM live smoke test; deployed API thật.
12. README, docs API, sơ đồ, schema, examples, video ≤5 phút, AI_WORKLOG và form nộp.

Không làm trong P0: frontend, public signup, OAuth server, refresh token, streaming, upload file, RAG/vector DB, agent/tools, microservices, Kafka, Kubernetes, queue và cache. Đây là cách giữ phạm vi đủ hoàn thành; không xem chúng là điều kiện đạt challenge.

## 4. Bonus theo thứ tự và điểm dừng

| Ưu tiên | Bonus | Thời gian dự kiến | Chỉ bắt đầu khi |
|---|---|---:|---|
| P1a | Log JSON có request ID/provider ID; thống kê attempt/retry | Nằm trong P0 logging, không gọi là full observability | Hoàn thành telemetry cơ bản |
| P1b | Cost estimation từ token và bảng giá ghi ngày | 0.5–1 giờ | Token usage đúng và giá model đã xác minh |
| P1c | Hai model cùng provider; route `fast`/`standard` | 1–1.5 giờ | Cả hai model có quyền truy cập và schema phù hợp |
| P1d | Fallback model dùng chung deadline và attempt cap | 1–1.5 giờ | Test 503→fallback và usage theo model thật pass |
| P2 | Provider thứ hai, queue, cache, dashboard metrics | Sau deadline | Không kéo vào bản nộp tối thiểu |

**Không bắt đầu bonus sau 21:00 ngày 30/09.** Fallback model cùng provider không được mô tả là bảo vệ khỏi outage toàn provider. Chỉ tuyên bố bonus nào đã test và có bằng chứng.

## 5. Lộ trình và cổng nghiệm thu

Các giờ dưới đây là effort, các ngày là mốc đích. Sắp xếp ca làm việc sau khi biết lịch rảnh của người dùng.

| Mốc | Effort | Việc hoàn thành | Cổng nghiệm thu |
|---|---:|---|---|
| 28/09 | 5 giờ | Chốt stack/key/host; skeleton; PostgreSQL+migration; auth; một call LLM thật; thử deploy sớm | G0: runtime chạy, DB `SELECT 1`, login pass, call provider có usage, health online hoặc xác định và xử lý blocker deploy |
| 29/09 | 7 giờ | Chat+history, analyze+schema, request/attempt persistence, usage | G1: luồng login→chat 2 lượt→analyze→history→usage chạy trên API deploy, restart không mất dữ liệu |
| 30/09 | 7 giờ | Error mapping, retry/deadline, limiter, ownership, integration tests; tối đa một bonus nếu dư giờ | G2: test lỗi có evidence; hai user cách ly; usage đối chiếu được; 21:00 dừng mở rộng scope |
| 01/10 trước 14:00 | 2 giờ | Regression, clean checkout, migration, production smoke | G3: freeze code khi P0 pass; mọi sửa đổi sau đó phải chạy lại kiểm tra liên quan |
| 01/10 14:00–18:00 | 3 giờ | Hoàn thiện README/worklog/docs/schema; kiểm tra link và ẩn danh | G4: hồ sơ thể hiện đúng code và giới hạn thực tế |
| 01/10 18:00–21:00 | 2 giờ | Quay video, điền form, kiểm tra và nộp | G5: video ≤5 phút, link truy cập được, ghi nhận trạng thái nộp thành công |
| Dự phòng | 4 giờ | Lỗi deployment/provider, sửa test hoặc quay lại demo | Không dùng dự phòng để thêm feature |

Nếu G0 chưa xong cuối 28/09: dành đầu 29/09 sửa key/deploy, bỏ bonus. Nếu G1 chưa xong cuối 29/09: giữ endpoint tối thiểu, bỏ dashboard và customization. Nếu G2 còn lỗi bảo mật/usage/deadline: sửa trước, không quay video che lỗi. Nếu đến 01/10 chỉ còn thời gian ngắn: ưu tiên tính đúng, đường deploy ổn định và hồ sơ trung thực.

## 6. Backlog sẵn sàng thực hiện

| ID | Việc | Phụ thuộc | Done khi | Giờ |
|---|---|---|---|---:|
| B00 | Chốt stack; runtime/DB/key/credit/deploy smoke | Không | Ghi quyết định, call thật, không đưa secret vào repo | 1.0 |
| B01 | Skeleton, config validation, health, docs, error/request-ID foundation | B00 | Server chạy; thiếu config fail rõ; secret được redact | 1.0 |
| B02 | DB migration và seed; constraints/index | B01 | DB mới migrate+seed; ownership constraints đúng | 1.5 |
| B03 | Auth JSON, password hash, JWT, auth guard/dependency | B02 | Login valid/invalid/expired; Swagger bearer | 1.5 |
| B04 | Adapter LLM thật + bounded request/attempt ledger | B01–B03 | LLM response + metadata được lưu; fake chỉ dùng trong test | 2.0 |
| B05 | Conversation + chat context và serialization theo conversation | B04 | 2 lượt có context; persist sau restart; user B không đọc A | 2.0 |
| B06 | Structured ticket analysis + refusal/incomplete/schema handling | B04 | JSON đúng schema; xử lý lỗi không trả success giả | 1.5 |
| B07 | Usage aggregates + SQL đối chiếu | B05–B06 | Fixture 5 request cho số liệu đúng; retry không nhân request | 1.5 |
| B08 | Retry policy, error mapping, cancellation và total deadline | B04 | 503→success; quota không retry; deadline bounded | 2.0 |
| B09 | DB rate limiter; login IP limiter; daily safety cap | B02–B03 | N request song song chỉ đúng số cho phép gọi provider | 1.5 |
| B10 | Integration/security tests và bằng chứng lỗi | B05–B09 | Các ca P0 ở VERIFICATION pass trên Postgres | 3.5 |
| B11 | Deploy sớm rồi production smoke, clean checkout | B01 sớm; B10 hoàn thiện | HTTPS/docs/DB/LLM thật; migration và restart pass | 2.5 |
| B12 | Hoàn thiện README, schema, docs, worklog, form | Làm dần; chốt sau B10–B11 | Không placeholder, không fake evidence; hướng dẫn lặp lại | 2.5 |
| B13 | Quay demo và kiểm tra/nộp | B12 | Video ≤5 phút, các link mở được, receipt thật | 2.0 |
|  | Tổng |  | Có thể điều chỉnh sau buổi đầu; chưa gồm bonus/dự phòng | **26.0** |

Thực hiện B04 theo vertical slice nhỏ trước, tránh viết toàn bộ nền tảng rồi mới phát hiện model/key không hoạt động. Chuẩn bị deploy ở B01/B02 và test B11 theo từng mốc, không đợi cuối cùng.

## 7. Ma trận yêu cầu → bằng chứng

| Yêu cầu challenge | Thiết kế/đầu ra | Bằng chứng phải có |
|---|---|---|
| Authentication | `/v1/auth`, bearer, password hash, JWT expiry | 200 login; 401 sai/thiếu/expired |
| Database integration | PostgreSQL + migration + seed | Khởi tạo DB mới; data còn sau restart |
| LLM integration | Adapter thật | Deployed call; provider ID; model và usage thật |
| Structured output | Ticket schema version 1 | JSON valid; refusal/incomplete không thành 200 |
| Conversation storage | conversations/messages | 2 lượt có context, GET trả messages |
| Error handling | Error envelope + status mapping | JSON lỗi có code/request_id, không lộ stack/key |
| Retry | Attempt ledger + cap/backoff | Test 503 rồi success; 1 logical request, 2 attempts |
| Timeout | Total deadline + per-attempt budget | Fake slow upstream, response bounded, DB terminal |
| Logging | JSON stdout, redact | Dò request_id nối log/request/attempt |
| Rate limiting | Atomic DB buckets | Parallel test; 429 có Retry-After, không gọi upstream |
| Per-request audit | user/model/time/latency/tokens/status | SQL row cho success, fail, timeout và rate-limit |
| Usage API | Aggregate riêng request/attempt | Fixture và công thức trong DATABASE.md |
| Source | Repo với config/example/lockfile | Clone sạch chạy được; không secret |
| API documentation | Runtime OpenAPI + API guide | Docs live khớp response thật |
| Architecture diagram | Mermaid + ảnh xuất khi nộp | Mở được trong repo; tên thành phần khớp code |
| Database schema | Migration + ERD + SQL thiết kế | So sánh migration thực tế với schema |
| Postman/API examples | Collection và example inputs | Run against deployed API |
| Deployed API | HTTPS và persistent DB | Reviewer truy cập được trong thời gian review |
| README | Hướng dẫn, metrics, limitations | Người khác làm lại từ checkout sạch |
| Demo ≤5 phút | Script trong SUBMISSION.md | Có luồng thật và evidence lỗi có nhãn |
| AI_WORKLOG | Log theo phiên, prompt, sai/sửa, evidence | Phân biệt đã dùng với prompt chuẩn bị |
| Ít nhất một prompt + process ≥30 ký tự | Mẫu form | Prompt thật từ phiên này + mô tả sửa theo thực tế |

## 8. Tối ưu theo rubric 0–4

| Tiêu chí | Cách chứng minh | Tránh |
|---|---|---|
| Chất lượng prompt | Bối cảnh/role/constraints/output/acceptance rõ; prompt phiên thực có trong worklog | Chỉ ghi “hãy code giúp tôi” |
| Chất lượng kết quả | API live, collection, một use case hoàn chỉnh | Nhiều endpoint chỉ trả dữ liệu mock |
| Tư duy kiểm chứng | Test ownership, retry, deadline, schema và metric; lưu sai/sửa AI thực | Kể lỗi AI chưa từng xảy ra |
| Ứng dụng thực tế | Hai client tích hợp cùng một contract; đo một tác vụ tích hợp/ticket cụ thể | Số giờ tiết kiệm tự bịa hoặc claim scale chưa test |
| Trình bày/chia sẻ | README clean setup, diagram, video dưới 5 phút, prompt/workflow tái lập | Video chỉ đọc slide hoặc che lỗi |

Không thể bảo đảm điểm chấm. Mục tiêu là bằng chứng rõ ở cả năm tiêu chí thay vì chạy theo số feature.

## 9. Rủi ro và hành động

| Rủi ro | Kiểm tra sớm | Hành động |
|---|---|---|
| Chưa có key/credit hoặc model không hỗ trợ schema | B00, trong giờ đầu | Đổi sang provider có quyền truy cập; cập nhật adapter/spec; không nộp mock như real |
| Python/Docker chưa có | Preflight đã phát hiện PATH | Chọn runtime phù hợp; managed Postgres không cần Docker local; không cài mọi thứ cùng lúc |
| Deploy cần thanh toán hoặc fail build | Deploy skeleton 28/09 | Chốt budget/host; giữ Docker/build runbook portable |
| Retry lồng SDK gây request gấp nhiều lần | Đọc docs + spy attempts | SDK max_retries=0, gateway là nơi điều phối duy nhất |
| Timeout vẫn bị provider tính phí | Test read-timeout; kiểm tra ledger | Không replay read-timeout mặc định; đánh dấu usage unknown |
| Counter memory sai khi nhiều worker/restart | Parallel/restart test | DB counter chung; ghi giới hạn fixed-window |
| User đọc hội thoại người khác | 2-user integration test | Filter user_id + 404 cho resource ngoài quyền |
| Metric sai do JOIN messages/attempts | Fixture 5 request | Aggregate từng tập rồi ghép; không cộng số nhân bản |
| Reviewer dùng hết quota demo | Giới hạn riêng/global, theo dõi thời gian review | Điều chỉnh cap trong budget; video/API examples dự phòng có nhãn |
| Mất ẩn danh | Soát README/video/file export | Bỏ tên, avatar, logo; GitHub có thể lộ tài khoản nên cần kiểm tra quy định cổng thi |
| Link hết hạn sau deadline | Smoke + policy host/video | Duy trì API đến ít nhất 08/10/2026 và đến khi review thực tế kết thúc |

## 10. Điều kiện bắt đầu implementation

- Stack đã chốt FastAPI; số giờ rảnh cần xác nhận, hiện dùng 26 giờ + 4 giờ dự phòng.
- Runtime dùng được; Postgres test/deploy truy cập được.
- Key được cấu hình bằng secret, không gửi qua chat; smoke test provider thật đã pass.
- Nơi deploy và budget đã rõ; model có structured output được xác minh.
- API/schema/acceptance ở bộ tài liệu này được dùng làm nguồn thiết kế; mọi thay đổi cập nhật lại cùng code.

Những tài khoản/secret/quyền deploy phụ thuộc người dùng vẫn chưa được xác minh. Bộ tài liệu sẵn sàng để thực hiện; chưa thể gọi môi trường thực thi là sẵn sàng hoàn toàn.
