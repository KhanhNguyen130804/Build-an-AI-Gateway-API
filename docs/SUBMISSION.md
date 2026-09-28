# Hồ sơ nộp bài và demo

**Draft; cập nhật sau Phase04 local (29/09/2026).** Có evidence cho authentication và một lượt chat đầu tiên qua gateway với request/attempt PostgreSQL; continuation, analysis, usage, reliability phases còn lại và cloud release chưa hoàn thành. Các placeholder và claims phải sửa theo evidence mới trước khi nộp. Nội dung challenge/screenshot là yêu cầu bài thi được người dùng cung cấp; việc chuẩn bị hồ sơ không tự động bao gồm gửi form hoặc chia sẻ ra ngoài.

## Danh sách deliverable

- [ ] Source repository truy cập được, có lockfile và migration, không secret.
- [ ] Deployed API và Swagger/OpenAPI hoạt động qua HTTPS.
- [ ] README hoàn chỉnh: problem, solution, architecture/workflow, API, DB, AI usage, completed work, metrics, reliability, limitations.
- [ ] Architecture diagram và database ERD; Mermaid hiển thị trong repo, hoặc ảnh xuất nếu nơi nộp không hỗ trợ.
- [ ] Schema thực/migration và SQL đối chiếu usage khớp nhau.
- [ ] Postman collection hoặc API examples đã chạy với API deploy; export không token/password/provider key.
- [ ] Video ≤5 phút, link có quyền xem và không tự hết hạn trước review.
- [ ] AI_WORKLOG có công cụ, cách hỗ trợ, lỗi AI đã quan sát/sửa thật và kế hoạch thêm7 ngày.
- [ ] Ít nhất1 prompt thực đã dùng; process description ≥30 ký tự.
- [ ] Kiểm tra ẩn danh theo screenshot: bỏ tên và logo cá nhân khỏi file/video.
- [ ] Kiểm tra GitHub profile/repo owner có thể lộ danh tính; chưa biết cổng thi cho phép mức nào, tránh tự tuyên bố anonymous tuyệt đối.
- [ ] Để showcase/prompt-log sharing theo lựa chọn thực của người dùng; không tự quyết định checkbox.

## README cuối cùng cần trả lời

1. Vấn đề: nhiều client gọi provider trực tiếp dẫn đến auth/context/usage/reliability bị lặp.
2. Giải pháp: gateway chung, với chat và ticket analysis làm ví dụ cụ thể.
3. Chạy local: Python version, install lockfile, env, DB migration, seed, start và test; commands đã chạy từ checkout sạch.
4. Reviewer thử: docs URL, cách login/authorize, request examples, quota và synthetic-data warning.
5. Kiến trúc: request flow, một web service/DB, provider adapter, diagram.
6. Database: sáu bảng, owner filtering/constraints, request/attempt distinction, successful message commit.
7. AI: provider/model thực đã dùng, structured schema/prompt version, limitations và refusal.
8. Reliability: retryable/nonretryable, SDK retries disabled, deadline, rate limit và persistence failures.
9. Metrics: công thức đúng của bản cuối, cohort/timezone, unknown tokens và fixture đối chiếu.
10. Test/evidence: lệnh thực, kết quả thực, live smoke và phần chưa được kiểm thử.
11. AI use: dẫn worklog và prompt thực; vai trò AI vs kiểm chứng của developer.
12. Completed/limitations: chỉ tick phần đã chạy; bonus đã chứng minh; remaining work.

## Kịch bản video 4 phút 40 giây

Mục tiêu dưới5 phút có khoảng đệm20 giây. Dùng ticket giả, ẩn env/browser profile/avatar/key.

| Thời gian | Nội dung hiển thị | Lời dẫn chính |
|---|---|---|
| 00:00–00:25 | Sơ đồ architecture | Hai ứng dụng dùng chung gateway; auth/usage/reliability tập trung |
| 00:25–00:55 | API deploy/Swagger, login và authorize | Đây là API online; provider key ở server; protected calls cần bearer |
| 00:55–01:40 | Hai lượt chat trong một conversation | Lượt2 dùng context từ database; GET history chứng minh lưu trữ |
| 01:40–02:20 | Analyze ticket payment/account | JSON schema v1, enums, human-review flag; không chỉ parse JSON tự do |
| 02:20–03:00 | GET usage và ledger/log đã redact | Request khác attempt; explain known tokens/latency/error denominator |
| 03:00–03:40 | Evidence test retry/timeout/rate-limit/ownership | Gắn nhãn “deterministic test with fake upstream”; không gọi mock là live integration |
| 03:40–04:15 | Worklog, một sai/sửa AI thực và verification | Có lỗi cộng giờ trong draft kế hoạch đã sửa; ưu tiên thêm ví dụ code nếu quan sát được khi triển khai |
| 04:15–04:40 | README/setup/limitations/links | Cách thử lại; phần hoàn thành thật; hạn chế và cải tiến tiếp |

Nếu chưa có lỗi AI thực để trình bày, nói rõ không có lỗi đã quan sát ở phần đó và trình bày kiểm tra thực; không tạo câu chuyện sai. Không chạy nhiều paid requests để diễn rate limiting; dùng test có nhãn.

## Nội dung form chuẩn bị

### Product link/file

Ưu tiên trang README/landing đơn giản có liên kết API/docs, source và video: `[TODO_REVIEWER_ENTRY_URL]`. Có thể dùng repo README nếu quyền truy cập và ẩn danh phù hợp. Không cần xây website riêng chỉ để nộp backend.

### Prompt used — có thể dùng ngay cho phiên chuẩn bị

Tool: `Codex`.

Ghi prompt thật của phiên này; có thể trích phần mở đầu người dùng cùng yêu cầu challenge đã gửi. Bản mô tả ngắn dưới đây là **paraphrase**, không phải nguyên văn:

```text
Chuẩn bị kế hoạch chi tiết và các tài liệu cần thiết trước khi triển khai AI Gateway
cho challenge backend. Còn khoảng3 ngày; cần auth, database, LLM thật,
structured output, lưu hội thoại, retry, timeout, logging, rate limit và usage.
Chuẩn bị kiến trúc, schema, hợp đồng API, ca kiểm thử, deployment và hồ sơ nộp.
Stack chốt sau trao đổi: Python + FastAPI.
```

Ghi prompt thực đã dùng trong từng phiên vào [AI_WORKLOG.md](../AI_WORKLOG.md). Các prompt mẫu P01–P05 vẫn là tài liệu chuẩn bị cho tới khi được thực thi nguyên văn.

### Process description — bản trung thực cho giai đoạn hiện tại

```text
Tôi cung cấp đề bài cho Codex, chọn Python + FastAPI, rồi triển khai từng phần có kiểm chứng.
Đến Phase04, gateway có schema PostgreSQL/migration/seed, Argon2id/JWT bearer và endpoint chat
một lượt gọi OpenAI qua gateway, có request/attempt ledger. Tôi kiểm tra 50 ca local, Ruff và
một live smoke readiness/login/chat với PostgreSQL; output/metadata đã được xác nhận nhưng chưa
triển khai lên cloud. Continuation, phân tích ticket, usage, retry/rate limit và release cuối còn phải làm.
```

Trước nộp, cập nhật đoạn này bằng kết quả implementation/test/deploy mới nhất. Mẫu đầy đủ dưới đây chỉ dùng khi mọi phần ghi trong đó đã được thực hiện:

```text
Tôi dùng Codex để phân tích yêu cầu, thiết kế và triển khai từng luồng nhỏ của gateway.
Tôi kiểm tra kết quả AI bằng test auth/ownership, structured output, retry, timeout,
rate limit và đối chiếu usage với dữ liệu database. Sau khi sửa các lỗi quan sát được,
tôi deploy API, thử lại bằng Postman và ghi prompt, bằng chứng, hạn chế vào AI_WORKLOG.
```

Cả hai đoạn dài hơn30 ký tự; độ dài tối thiểu không thay thế độ chính xác của nội dung.

### Estimated hours saved

`[TODO_ESTIMATE_IF_DEFENSIBLE]`. Đo actual effort và nêu baseline/assumption trong worklog. Không điền4 giờ chỉ vì placeholder của form gợi ý4. Nếu không có cơ sở, để trống nếu trường không bắt buộc.

## Kiểm tra trước nộp — mốc21:00 ngày01/10

1. Mở entry/API/repo/video bằng phiên không dùng quyền owner; kiểm tra quyền xem và account demo.
2. Chạy smoke ngắn trên deploy; không để token trong Postman export.
3. Soát TODO/placeholder, tên/logo, secret và claims chưa test trong hồ sơ/video.
4. Kiểm tra thời lượng video thực và mô tả rõ test dùng fake upstream.
5. Điền prompt thực và process thực; lựa chọn hai checkbox sharing do người dùng quyết định.
6. Nộp khi người dùng thực hiện/yêu cầu nộp; ghi receipt/trạng thái thành công thật, không suy ra từ click.
7. Lưu bản nộp và giữ dịch vụ/link đến hết review; hạn window168h không phải giấy phép để ngừng API ngay sau deadline.
