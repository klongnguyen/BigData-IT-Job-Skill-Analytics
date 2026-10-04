# Quy tắc định danh và khử trùng lặp

Tài liệu phân biệt hành vi đã có trong mã với các quy tắc fuzzy/repost còn là thiết kế. Pipeline hiện khử trùng lặp xác định theo **định danh nguồn**; không tự gộp hai ID nguồn khác nhau dù `job_hash` giống nhau.

## Đã triển khai trong Spark ETL

- Sinh `job_id` ổn định bằng SHA-256 từ nguồn và `source_record_id`; với archive không có ID gốc, dùng checksum dòng raw làm ID nguồn ổn định.
- Sinh `job_hash` từ company, title, location và ngày đăng như tín hiệu tìm cặp cần audit. `job_hash` không còn là khóa loại bản ghi.
- Khi nhiều snapshot trùng `job_id`, chọn survivor theo `collected_at` mới nhất; tie-breaker lần lượt dùng `raw_checksum`, `job_hash`, `source_url` và `ingestion_id` để provenance vẫn xác định khi hai snapshot trùng giây và nội dung. Hai source ID khác nhau được giữ riêng.
- Ghi provenance cho các dòng Silver còn lại. Bản ghi thiếu hoặc có `posted_at` sai định dạng, title rỗng, hoặc source record ID rỗng được quarantine, không gán giá trị giả để qua pipeline.
- ETL chỉ đọc các Bronze run được chỉ định rõ; kiểm tra checksum và số record thực tế từng file theo manifest, rồi đối chiếu số dòng Spark đọc với tổng số dòng các manifest trước khi ghi output. Manifest ETL lưu `input_rows`, `quarantine_rows`, `identity_duplicates_removed`, `silver_rows`, `provenance_rows` và số `job_id` duy nhất.

## Chưa triển khai

### Tin gần trùng đa nền tảng

Chưa có fuzzy matching theo công ty, title, khoảng cách thời gian hay độ tương tự mô tả; chưa hợp nhất nguồn hoặc chấm điểm độ tin cậy. Đây là hạng mục cần dữ liệu JD và đánh giá thủ công trước khi dùng cho analytics.

### Tin đăng lại

Chưa có phân loại repost theo cửa sổ 14/30 ngày và tương tự JD. Chưa loại repost khỏi chỉ số nhu cầu.

## Cổng trước khi bật fuzzy/repost

1. Thu thập JD/source URL và giữ lineage đầy đủ.
2. Tạo tập cặp tin được gán nhãn độc lập (duplicate/repost/non-duplicate).
3. Chốt ngưỡng trên validation set, báo precision/recall và phân tích sai số.
4. Chạy so sánh chỉ số có/không fuzzy hoặc repost filter; lưu audit trail cho quyết định hợp nhất.

Không dùng `dropDuplicates()` không có thứ tự xác định làm tiêu chí chọn survivor. Hành vi và ngưỡng phải được kiểm chứng lại khi mở rộng deduplication.
