# Hướng dẫn agent — AI Gateway

## Mục tiêu và nguồn sự thật

- Dự án xây một API gateway cho ứng dụng chat có lưu lịch sử và phân loại support ticket thành JSON có cấu trúc. Stack đã chọn: Python 3.12, FastAPI, PostgreSQL/Supabase, SQLAlchemy async, psycopg và Alembic; OpenAI là provider dự kiến, Vercel là host đã chọn.
- Trước khi làm việc, đọc `PHASE_TASKS.md` để nắm phase và checklist hiện tại; đọc `PLAN.md` cho phạm vi; đọc các tài liệu chuyên đề liên quan tới task.
- Runtime trong `app/` là căn cứ để kết luận route và behavior đang hoạt động. `docs/openapi.json`, Postman, SQL thiết kế, ORM model hoặc checklist không tự chứng minh endpoint hay luồng nghiệp vụ đã được triển khai.
- Alembic migration là nguồn DDL triển khai. `db/schema.sql` là tài liệu tham chiếu, không dùng thay migration.
- Phân biệt rõ code runtime, nền tảng/schema, thiết kế, và evidence lịch sử. Mọi nhận định về dịch vụ bên ngoài phải nêu thời điểm/phạm vi evidence; không suy ra trạng thái hiện tại từ evidence cũ.
- Một probe gọi OpenAI độc lập không chứng minh gateway có provider adapter hoặc endpoint AI.

## Bố cục chính

- `app/main.py`: FastAPI app factory, lifespan và đăng ký router.
- `app/api/`: HTTP routers; chỉ coi route được đăng ký trong app là runtime API.
- `app/core/`: settings, lỗi, logging, middleware, password verification và JWT.
- `app/db/`: PostgreSQL session, ORM models, seed và query helpers.
- `app/providers/`, `app/services/`: nơi đặt provider adapters và nghiệp vụ khi phase tương ứng được thực hiện; sự hiện diện của package không khẳng định tính năng đã xong.
- `migrations/`, `alembic.ini`: migration Alembic.
- `scripts/`: setup, preflight, migrate, seed và verifier; một số script gọi dịch vụ thật hoặc ghi file.
- `tests/`: unit và foundation tests. Không coi fake session/provider là bằng chứng cho hành vi live.
- `docs/`, `examples/`, `artifacts/evidence/`: thiết kế, hướng dẫn, ví dụ và bằng chứng có thời điểm/phạm vi cụ thể.

## Quy tắc làm việc

- Làm đúng scope người dùng yêu cầu. Với yêu cầu chỉ đọc, chỉ kiểm tra và báo cáo; không sửa file, tạo kế hoạch mới, chạy test hoặc thực thi script.
- Trước khi sửa, xem trạng thái Git và giữ nguyên thay đổi sẵn có. Không commit, push, deploy, migrate, seed hoặc thay đổi tài khoản/cấu hình từ xa trừ khi người dùng yêu cầu.
- Giữ thay đổi nhỏ, có mục đích; cập nhật tài liệu liên quan khi behavior hoặc contract thay đổi. Không tạo lại tài liệu generated nếu task không yêu cầu.
- Dùng Python 3.12 và tuân theo cấu hình Ruff trong `pyproject.toml` (line length 100). Giữ code async nhất quán với FastAPI và SQLAlchemy async hiện có.
- Kiểm tra input ở runtime bằng Pydantic; từ chối field ngoài contract khi phù hợp. Không dựa vào type hints để thay runtime validation.
- Truy vấn tài nguyên có chủ sở hữu phải luôn scope theo user đã xác thực. Không xem UUID là cơ chế phân quyền.
- Dùng Alembic cho thay đổi schema mới. Không chỉnh sửa lịch sử migration đã áp dụng; tạo revision mới. Không chạy DDL trong startup hoặc mỗi invocation serverless.
- Giữ `request_id` xuyên suốt response/log/DB khi có ledger. Log chỉ metadata đã làm sạch; không log credentials, bearer token, password, DB URL, prompt/ticket thô hoặc provider response thô.
- Khi triển khai LLM, model/route phải do server allowlist quyết định; không nhận API key, base URL hay model tùy ý từ client. Tắt retry của SDK nếu gateway quản lý retry. Token/usage chưa được provider báo phải giữ trạng thái unknown/partial, không đổi thành số 0 giả.

## Secrets, dịch vụ thật và lệnh có side effect

- Không mở, in, trích dẫn, đưa vào output hoặc commit `.env` hay secret khác. Chỉ kiểm tra sự hiện diện/trạng thái ignore khi cần. Dùng `.env.example` để hiểu tên biến và giá trị mẫu.
- Không tự chạy `scripts/seed.py`, `scripts/migrate.py upgrade`, `scripts/verify_database.py` hoặc `scripts/verify_restart.py`: chúng có thể sửa DB, tạo/dừng process hoặc ghi evidence.
- `scripts/verify_auth.py` ghi `artifacts/evidence/phase03.json`; chỉ chạy khi được yêu cầu và đã xác định rõ môi trường DB.
- `scripts/preflight.py --provider` gọi provider thật và có thể phát sinh phí. Không chạy nếu người dùng chưa yêu cầu rõ.
- `scripts/preflight.py --database` chỉ thực hiện probe DB theo thiết kế, nhưng vẫn kết nối dịch vụ thật; chỉ chạy khi phạm vi task cho phép kiểm tra live.
- `scripts/build_planning_artifacts.mjs` ghi đè `docs/openapi.json`, Postman collection và `examples/tickets.json`. Không chạy để kiểm tra runtime; nếu task yêu cầu chạy, xem diff của cả ba output.
- Không tuyên bố Vercel/Supabase/OpenAI đang hoạt động chỉ từ URL, config cục bộ hoặc evidence lịch sử. Deployment và provider smoke cần được ghi đúng phiên bản, thời gian và phạm vi.

## Tests và evidence

- Không thêm hoặc chạy tests trừ khi người dùng yêu cầu kiểm chứng. Khi được yêu cầu, chọn các test liên quan trước; DB-specific behavior cần PostgreSQL phù hợp, không coi SQLite/fake là thay thế tương đương.
- Không dùng suite test để gọi provider trả phí. Dùng fake adapter cho lỗi, retry và concurrency; đánh nhãn rõ mọi fake/synthetic evidence.
- Không tự sửa evidence lịch sử để thể hiện kết quả mới. Chỉ cập nhật evidence khi lệnh tương ứng thật sự đã chạy; ghi ngày/giờ, commit, môi trường, command, kết quả, scope và giới hạn.
- Trong báo cáo, phân biệt kết quả vừa chạy với nội dung đọc từ worklog/evidence cũ; nêu rõ phần chưa xác minh.

## Hoàn tất task

- Tóm tắt file thay đổi và lý do.
- Nêu kiểm tra đã chạy với kết quả thực; nếu không chạy, ghi rõ.
- Nêu giới hạn hoặc trạng thái bên ngoài chưa xác minh khi chúng ảnh hưởng kết luận.
- Không mở rộng task sang commit, push, deploy hoặc thao tác gửi dữ liệu nếu chưa được yêu cầu.
