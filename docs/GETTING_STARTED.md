# Bắt đầu với OpenAI, Supabase và Vercel

**Cập nhật28/09/2026:** Phase01–03 đã hoàn tất local. 35 pytest tests, Ruff và read-only auth probe với seeded DB account PASS trong lần triển khai Phase03; các kiểm tra DB/OpenAI lịch sử được ghi riêng. Vercel vẫn chạy skeleton Phase01, chưa có cloud DB/LLM credentials. Local `.env` đã được cấu hình riêng. [Swagger online](https://ai-gateway-challenge.vercel.app/docs). Các bước dưới đây hướng dẫn tái lập môi trường; kết quả cũ không thay thế việc kiểm tra lại sau thay đổi.

## 1. Xem phần đã chạy

Tại workspace, dùng Python của venv, không cần activate PowerShell:

```powershell
& .\.venv\Scripts\python.exe -m app
```

Mở [Swagger local](http://127.0.0.1:8000/docs). `/health/live` kiểm tra process; `/health/ready` trả200 khi `DATABASE_URL` truy cập được và revision `0001_gateway` đã áp dụng, nếu không trả503 an toàn. Cloud Vercel chưa có DB credentials nên readiness của bản public vẫn có thể trả503. Local runtime hiện có `POST /v1/auth` và `GET /v1/auth/me`; chat/analyze/history/usage chưa được triển khai.

`.env` riêng đã được tạo với JWT/hash secrets ngẫu nhiên, không đưa vào Git. `scripts/bootstrap_env.py` không ghi đè khi file đã tồn tại. Development có thể khởi động khi thiếu DB/LLM, nhưng login cần database và `JWT_SECRET`; production từ chối thiếu cấu hình bắt buộc.

Để thử auth local, dùng tài khoản seed riêng trong `.env` hoặc tài khoản đã seed trong DB. Trong Swagger gọi `POST /v1/auth` bằng JSON `{"username":"...","password":"..."}`, sao chép `access_token` vào nút **Authorize** dưới dạng Bearer, rồi gọi `GET /v1/auth/me`. Không đưa password vào query string, log hoặc Postman export. Xem [Phase03 auth guide](PHASE03_AUTH.md) để biết claim/TTL và lệnh kiểm chứng read-only.

## 2. Tạo OpenAI API key

1. Đăng nhập OpenAI API Platform, chọn project dùng cho challenge.
2. Mở phần API keys, tạo key cho project và lưu riêng; kiểm tra billing/credit và usage limits của tài khoản.
3. Điền `OPENAI_API_KEY` trong `.env` ở workspace. Không paste giá trị vào chat hoặc commit.
4. Chọn model hỗ trợ Responses và structured output. Có thể thử `OPENAI_MODEL=gpt-4.1-mini`; tài liệu chính thức ghi nhận hai khả năng này, nhưng quyền truy cập/credit của tài khoản vẫn cần live probe.

[OpenAI quickstart](https://developers.openai.com/api/docs/quickstart), [GPT-4.1 Mini capabilities](https://developers.openai.com/api/docs/models/gpt-4.1-mini).

Ví dụ cấu hình (không phải key thật):

```dotenv
OPENAI_API_KEY=YOUR_PRIVATE_PROJECT_KEY
OPENAI_MODEL=gpt-4.1-mini
```

Khi đã cấu hình, probe một call thật, có thể phát sinh phí:

```powershell
& .\.venv\Scripts\python.exe scripts/preflight.py --provider
```

Probe không chạy tự động khi server khởi động. Nó kiểm tra structured response và metadata, không chứng minh các business endpoints đã hoàn thành. Không có key/model thì báo NOT_CONFIGURED, không thay bằng mock.

## 3. Tạo PostgreSQL project trên Supabase

1. Đăng nhập Supabase Dashboard; tạo một project riêng cho challenge, chọn region phù hợp với nơi deploy.
2. Đặt database password và lưu riêng. Không đưa dữ liệu công ty thật vào project demo.
3. Chờ database provision xong, mở **Connect** để lấy PostgreSQL connection string. Gateway dùng SQLAlchemy/psycopg trực tiếp, chưa cần Supabase client, anon key hoặc service-role API key.
4. Cho Windows/local hoặc migration: chọn **Session pooler** port5432 nếu mạng không hỗ trợ direct IPv6. Copy nguyên hostname và username từ dashboard; không tự suy ra từ region.
5. Thay phần password bằng password DB đã đặt; URL-encode ký tự đặc biệt trong password. Giữ TLS theo hướng dẫn endpoint, không tắt certificate verification để chữa lỗi.
6. Điền `DATABASE_URL` trong `.env`. Nên thêm `sslmode=require` để mã hóa đường truyền nếu URL chưa có; khi cần verify-full dùng CA chính thức của provider.

Ví dụ phải thay bằng giá trị của project:

```dotenv
DATABASE_URL=postgresql://postgres.PROJECT_REF:URL_ENCODED_PASSWORD@ACTUAL_POOLER_HOST:5432/postgres?sslmode=require
```

Chạy probe read-only trước migration:

```powershell
& .\.venv\Scripts\python.exe scripts/preflight.py --database
```

Probe chỉ `SELECT 1`, không tạo/xóa schema hay bảng. Phase02 đã thêm ORM/migration/seed và gắn DB vào readiness. Dùng các lệnh ở [Phase02 runbook](PHASE02_DATABASE.md) để áp dụng migration/seed trên một database mới.

Supabase mô tả session pooler cho IPv4 và transaction pooler cho serverless: [connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres).

### Vercel và transaction pooler

Trên Vercel, dùng Transaction pooler port6543 cho short-lived connections. Psycopg tắt prepared statements (`prepare_threshold=None`); app dùng transaction-local state, không phụ thuộc `SET` hoặc session locks tồn tại qua nhiều transaction. SQLAlchemy dùng psycopg async và NullPool; migration dùng session/direct connection riêng, không chạy migration trong mỗi invocation.

### Dữ liệu gateway và Supabase Data API

Gateway dùng JWT của chính gateway, không mặc định là Supabase Auth. Đặt sáu bảng trong schema nội bộ `gateway`, không thêm schema này vào exposed schemas của Data API. Phase02 đã kiểm tra grants/RLS và quyền anon/authenticated; dashboard exposed-schema settings chưa được kiểm tra độc lập. Backend hiện dùng credential có quyền cao, nên giữ `.env` riêng và không cấp credential đó cho client. [Supabase Data API security](https://supabase.com/docs/guides/api/securing-your-api).

## 4. Chuẩn bị Vercel

Đã có `app.vercel:app`, `tool.vercel.entrypoint` trong pyproject và `vercel.json` đặt function maxDuration60s. Skeleton đã được build/deploy và public-smoke bằng Vercel CLI; Git auto-deploy chưa kết nối. Bản hiện tại trên Vercel chưa gồm Phase02/03 và chưa có cloud DB/JWT/provider configuration. [FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi), [Python runtime](https://vercel.com/docs/functions/runtimes/python).

1. Dùng repository GitHub đã có hoặc kết nối repository của checkout; không push `.env`/venv. Git auto-deploy chưa kết nối nên release đã dùng Vercel CLI.
2. Trong Vercel, import repository, kiểm tra preset FastAPI và Python3.12 theo pyproject.
3. Thêm environment variables trong Vercel cho environment cần deploy. DB URL deploy có thể khác local do dùng transaction pooler.
4. Phase01 skeleton có thể chạy development mode để kiểm tra build/health; chưa xem đó là release sản phẩm. Bản production sau phải cấu hình `APP_ENV=production` và đủ secrets/model/database/caps.
5. Sau khi integration có, migrate/seed một lần riêng trước release. Không chạy Uvicorn long-lived process hoặc dùng filesystem như database trong serverless function.
6. Deploy và mở `/health/live`, `/docs`, `/openapi.json`; `/health/ready` cần source có Phase02 cùng DB credentials hợp lệ. Bản public hiện vẫn là Phase01 skeleton.

Local runner dùng `python -m app`; Vercel load ASGI instance trực tiếp. Skeleton đã được build/deploy bằng Vercel CLI; Git auto-deploy chưa kết nối. Dockerfile là lựa chọn portable khác, không phải cách Vercel chạy function. Trước khi release source mới, dùng `scripts/migrate.py` và `scripts/seed.py` một lần theo runbook; không chạy schema mutation trong mỗi request/function.

## 5. Kiểm tra và cập nhật key/config

```powershell
& .\.venv\Scripts\python.exe scripts/preflight.py
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m ruff check app tests scripts migrations
```

Sau khi chỉnh `.env`, restart server để nhận config mới. Với runner đang hoạt động, dừng bằng Ctrl+C rồi chạy lại.

Khi xong phần tài khoản, chỉ cần thông báo “đã cấu hình .env”. Việc có key không tự chứng minh billing/model/DB hoạt động; cần probe thật và ghi evidence. Nếu probe FAIL, gửi loại lỗi/code đã redact, không gửi secret hoặc connection string đầy đủ.
