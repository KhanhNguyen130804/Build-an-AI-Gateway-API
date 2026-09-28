# Hai lựa chọn stack

Trạng thái: **người dùng đã chọn Python + FastAPI** sau phần so sánh. Tài liệu giữ cả hai lựa chọn để giải thích quyết định; chỉ triển khai nhánh FastAPI.

## Hiểu từng thành phần

Python/TypeScript là ngôn ngữ. FastAPI/NestJS là framework HTTP. PostgreSQL là database. SQLAlchemy/Prisma là lớp truy vấn và mô hình database. Alembic/Prisma Migrate quản lý thay đổi schema. SDK LLM gọi provider; framework không tự làm cho LLM chính xác.

| Khía cạnh | FastAPI | NestJS |
|---|---|---|
| Ngôn ngữ/runtime | Python, async/await | TypeScript trên Node.js, async/await |
| Tổ chức | Router, service, repository; tự đặt ranh giới | Module, controller, provider/service; DI theo framework |
| Input validation | Pydantic | DTO + ValidationPipe/class-validator |
| LLM output validation | Pydantic + structured-output SDK | Zod + structured-output SDK |
| API docs | OpenAPI và Swagger từ khai báo FastAPI | `@nestjs/swagger` và DTO/decorator |
| Database đề xuất | SQLAlchemy 2 async + psycopg + Alembic | Prisma + PostgreSQL driver theo bản Prisma chốt |
| Auth đề xuất | PyJWT + pwdlib Argon2 | JWT library + Argon2; guard kiểm tra user |
| Test | pytest, HTTP client async, fake adapter | Jest, Supertest, fake adapter |
| Độ dài phần khung | Thường ít khai báo hơn cho prototype nhỏ | Nhiều khai báo hơn, ranh giới trách nhiệm rõ |
| Lợi khi đã quen | Python backend/AI/data | JS/TS, Angular hoặc Java/Spring-style DI |
| Máy hiện tại | Python chưa thấy trong PATH | Node/npm có trong PATH |

FastAPI có validation và docs tích hợp: [tài liệu chính thức](https://fastapi.tiangolo.com/features/). NestJS mô tả kiến trúc module/DI trong [introduction](https://docs.nestjs.com/); validation qua [ValidationPipe](https://docs.nestjs.com/techniques/validation), Swagger qua [OpenAPI integration](https://docs.nestjs.com/openapi/introduction).

## Ưu/nhược điểm dễ áp dụng cho bài này

**FastAPI:** ít ceremony, schema Pydantic có thể dùng cho request và kiểm tra output; phù hợp hoàn thành một luồng nhỏ nhanh nếu đã biết Python. Đổi lại phải tự giữ tổ chức dự án, dùng async đúng và chuẩn bị runtime. Python type hint không thay thế runtime validation cho mọi dữ liệu.

**NestJS:** module Auth/AI/Conversations/Usage dễ giải thích; TypeScript giúp compiler/editor kiểm tra phần lớn kết nối nội bộ. Đổi lại cần hiểu decorator, DI, guard, pipe và exception filter. Kiểu TypeScript bị xóa lúc chạy, nên request và output LLM vẫn phải được validate. Chọn NestJS khi đã quen JS/TS; không dành sát deadline để học framework chỉ vì muốn sơ đồ nhìn lớn.

Trong gateway này, cần đo latency LLM/DB/network trước khi lo chênh lệch tốc độ framework. Chưa có benchmark của dự án để kết luận stack nào nhanh hơn. Cả hai đều có thể đáp ứng toàn bộ P0.

## Dependency shortlist, chưa cài

Không pin phiên bản giả trong giai đoạn chuẩn bị. Sau chọn stack: kiểm tra compatibility, cài, tạo lockfile và dùng đúng runtime đã test cho CI/deploy.

- FastAPI: `fastapi`, `uvicorn`, `pydantic-settings`, `sqlalchemy`, `psycopg`, `alembic`, `openai`, `pyjwt`, `pwdlib[argon2]`, `pytest`, HTTP test client. Dùng stdlib logging JSON formatter nhỏ; không thêm observability platform để hoàn thành P0.
- NestJS: Nest core/platform, config, swagger, DTO validation, Prisma client/migrate + driver phù hợp, OpenAI SDK, JWT, Argon2, Zod, Jest/Supertest. Kiểm tra native Argon2 build trong Docker/host ngay B00.
- Cả hai: gateway điều phối retry; tắt retry tự động SDK. DB là persistence và fixed-window limiter. Không bắt buộc Redis/Docker Desktop local.

## Layout dự kiến

FastAPI:

```text
app/
  main.py
  api/{auth,chat,analyze,conversations,usage,health}.py
  core/{config,security,errors,logging}.py
  db/{models,session}.py
  services/{gateway,conversation,usage,rate_limit}.py
  providers/{base,openai}.py
  schemas/{auth,chat,analysis,usage}.py
migrations/
tests/
```

NestJS:

```text
src/
  main.ts
  app.module.ts
  common/{config,guards,filters,logging}/
  auth/
  ai/{gateway,providers,dto,schemas}/
  conversations/
  usage/
  rate-limit/
  database/
prisma/{schema.prisma,migrations}/
test/
```

Các tên trong layout là trách nhiệm dự kiến, không phải yêu cầu tạo mỗi mục thành một abstraction. Giữ một web service, một DB và một adapter thật cho bản đầu.

## Cách chốt

Quen Python hơn → FastAPI. Quen JS/TS hơn → NestJS. Nếu ngang nhau, FastAPI là đề xuất cho prototype nhỏ sau khi giải quyết runtime. Nếu đang dùng stack backend khác thành thạo, ghi rõ để cân nhắc tiết kiệm thời gian chuyển ngôn ngữ.
