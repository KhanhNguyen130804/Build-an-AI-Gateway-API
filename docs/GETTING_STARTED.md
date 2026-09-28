# Bắt đầu với OpenAI, Supabase và Vercel

**Trạng thái28/09/2026:** Phase01 chạy local và20 test đã pass. Chưa kết nối DB/LLM thật, chưa deploy. Các bước dưới đây chuẩn bị phần tài khoản mà project chưa có quyền truy cập.

## 1. Xem phần đã chạy

Tại workspace, dùng Python của venv, không cần activate PowerShell:

```powershell
& .\.venv\Scripts\python.exe -m app
```

Mở [Swagger local](http://127.0.0.1:8000/docs). `/health/live` trả200; `/health/ready` trả503 vì Phase02 chưa tích hợp DB. Swagger hiện chỉ có hai health endpoints; auth/chat/analyze/history/usage sẽ được thêm ở các phase sau.

`.env` riêng đã được tạo với JWT/hash secrets ngẫu nhiên, không đưa vào Git. `scripts/bootstrap_env.py` không ghi đè khi file đã tồn tại. Development được phép chưa có DB/LLM để dựng skeleton; production từ chối thiếu config bắt buộc.

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

Probe chỉ `SELECT 1`, không tạo/xóa schema hay bảng. Phase02 mới tạo ORM/migration/seed và gắn DB vào readiness.

Supabase mô tả session pooler cho IPv4 và transaction pooler cho serverless: [connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres).

### Vercel và transaction pooler

Trên Vercel, dùng Transaction pooler port6543 cho short-lived connections. Psycopg phải tắt prepared statements (`prepare_threshold=None`); dùng transaction-local state, không phụ thuộc `SET` hoặc session locks tồn tại qua nhiều transaction. Phase02 sẽ cấu hình SQLAlchemy pool/driver cho serverless. Migration dùng session/direct connection riêng; không chạy migration trong mỗi invocation.

### Dữ liệu gateway và Supabase Data API

Gateway dùng JWT của chính gateway, không mặc định là Supabase Auth. Đặt sáu bảng trong schema nội bộ `gateway`, không thêm schema này vào exposed schemas của Data API. Phase02 phải kiểm tra grants/RLS và quyền anon/authenticated, tránh để user/password hash/conversation/usage có thể đọc trực tiếp ngoài gateway. [Supabase Data API security](https://supabase.com/docs/guides/api/securing-your-api).

## 4. Chuẩn bị Vercel

Đã có `app/vercel.py` export FastAPI instance, `tool.vercel.entrypoint` trong pyproject và `vercel.json` đặt function maxDuration60s. Đây là cấu hình chuẩn bị; Vercel build/deploy chưa được chạy. [FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi), [Python runtime](https://vercel.com/docs/functions/runtimes/python).

1. Chuẩn bị GitHub repository và push source, không push `.env`/venv.
2. Trong Vercel, import repository, kiểm tra preset FastAPI và Python3.12 theo pyproject.
3. Thêm environment variables trong Vercel cho environment cần deploy. DB URL deploy có thể khác local do dùng transaction pooler.
4. Phase01 skeleton có thể chạy development mode để kiểm tra build/health; chưa xem đó là release sản phẩm. Bản production sau phải cấu hình `APP_ENV=production` và đủ secrets/model/database/caps.
5. Sau khi integration có, migrate/seed một lần riêng trước release. Không chạy Uvicorn long-lived process hoặc dùng filesystem như database trong serverless function.
6. Deploy và mở `/health/live`, `/docs`, `/openapi.json`; `/health/ready` chỉ thành200 sau Phase02 và DB thực sự hoạt động.

Local runner dùng `python -m app`; Vercel load ASGI instance trực tiếp. Dockerfile là lựa chọn portable khác, không phải cách Vercel chạy function.

## 5. Kiểm tra và cập nhật key/config

```powershell
& .\.venv\Scripts\python.exe scripts/preflight.py
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe -m ruff check app tests scripts/bootstrap_env.py scripts/preflight.py
```

Sau khi chỉnh `.env`, restart server để nhận config mới. Với runner đang hoạt động, dừng bằng Ctrl+C rồi chạy lại.

Khi xong phần tài khoản, chỉ cần thông báo “đã cấu hình .env”. Việc có key không tự chứng minh billing/model/DB hoạt động; cần probe thật và ghi evidence. Nếu probe FAIL, gửi loại lỗi/code đã redact, không gửi secret hoặc connection string đầy đủ.
