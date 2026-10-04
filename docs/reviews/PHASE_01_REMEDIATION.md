# Phase 01 Remediation — cập nhật sau review C2C

**Ngày:** 04/10/2026  
**Nguồn:** [`PHASE_01_SYSTEM_REVIEW.md`](PHASE_01_SYSTEM_REVIEW.md) và audit dữ liệu mới trong repository.

Đây là trạng thái khắc phục sau review, không viết lại phát hiện lịch sử trong báo cáo ban đầu. Các tuyên bố trước ngày 04/10 về sample tổng hợp và coverage nhiều năm đã được thay bằng audit và GO/NO-GO hiện tại. Final Plan được giữ nguyên làm tài liệu chuẩn đã có quality gate; tài liệu này cùng [`go_no_go_report.md`](../planning/go_no_go_report.md) ghi trạng thái triển khai mới nhất. Các trạng thái `CODE PATCHED — PENDING RUNTIME VALIDATION` nghĩa là mã/tài liệu đã được cập nhật nhưng chưa xác nhận bằng chạy Spark/ETL hoặc test tương ứng.

| Finding | Trạng thái | Khắc phục / giới hạn còn lại |
|---|---|---|
| F01 — Synthetic historical sample | **ARTIFACT REGENERATED — SOURCE/CHECKSUM VERIFIED** | Sample 300 dòng lấy phân tầng trực tiếp từ archive năm 2023. Fixture cũ chuyển vào `data/fixtures/synthetic/`, gắn `source` và `data_origin` synthetic; không dùng trong profiling hay feasibility. Collector code chưa được xác nhận lại bằng test/runtime riêng. |
| F02 — Chuỗi thời gian và kết luận forecast | **PARTIAL — DATA LIMITATION REMAINS** | Có checksum, tháng và nghề × tháng trong manifest. Kết luận giữ GO prototype, conditional GO descriptive, NO-GO forecast. Không có dữ liệu historical 2024–2025 hoặc chuỗi nhiều năm được bổ sung bởi code. |
| F03 — Coverage bị gọi nhầm accuracy | **SCRIPT UPDATED — OUTPUT NOT EXECUTED IN THIS PASS** | Diagnostic logic được thay bằng coverage-only script tách archive tags và fresh JD; kết quả cũ bị đánh dấu deprecated. Chưa chạy script diagnostic mới trong pass này; không claim precision/recall/accuracy khi chưa có independent labels. |
| F04 — Title/skill taxonomy | **CODE PATCHED — PENDING RUNTIME VALIDATION** | Matching title/skill dùng chung helper, ranh giới token hỗ trợ C++/C#, alias nghề chuyên biệt được ưu tiên, taxonomy v0.1 thêm React/Next.js/HTML-CSS/Pandas/NumPy/Prompt Engineering và bỏ alias ngắn mơ hồ. Chưa có nhãn độc lập để ước lượng precision/recall. |
| F05 — Timestamp giả và timezone | **CODE PATCHED — PENDING RUNTIME VALIDATION** | HTTPS xác thực mặc định; timestamp thiếu không thay bằng giờ thu thập; dòng posted_at thiếu/sai được quarantine. Schema cho phép null timestamp. Spark ETL chưa chạy để xác nhận hành vi runtime. |
| F06 — Schema/tài liệu lệch nhau | **CODE PATCHED — PENDING RUNTIME VALIDATION** | Schema code và tài liệu đồng bộ 18 trường; description nullable; mapping archive dùng header thật và nêu rõ không có JD/native ID. Scope/RQ/README/summary phản ánh observed coverage. |
| F07 — Dedup và provenance | **CODE PATCHED — PENDING RUNTIME VALIDATION** | ID và checksum ổn định theo source record/content, survivor chọn xác định, provenance gắn mỗi dòng Silver. Fuzzy cross-platform matching và repost detection vẫn planned; chưa có benchmark đánh giá. |
| F08 — Fresh collector | **CODE PATCHED — PENDING RUNTIME VALIDATION** | TLS chuẩn, không lưu batch rỗng khi mọi nguồn lỗi, snapshot trước đó được giữ; country không xác định để null. Pagination/retry/đánh giá điều khoản và chạy định kỳ vẫn cần làm trước production. |
| F09 — Tái lập và tài liệu trạng thái | **ARTIFACT REGENERATED — CODE PATH PENDING RUNTIME VALIDATION** | Manifest raw có checksum/counts; profiling và GO/NO-GO dùng dữ liệu thật; README và summary cập nhật. Số liệu Bronze/Silver của các lần chạy trước được ghi là chưa xác nhận lại. |
| F10 — An toàn khi ghi output ETL | **CODE PATCHED — PENDING RUNTIME VALIDATION** | Silver, provenance và quarantine được ghi vào staging trước; ETL mặc định từ chối nếu output chuẩn đã tồn tại. Chỉ `--replace-existing` mới thay output, đồng thời giữ backup theo run ID. Chưa chạy Spark để xác nhận hành vi runtime. |
| F11 — Assertion-based regression tests | **OPEN — TEST SUITE NOT ADDED OR RUN** | `tests/test_phase01_feasibility.py` là diagnostic coverage, không phải regression test suite. Các assertion contracts cho schema, ID, taxonomy, fixture provenance và output-path safety vẫn cần được bổ sung và chạy trong một lượt nghiệm thu test riêng. |

## Kết quả kiểm kê dùng cho quyết định

- Archive `data/raw/data_jobs.csv`: 785.741 dòng, 12 tháng năm 2023; không có `job_description` hoặc native job ID.
- Historical sample: 300 dòng thật, 25 dòng mỗi tháng; không đại diện cho các năm khác.
- Fresh file là snapshot đã lưu, không chứng minh collector chạy liên tục hoặc API còn sẵn sàng tại hiện tại.
- Dự báo vẫn **NO-GO**; license/điều khoản archive cần được xác minh trước khi phát hành dữ liệu hoặc kết quả.

## Kiểm tra trong lần khắc phục

Đã tạo lại sample, audit manifest và data profile từ nguồn repository. Đã rà soát mã/schema/tài liệu và diff; C2C xác nhận cơ chế staging/promotion/rollback chỉ qua static review. Spark ETL chưa chạy trong lần khắc phục này, nên hành vi ghi staging và promotion vẫn pending runtime validation. Assertion-based regression suite chưa được bổ sung hoặc chạy; diagnostic script không thay thế suite đó. Các đầu ra Silver/Provenance cũ vì vậy chưa được xác nhận theo mã mới.
