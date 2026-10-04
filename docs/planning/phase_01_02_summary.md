# Tổng kết Phase 01 và ghi chú Phase 02

## Phase 01 — Feasibility & Project Definition

Phase 01 được mở lại để sửa kết luận khả thi dựa trên bằng chứng trong repository. Review chi tiết ở [`PHASE_01_SYSTEM_REVIEW.md`](../reviews/PHASE_01_SYSTEM_REVIEW.md); số liệu kiểm kê và checksum ở [`phase01_data_audit.json`](../data/phase01_data_audit.json); quyết định mới ở [`go_no_go_report.md`](go_no_go_report.md).

| Hạng mục | Bằng chứng hiện có | Trạng thái |
|---|---|---|
| Historical archive | 785.741 dòng, 12 tháng năm 2023; có title/date/source tags; không có JD hoặc native job ID | Đủ cho prototype và descriptive analytics giới hạn |
| Fresh data | Snapshot đã lưu từ API công khai; không chứng minh API đang hoạt động liên tục | Dùng làm ví dụ snapshot, không ghép thành chuỗi lịch sử |
| Occupation/skill taxonomy | Bộ từ điển V0 và deterministic matcher; chưa có independent labeled set | Coverage có thể thống kê, accuracy chưa biết |
| Unified schema | 18 trường; các trường không có nguồn giữ null; provenance lưu riêng | Đặc tả đã đồng bộ, cần chạy ETL ở môi trường đích trước nghiệm thu vận hành |
| Time series / forecast | Chỉ có archive 2023 và snapshot rời rạc | **NO-GO** cho forecast/predictive claims |

**Quyết định hiện tại:** GO cho prototype; conditional GO cho mô tả dữ liệu theo đúng nguồn và giới hạn; NO-GO cho dự báo. Quality gate Phase 01 còn mở cho đến khi nguồn, điều khoản sử dụng, nhãn taxonomy và chuỗi thời gian đáp ứng các điều kiện trong GO/NO-GO report.

Các câu hỏi nghiên cứu RQ1–RQ6 là mục tiêu cần trả lời, không phải kết quả đã đo được. Phạm vi mong muốn 2022–2026 không đồng nghĩa với coverage quan sát được.

## Phase 02 — Ingestion & Storage

Repository có mã ingestion và Spark ETL, nhưng kết quả cũ trong tài liệu này không còn được xem là số liệu nghiệm thu: lịch sử chạy không có artifact/checksum đủ để tái lập trong lần review. Không khẳng định số dòng Bronze/Silver, mức dedup, hoặc mức sẵn sàng 100% nếu chưa chạy pipeline trên input cố định và lưu manifest.

Các lần chạy Spark sẽ cần xác nhận riêng trong môi trường cài đủ Java/Hadoop/Spark. Lần cập nhật Phase 01 này không chạy Spark ETL hay ghi đè Silver/Provenance/Quarantine.
