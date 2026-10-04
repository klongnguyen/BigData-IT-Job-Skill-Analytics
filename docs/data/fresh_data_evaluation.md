# Fresh Data Evaluation — snapshot evidence

Các nguồn Arbeitnow và Remotive được khảo sát qua endpoint công khai, nhưng các kết quả HTTP/sample được ghi trước đây chỉ là bằng chứng tại thời điểm chạy. Tài liệu này không khẳng định API hiện còn sẵn sàng hoặc tạo được dòng dữ liệu liên tục.

## Trường nguồn quan sát được

| Nguồn | ID dòng | Thời gian đăng | JD/tags | Ghi chú |
|---|---|---|---|---|
| Arbeitnow | `slug` | `created_at` | `description`, `tags` | API trả trang dữ liệu; collector hiện tại chưa duyệt toàn bộ pagination |
| Remotive | `id` | `publication_date` | `description`, `tags` | Collector giới hạn category software-dev |

Pipeline phải giữ ID nguồn, URL nếu có, checksum raw, thời điểm thu thập và `skills_origin`. Timestamp thiếu/sai giữ null và được quarantine; xác thực TLS tiêu chuẩn được bật.

## Giới hạn và quyết định

- `data/sample/fresh/fresh_sample.json` là snapshot đã lưu, không phải live check. Nội dung có thể chứa trường do collector cũ suy diễn; không dùng các giá trị city/country đó như sự thật nguồn.
- Snapshot fresh khác nguồn và không liên tục với archive lịch sử năm 2023; không nối hai tập để tuyên bố concept drift hoặc kiểm định forecasting.
- `tags` và rule-based matching đo coverage, không phải độ chính xác. Cần nhãn độc lập để báo precision/recall.
- API pagination, độ phủ nghề, điều khoản, tốc độ thay đổi schema và quota cần được tái kiểm tra trước khi đưa vào vận hành.

**Trạng thái Phase 01:** fresh API phù hợp làm nguồn prototype/snapshot có điều kiện. Chưa đủ bằng chứng cho forecast hoặc khẳng định coverage ổn định. Quyết định chi tiết ở [GO/NO-GO report](../planning/go_no_go_report.md).
